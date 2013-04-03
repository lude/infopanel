from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

import requests
import base64
import sys
import os
import json
import datetime
import oauth2 as oauth
import time


def oauth_req(request, url, key, secret, http_method="GET", post_body='',
              http_headers=None):
    consumer = oauth.Consumer(
        key=request.registry.settings.get('twitter.consumer_key'),
        secret=request.registry.settings.get('twitter.consumer_secret')
    )
    token = oauth.Token(key=key, secret=secret)
    client = oauth.Client(consumer, token)

    resp, content = client.request(
        url,
        method=http_method,
        body=post_body,
        headers=http_headers,
    )
    return content


def degrees_to_direction(deg):
    ret = "unknown"
    if deg in range(0, 22):
        ret = "North"
    if deg in range(23, 67):
        ret = "Northeast"
    if deg in range(68, 112):
        ret = "East"
    if deg in range(113, 157):
        ret = "Southeast"
    if deg in range(158, 202):
        ret = "South"
    if deg in range(203, 247):
        ret = "Southwest"
    if deg in range(248, 292):
        ret = "West"
    if deg in range(293, 337):
        ret = "Northwest"
    if deg in range(338, 360):
        ret = "North"

    return ret


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + "s"
        if second_diff < 3600:
            return str(second_diff / 60) + "m"
        if second_diff < 86400:
            return str(second_diff / 3600) + "h"
    if day_diff < 7:
        return str(day_diff) + "d"
    if day_diff < 31:
        return str(day_diff / 7) + "w"
    return str(day_diff / 365) + "y"


@view_config(route_name='index')
def index(self):
    return render_to_response('templates/index.pt', {'foo': 1}, self)


@view_config(route_name='forecastio')
def forecastio(self):
    # http://www.alessioatzeni.com/meteocons/ -> forecast.io conversion table
    webfont = {
        'clear-day': 'B',
        'clear-night': 'C',
        'rain': 'R',
        'snow': 'W',
        'sleet': 'X',
        'wind': 'F',
        'fog': 'M',
        'cloudy': 'N',
        'partly-cloudy-day': 'H',
        'partly-cloudy-night': 'I'
    }

    # grab the forecast.io json
    r = requests.get(
        'https://api.forecast.io/forecast/%s/%s,%s' % (
            self.registry.settings.get('forecastio.apikey'),
            self.registry.settings.get('forecastio.latitude'),
            self.registry.settings.get('forecastio.longitude')
        )
    )

    #pythonize it
    weather = json.loads(r.content)

    currently = {}
    currently['icon'] = webfont.get(weather['currently']['icon'], ')')
    currently['summary'] = weather['currently']['summary']
    currently['temperature'] = int(weather['currently']['temperature'])

    minutely = {}
    minutely['icon'] = webfont.get(weather['minutely']['icon'], ')')
    minutely['summary'] = weather['minutely']['summary']

    hourly = {}
    hourly['icon'] = webfont.get(weather['hourly']['icon'], ')')
    hourly['summary'] = weather['hourly']['summary']

    daily = {}
    daily['icon'] = webfont.get(weather['daily']['icon'], ')')
    daily['summary'] = weather['daily']['summary']

    weekly = []
    daycount = 0
    for forecast in weather['daily']['data']:
        if daycount is 5:
            break
        d = {}
        d['day'] = datetime.datetime.fromtimestamp(forecast['time']).strftime('%A')
        d['high'] = int(forecast['temperatureMax'])
        d['low'] = int(forecast['temperatureMin'])
        d['windspeed'] = int(forecast['windSpeed'])
        try:
            d['winddir'] = degrees_to_direction(forecast['windBearing'])
        except KeyError:
            d['winddir'] = ''
        d['summary'] = forecast['summary']
        d['icon'] = webfont.get(forecast['icon'])
        weekly.append(d)
        daycount += 1

    return render_to_response(
        'templates/forecastio.pt', {
            'currently': currently,
            'minutely': minutely,
            'hourly': hourly,
            'daily': daily,
            'weekly': weekly,
        }, self)


@view_config(route_name='redditnews')
def redditnews(self):
    r = requests.get(
        "http://www.reddit.com/r/%s.json" % (
            self.registry.settings.get('reddit.subreddits')
        )
    )

    j = json.loads(r.content)['data']['children']

    news = []
    articlecount = 0
    for a in j:
        d = {}
        d['url'] = a['data']['url']
        d['title'] = a['data']['title']
        d['subreddit'] = a['data']['subreddit']
        d['score'] = a['data']['score']
        d['author'] = a['data']['author']
        d['created'] = pretty_date(int(a['data']['created']))
        news.append(d)

    return render_to_response(
        'templates/reddit.pt', {
            'news': news,
        }, self)


@view_config(route_name='twitter')
def twitter(self):
    home_timeline = oauth_req(
        self,
        'https://api.twitter.com/1.1/lists/statuses.json?list_id=86741833',
        self.registry.settings.get('twitter.access_token'),
        self.registry.settings.get('twitter.access_token_secret')
    )

    t = json.loads(home_timeline)

    tweets = []
    tcount = 0
    for tw in t:
        d = {}
        d['text'] = tw['text']
        d['user'] = tw['user']['screen_name']
        d['userpic'] = tw['user']['profile_image_url']
        tweets.append(d)
        tcount += 1

    return render_to_response(
        'templates/twitter.pt', {
            'tweets': tweets,
        }, self
    )
