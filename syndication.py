from flask import Flask, jsonify, request, make_response,g,Response
import sqlite3
import re
from passlib.hash import sha256_crypt
from flask_api import status
from flask_httpauth import HTTPBasicAuth
import datetime
from http import HTTPStatus
import datetime
import requests

from rfeed import *

app = Flask(__name__)
auth = HTTPBasicAuth()

@app.route("/summary", methods=['GET'])
def summary():
    article_summary = requests.get('http://localhost/metaarticle/10')
    articles = []

    if article_summary is not None:
        article_summary = article_summary.json()

    for article in article_summary:
        articles.append(Item(
            title = article['title'],
            author = article['email'],
            link = article['url'],
            date = article['create_time']
        ))

    feed = Feed(
        title = "Summary Feed",
        link = "www.summaryfeed.com",
        description = "This is summary feed of 10 most recent articles",
        language = "en-US",
        items = articles
    )

    return feed.rss()

@app.route("/comments", methods=['GET'])
def commentsummary():
    article_summary = requests.get('http://localhost/recentarticle/10')
    articles = []

    if article_summary is not None:
        article_summary = article_summary.json()

    for article in article_summary:
        comment_array = []
        comments = requests.get('http://localhost/articles/comments/recentcomments/'+str(article['article_id'])+'/10')
        if comments is not None and comments.text != '':
            comments = comments.json()

        for comment in comments:
            comment_array.append(comment['comment_content'])

        articles.append(Item(
            title = article['title'],
            categories = comment_array
        ))

    feed = Feed(
        title = "Comment Feed",
        link = "http://www.commentfeed.com",
        description = "This is comment feed",
        language = "en-US",
        items = articles
    )

    return feed.rss()

@app.route('/feed', methods=['GET'])
def feed():
    r = requests.get('http://localhost/metaarticle/100')

    items = []

    if r is not None:
        r = r.json()


    for article in r:

        comment_tags = requests.get("http://localhost/tag/gettag/"+ str(article['article_id']))


        if comment_tags is not None and comment_tags != '':
            comment_tags = comment_tags.json()

        tags = []
        for tag in comment_tags:
            if 'tag_name' in tag:
                tags.append(tag['tag_name'])

        comment_count = requests.get("http://localhost/articles/comments/countcomment/"+ str(article['article_id']))

        if comment_count == '':
            comment_count = "Number of comments for given article: 0"

        comment_count = comment_count.json()

        items.append(Item(
            title = article['title'],
            description = comment_count,
            categories = tags
        ))


    feed = Feed(
        title = "Full Feed",
        link = "http://www.fullfeed.com/rss",
        description = "This is full feed",
        language = "en-US",
        lastBuildDate = datetime.datetime.now(),
        items = items)

    return feed.rss()

app.run()
