![Broken Down Slide](https://github.com/derferman/hn-comments/raw/master/slide.jpg)

## Question

Have the comments on Hacker News gotten demonstrably worse over time?

## Background Research

We'll need to download all the comments from frontpage stories over the entire history of Hacker News.

    pip install -r requirements.txt
    fab download

## Hypothesis

Earlier stories have fewer comments. These comments are of higher quality.

## Analysis

    fab transform analyze

## Conclusion

After graphing comment score, comment length, comment totals, and story points over time, the only conclusion I can draw to is that the number of comments per story have increased over time.

![# of Comments per Story versus Time](https://github.com/derferman/hn-comments/raw/master/comments.png)

## Experiment Status

**FAILED:** After getting all that comment data, I didn't find anything cool. Sigh


