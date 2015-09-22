from flask import Flask, request
from lib.helpers import degrees_to_direction, pretty_date, jsonify
from time import strftime
from requests_oauthlib import OAuth1Session
from datetime import datetime

import requests

app = Flask(__name__)
app.config.from_envvar('INFOPANEL_SETTINGS_FILE')


@app.route('/clock', methods=['GET'])
def clock():
    clock = strftime("%a %m/%d %I:%M %p")
    return jsonify({'clock': clock})


@app.route('/greeting', methods=['GET'])
def greeting():
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
    return jsonify({'greeting': retval})


@app.route('/twitter', methods=['GET'])
def twitter():
    twitter = OAuth1Session(app.config.client_key
                            client_secret=app.config.client_secret,
                            resource_owner_key=app.config.ro_key,
                            resource_owner_secret=app.config.ro_secret)

    url = 'https://api.twitter.com/1.1/lists/statuses.json?list_id=86741833&count=5'
    r = twitter.get(url)
    t = r.json()

    tweets = []
    tcount = 0
    for tw in t:
        d = {}
        d['id'] = tw['id']
        d['text'] = tw['text']
        d['created_at'] = tw['created_at']
        d['name'] = tw['user']['name']
        d['handle'] = tw['user']['screen_name']
        d['userpic'] = tw['user']['profile_image_url']
        tweets.append(d)
        tcount += 1

    return jsonify(tweets)


@app.route('/forecastio', methods=['GET'])
def forecastio():
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
    apikey = '3df3692a7ae010dc994ead5bac3655f2'
    latlong = '40.73853,-74.03145'
    r = requests.get(
        'https://api.forecast.io/forecast/%s/%s' % (apikey, latlong)
    )

    #pythonize it
    weather = r.json()

    currently = {}
    currently['icon'] = webfont.get(weather['currently']['icon'], ')')
    currently['summary'] = weather['currently']['summary']
    currently['humidity'] = int(weather['currently']['humidity'] * 100)
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
        d['day'] = datetime.fromtimestamp(forecast['time']).strftime('%A')
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

    return jsonify({
        'currently': currently,
        'minutely': minutely,
        'hourly': hourly,
        'daily': daily,
        'weekly': weekly,
    })


@app.route('/redditnews', methods=['GET'])
def redditnews():
    headers = {
        'User-Agent': 'infobot by /u/davidj911'
    }

    r = requests.get(
        "http://www.reddit.com/r/worldnews+news.json?limit=5",
        headers=headers
    )

    j = r.json()['data']['children']

    news = []
    i = 0
    for a in j:
        d = {}
        d['id'] = a['data']['name']
        d['url'] = a['data']['url']
        d['title'] = a['data']['title']
        d['subreddit'] = a['data']['subreddit']
        d['score'] = a['data']['score']
        d['author'] = a['data']['author']
        d['created'] = a['data']['created_utc']
        d['displayOrder'] = i
        i += 1
        news.append(d)

    return jsonify(news)

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("6542"),
        debug=True
    )
