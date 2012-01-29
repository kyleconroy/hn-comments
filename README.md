![Broken Down Slide](https://github.com/derferman/hn-decline/raw/master/slide.jpg)

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

Was I right?

    fab graph






