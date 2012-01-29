from fabric.api import *
from lxml import html
import datetime
import urllib
import time
import datetime
import re
import os
import json

DOWNLOAD_DATE = datetime.datetime(2012, 1, 28)

def story_id(url):
    _, story = url.split("id=")
    return story


def save_story(url, directory):
    story_url = "http://news.ycombinator.com"
    story_url += url.split("http://news.ycombinator.com")[1]

    story = story_id(url)
    created = False
    filename = os.path.join(directory, "{}.html".format(story))

    if not os.path.exists(filename):
        created = True
        urllib.urlretrieve(story_url, filename)

    return filename, created


def parse_stories(frontpage_path):
    try:
        parsed = html.fromstring(open(frontpage_path).read())
    except:
        return []

    pattern = re.compile("http:\/\/web\.archive\.org\/web\/\d+\/"
                         "http:\/\/news\.ycombinator\.com\/(item|comments)\?id=(\d+)")
    urls = [] 
    for link in parsed.cssselect("td.subtext a"):
        href = link.attrib["href"]
        if pattern.match(href) and "id=363" not in href: 
            urls.append(href.replace("comments", "item"))
    return urls


def transform_frontpages():
    if not os.path.isdir("data"):
        os.makedirs("data")

    if os.path.exists("data/frontpages.json"):
        puts("Already created frontpages.json, stopping")
        return

    hn_dir = os.path.expanduser("~/clocktower/news.ycombinator.com")
    frontpages = []

    for frontpage in os.listdir(hn_dir):
        filename, ext = os.path.splitext(frontpage)

        ts = datetime.datetime.fromtimestamp(int(filename))
        readable = ts.strftime('%Y-%m-%d %H:%M:%S')
        puts("Transforming frontpage on {}".format(readable))

        urls = parse_stories(os.path.join(hn_dir, frontpage))
        stories = [story_id(url) for url in urls]

        if not stories:
            continue

        frontpages.append({
            "timestamp": int(filename),
            "stories": stories,
            })

    json.dump(frontpages, open("data/frontpages.json", "w"))


def parse_comments(parsed):
    return []


def parse_story(parsed):
    story = {
        "title": None,
        "dead": False,
        "points": 0,
        "submitter": None,
        "timestamp": None,
        "comments": parse_comments(parsed),
        }
    
    try:
        title = parsed.cssselect("td.title")[0].text_content()
        if title == "[deleted]" or title == "[dead]":
            story["dead"] = True
            return story
    except IndexError:
        pass

    try:
        link = parsed.cssselect("td.title a")[0]
        story["title"] = link.text_content()
        story["url"] = link.attrib["href"]
    except IndexError:
        pass

    try:
        span = parsed.cssselect("td.subtext span")[0]
        story["points"] = int(span.text_content().replace(" points", ""))
    except IndexError:
        pass

    try:
        td = parsed.cssselect("td.subtext")[0]
        match = re.search("(\d+) days ago", td.text_content())
        if match:
            days_ago = int(match.group(1)) 
            submitted = DOWNLOAD_DATE - datetime.timedelta(days=days_ago)
            story["timestamp"] = time.mktime(submitted.timetuple())
    except IndexError:
        pass

    try:
        link = parsed.cssselect("td.subtext a")[0]
        story["submitter"] = link.text_content()
    except IndexError:
        pass

    return story

def transform_stories():
    for story in os.listdir("comments/raw"):
        if story.startswith("."):
            continue  # Damn you .DS_Store

        story_id, ext = os.path.splitext(story)
        story_path = os.path.join("comments/raw", story)
        #puts("Parsing story {}".format(story))

        try:
            parsed = html.fromstring(open(story_path).read())
        except:
            continue  # Couldn't parse the html

        import pprint
        story = parse_story(parsed)
        pprint.pprint(story)

        

@task
def transform():
    transform_frontpages()
    transform_stories()


@task
def download():
    if not os.path.isdir("comments/raw"):
        os.makedirs("comments/raw")
    hn_dir = os.path.expanduser("~/clocktower/news.ycombinator.com")
    for frontpage in os.listdir(hn_dir):

        filename, ext = os.path.splitext(frontpage)
        ts = datetime.datetime.fromtimestamp(int(filename))
        readable = ts.strftime('%Y-%m-%d %H:%M:%S')
        puts("Parsing frontpage on {}".format(readable))

        stories = parse_stories(os.path.join(hn_dir, frontpage))
        for url in set(stories):
            filename, created = save_story(url, "comments/raw")
            if created:
                puts("Saved {} at {}".format(filename, time.time()))
                time.sleep(1)
            else:
                puts("Already saved {}".format(filename))

