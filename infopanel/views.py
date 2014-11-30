import requests
import json
import pygtfs

from pyramid.view import view_config
from requests_oauthlib import OAuth1Session
from datetime import datetime
from datetime import timedelta
from sqlalchemy import and_


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


@view_config(route_name='forecastio', renderer='json')
def forecastio(self):
    self.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With'
    self.response.headers['Access-Control-Allow-Origin'] = '*'
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

    return {
        'currently': currently,
        'minutely': minutely,
        'hourly': hourly,
        'daily': daily,
        'weekly': weekly,
    }


@view_config(route_name='redditnews', renderer='json')
def redditnews(self):
    self.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With'
    self.response.headers['Access-Control-Allow-Origin'] = '*'

    headers = {
        'User-Agent': 'infobot by /u/davidj911'
    }

    r = requests.get(
        "http://www.reddit.com/r/worldnews+news.json",
        headers=headers
    )

    j = json.loads(r.content)['data']['children']

    news = []
    for a in j:
        d = {}
        d['id'] = a['data']['name']
        d['url'] = a['data']['url']
        d['title'] = a['data']['title']
        d['subreddit'] = a['data']['subreddit']
        d['score'] = a['data']['score']
        d['author'] = a['data']['author']
        d['created'] = a['data']['created']
        news.append(d)

    return news


@view_config(route_name='twitter', renderer='json')
def twitter(self):
    self.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With'
    self.response.headers['Access-Control-Allow-Origin'] = '*'

    twitter = OAuth1Session('uJOBRUQCVQvVSkOcVF4Pg',
                            client_secret='U49Nciwx63kLV32KCoiGc3U13467Y38UsB5G45E1my4',
                            resource_owner_key='57659893-ucMjCx9xZ5IqNNIJuuewld8gd3PtuTwTSFJyVcFNg',
                            resource_owner_secret='dLt7KQfpsdLUjm7MyVFywT244t0LtUM5OROTWtmR9Q')

    url = 'https://api.twitter.com/1.1/lists/statuses.json?list_id=86741833'
    r = twitter.get(url)
    t = r.json()

    tweets = []
    tcount = 0
    for tw in t:
        d = {}
        d['id'] = tw['id']
        d['text'] = tw['text']
        d['created_at'] = tw['created_at']
        d['user'] = tw['user']['screen_name']
        d['userpic'] = tw['user']['profile_image_url']
        tweets.append(d)
        tcount += 1

    return tweets


@view_config(route_name='pathtrain', renderer='json')
def path_train(self):
    self.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With'
    self.response.headers['Access-Control-Allow-Origin'] = '*'

    sched = pygtfs.Schedule("path.db")

    nowtime = datetime.now().strftime('%H:%M:%S')
    nowdate = datetime.now().date()
    now = datetime.now()
    seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    periods = sched.service_periods  # (nowdate)
    dow = datetime.now().strftime("%a")

    if dow in ['Mon','Tue','Wed','Thu','Fri']:
        service_id = '744A1674'
    elif dow is 'Sat':
        service_id = '745A1674'
    else:
        service_id = '746A1674'

    q = sched.session.query(pygtfs.entity.StopTime).join(pygtfs.entity.Stop).join(pygtfs.entity.Trip).join(pygtfs.entity.Route).filter(
        pygtfs.entity.Trip.service_id == service_id
    ).filter(
        pygtfs.entity.Stop.stop_id == 26730
    ).filter(
        pygtfs.entity.Route.route_id.in_([859, 1024])
    ).filter(
        pygtfs.entity.Trip.direction_id == 1
    ).order_by(pygtfs.entity.StopTime.departure_time)

    i = 0
    departure_times = []
    for stop in q.all():
        if i == 2:
            break
        if stop.departure_time.val > seconds_since_midnight and stop.departure_time.val < seconds_since_midnight + 7200:
            d = timedelta(
                seconds=(stop.departure_time.val - seconds_since_midnight)
            )
            time = "%s (%d minutes)" % (
                (datetime.now() + d).strftime('%I:%M%p'),
                (int((stop.departure_time.val - seconds_since_midnight) / 60))
            )
            departure_times.append(time)
            i += 1

    """
    r = requests.get(
        'http://www.paalerts.com/recent_pathalerts.aspx'
    )
    try:
        alertsoup = BeautifulSoup(r.content)
        alert_time = alertsoup.find("label")
        alert = alertsoup.findAll("div", {"class": "formField"})[1]
        alert_text = "%s - %s" % (
            alert_time.string.strip(' \t\n\r'),
            alert.string.strip(' \t\n\r')
        )
    except IndexError:
    """
    alert_text = ""

    return {
        'times': departure_times,
        'alerts': alert_text
    }


@view_config(route_name='greeting', renderer='json')
def greeting(self):
    self.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With'
    self.response.headers['Access-Control-Allow-Origin'] = '*'

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
    return {'greeting': retval}


@view_config(route_name='clock', renderer='json')
def clock(self):
    self.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With'
    self.response.headers['Access-Control-Allow-Origin'] = '*'

    #TODO this seems like a backward way to do this
    clock = strftime("%a %m/%d %I:%M %p")

    return {'clock': clock}
