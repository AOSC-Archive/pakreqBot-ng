# utils.py

import trafaret as T

from json import dumps
from datetime import date, datetime

TRAFARET = T.Dict({
    T.Key('db'):
        T.Dict({
            'location': T.String(),
        }),
    T.Key('host'): T.IP,
    T.Key('port'): T.Int(),
})

def json_serial(obj): # From Stack Overflow: https://stackoverflow.com/a/22238613
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def dump_json(obj):
    return dumps(obj, default=json_serial)