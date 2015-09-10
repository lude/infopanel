from datetime import datetime
import json

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


def jsonify(data):
    return json.dumps(data)

