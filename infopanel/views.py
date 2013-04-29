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


def oauth_req(url, key, secret, http_method="GET", post_body='',
              http_headers=None):
    consumer = oauth.Consumer(
        key='uJOBRUQCVQvVSkOcVF4Pg',
        secret='U49Nciwx63kLV32KCoiGc3U13467Y38UsB5G45E1my4'
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
        'https://api.forecast.io/forecast/3df3692a7ae010dc994ead5bac3655f2/40.73853,-74.03145'
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
        "http://www.reddit.com/r/worldnews+news.json"
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
        'https://api.twitter.com/1.1/lists/statuses.json?list_id=86741833',
        '57659893-ucMjCx9xZ5IqNNIJuuewld8gd3PtuTwTSFJyVcFNg',
        'dLt7KQfpsdLUjm7MyVFywT244t0LtUM5OROTWtmR9Q',
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
        }, self)


@view_config(route_name='pathtrain')
def path_train(self):
    from gtfs import Schedule
    from gtfs.types import TransitTime
    from gtfs.entity import *
    from sqlalchemy import and_

    sched = Schedule("path.db")

    nowtime = datetime.datetime.now().strftime('%H:%M:%S')
    nowdate = datetime.datetime.now().date()
    now = datetime.datetime.now()
    seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    periods = sched.service_for_date(nowdate)

    q = sched.session.query(StopTime).join(Stop).join(Trip).join(Route).filter(
        Trip.service_id.in_(periods)
    ).filter(
        Stop.stop_name == "Hoboken"
    ).filter(
        Route.route_id.in_(['859', '1024'])
    ).filter(
        Trip.direction_id == 1
    ).order_by(StopTime.departure_time)

    print q
    print q.count()

    i = 0
    departure_times = []
    for stop in q.all():
        if i == 2:
            break
        if stop.departure_time.val > seconds_since_midnight and stop.departure_time.val < seconds_since_midnight + 7200:
            d = datetime.timedelta(seconds=(stop.departure_time.val - seconds_since_midnight))
            time = "%s (%d minutes)" % (
                (datetime.datetime.now() + d).strftime('%I:%M%p'),
                (int((stop.departure_time.val - seconds_since_midnight) / 60))
            )
            departure_times.append(time)
            i += 1
    return render_to_response(
        'templates/pathtrain.pt', {
            'times': departure_times,
        }, self)


@view_config(route_name='greeting')
def greeting(self):
    from time import strftime

    #TODO this seems like a backward way to do this
    hour = int(strftime("%H"))

    if 2 <= hour <= 11:
        retval = "Morning"
    if 12 <= hour <= 16:
        retval = "Afternoon"
    if 17 <= hour <= 21:
        retval = "Evening"
    if 22 <= hour <= 23:
        retval = "Night"
    if 0 <= hour <= 1:
        retval = "Night"
    return Response(retval)


@view_config(route_name='clock')
def clock(self):
    from time import strftime

    #TODO this seems like a backward way to do this
    clock = strftime("%a %m/%d %I:%M %p")

    return Response(clock)
