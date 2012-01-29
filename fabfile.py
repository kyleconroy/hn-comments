from fabric.api import *
from lxml import html
import datetime
import urllib
import time
import datetime
import re
import os
import json
import csv

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


def parse_comment(td):
    comment = {
        "id": None,
        "author": None,
        "url": None,
        "body": None,
        "score": 1,
        "timestamp": None,
    }

    try:
        match = re.search("(\d+) days ago", td.text_content())
        if match:
            days_ago = int(match.group(1)) 
            submitted = DOWNLOAD_DATE - datetime.timedelta(days=days_ago)
            comment["timestamp"] = time.mktime(submitted.timetuple())
    except IndexError:
        pass

    try:
        fragment = td.cssselect("span.comhead a")[1].attrib["href"]
        comment["id"] = int(fragment.split("id=")[1])
        comment["link"] = "http://news.ycombinator.com/" + fragment
    except IndexError:
        pass

    try:
        color = td.cssselect("span.comment font")[0].attrib["color"]
        worst = int("0xe6e6e6", 0)
        comment["score"] = 1 - int(color.replace("#", "0x"), 0) / float(worst)
    except IndexError:
        pass

    try:
        comment["author"] = td.cssselect("span.comhead a")[0].text_content()
    except IndexError:
        pass

    try:
        comment["body"] = td.cssselect("span.comment")[0].text_content()
    except IndexError:
        pass

    return comment


def parse_comments(parsed):
    return [parse_comment(td) for td in parsed.cssselect("td.default")]


def parse_story(parsed):
    story = {
        "title": None,
        "url": None,
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
    if not os.path.isdir("data/stories"):
        os.makedirs("data/stories")

    for story in os.listdir("comments/raw"):
        if story.startswith("."):
            continue  # Damn you .DS_Store

        story_id, ext = os.path.splitext(story)
        story_path = os.path.join("comments/raw", story)
        #puts("Parsing story {}".format(story))

        json_path = "data/stories/{}.json".format(story_id) 

        if os.path.exists(json_path):
            puts("Already created {}".format(json_path))
            continue

        try:
            parsed = html.fromstring(open(story_path).read())
        except:
            continue  # Couldn't parse the html

        story = parse_story(parsed)
        story["id"] = int(story_id)
        json.dump(story, open("data/stories/{}.json".format(story_id), "w"))
        puts("Created {}".format(json_path))


@task
def transform():
    transform_frontpages()
    transform_stories()

    
def analyze_comment_length():
    if not os.path.isdir("data/graphs"):
        os.makedirs("data/graphs")

    puts("Generating comment length data")

    writer = csv.writer(open("data/graphs/number_comments.csv", "w"))

    for story_file in os.listdir("data/stories"):
        if story_file.startswith("."):
            continue  # Damn you .DS_Store

        story = json.load(open(os.path.join("data/stories", story_file)))

        if story["timestamp"]:
            writer.writerow([story["timestamp"], len(story["comments"])])


def analyze_story_points():
    if not os.path.isdir("data/graphs"):
        os.makedirs("data/graphs")

    puts("Generating stories points data")

    writer = csv.writer(open("data/graphs/story_points.csv", "w"))

    for story_file in os.listdir("data/stories"):
        if story_file.startswith("."):
            continue  # Damn you .DS_Store

        story = json.load(open(os.path.join("data/stories", story_file)))
        writer.writerow([story["timestamp"], story["points"]])


def analyze_comment_score_versus_length():
    if not os.path.isdir("data/graphs"):
        os.makedirs("data/graphs")

    puts("Generating comment score versus length data")

    writer = csv.writer(open("data/graphs/comment_length_vs_score.csv", "w"))

    for story_file in os.listdir("data/stories"):
        if story_file.startswith("."):
            continue  # Damn you .DS_Store

        story = json.load(open(os.path.join("data/stories", story_file)))

        for comment in story["comments"]:
            if comment["body"]:
                writer.writerow([len(comment["body"]), comment["score"]])

def analyze_comment_case():
    scores = []
    lowercase = []

    for story_file in os.listdir("data/stories"):
        if story_file.startswith("."):
            continue  # Damn you .DS_Store

        story = json.load(open(os.path.join("data/stories", story_file)))

        for comment in story["comments"]:
            scores.append(comment["score"])
            if comment.get("body", None) and comment["body"] == comment["body"].lower():
                lowercase.append(comment["score"])

    all_avg = sum(scores) / float(len(scores))
    puts("Total number of all comments: {}".format(len(scores)))
    puts("Average score for all comments: {}".format(all_avg))

    lowercase_avg = sum(lowercase) / float(len(lowercase))
    puts("Total number of lowercase comments: {}".format(len(lowercase)))
    puts("Average score for lowercase comments: {}".format(lowercase_avg))


def analyze_worst_comments():
    scores = []

    for story_file in os.listdir("data/stories"):
        if story_file.startswith("."):
            continue  # Damn you .DS_Store

        story = json.load(open(os.path.join("data/stories", story_file)))

        for comment in story["comments"]:
            scores.append((comment["score"], comment)) 

    scores.sort()

    for score, body in scores[:10]:
        print score
        print comment
        print 


def analyze_comment_numbers():
    if not os.path.isdir("data/graphs"):
        os.makedirs("data/graphs")

    puts("Generating comment totals data")

    writer = csv.writer(open("data/graphs/comment_length.csv", "w"))

    for story_file in os.listdir("data/stories"):
        if story_file.startswith("."):
            continue  # Damn you .DS_Store

        story = json.load(open(os.path.join("data/stories", story_file)))

        for comment in story["comments"]:
            if comment["timestamp"] and comment["body"]:
                writer.writerow([comment["timestamp"], len(comment["body"])])

@task
def report():
    #analyze_comment_case()
    analyze_worst_comments()


@task
def analyze():
    analyze_comment_length()
    analyze_comment_numbers()
    analyze_story_points()
    analyze_comment_score_versus_length()

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

