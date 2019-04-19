# utils.py

"""
Utilities
"""

import trafaret as T

from json import dumps
from argon2 import PasswordHasher
from datetime import date, datetime

from pakreq.db import RequestType, RequestStatus
from aiosqlite3.sa.result import RowProxy

# Configuration checker
TRAFARET = T.Dict({
    T.Key('db'):
        T.Dict({
            'location': T.String(),
        }),
    T.Key('telegram'):
        T.Dict({
            'token': T.String(),
        }),
    T.Key('host'): T.IP,
    T.Key('port'): T.Int(),
    T.Key('base_url'): T.URL,
    T.Key('ldap_url'): (T.String() | T.Null)
})


def json_serial(obj):
    # From Stack Overflow: https://stackoverflow.com/a/22238613
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, RequestType):
        return get_type(obj)
    elif isinstance(obj, RequestStatus):
        return get_status(obj)
    elif isinstance(obj, RowProxy):
        return dict(zip(obj.keys(), obj.values()))
    raise TypeError('Type %s not serializable' % type(obj))


def dump_json(obj):
    """Wrapper for dumping JSON"""
    return dumps(obj, default=json_serial)


def get_type(type):
    """Get request type"""
    if type == RequestType.PAKREQ:
        return 'pakreq'
    elif type == RequestType.UPDREQ:
        return 'updreq'
    elif type == RequestType.OPTREQ:
        return 'optreq'
    else:
        return 'UnknownJellyExecutorException'


def get_status(status):
    """Get request status"""
    if status == RequestStatus.OPEN:
        return 'open'
    elif status == RequestStatus.DONE:
        return 'done'
    elif status == RequestStatus.REJECTED:
        return 'rejected'
    else:
        return 'UnknownJellyStatusException'


def password_hash(id, password):
    """Calculate password hash (Argon2), use this function if you want to
    generate password hashes (register new users)"""
    hasher = PasswordHasher()
    orig = '%s:%s' % (id, password)
    return hasher.hash(orig)


def password_verify(id, password, hash):
    """Verify password hash (Argon2), use this function if you want to
       authorize logins"""
    hasher = PasswordHasher()
    cleartext = '%s:%s' % (id, password)
    try:
        hasher.verify(hash, cleartext)
        return True
    except Exception:
        return False


def escape(text):
    """Escape string to avoid explosion"""
    try:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    except AttributeError:
        return 'N/A'
