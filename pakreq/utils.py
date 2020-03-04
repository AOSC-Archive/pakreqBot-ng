# utils.py

"""
Utilities
"""

import trafaret as T

from json import dumps
from argon2 import PasswordHasher
from datetime import date, datetime

from pakreq.db import RequestType, RequestStatus
from aiopg.sa.result import RowProxy

# Configuration checker
TRAFARET = T.Dict({
    T.Key('db'):
        T.Dict({
            'host': T.String(),
            'username': T.String(),
            'password': T.String(allow_blank=True),
            'database': T.String(),
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


def get_password_hasher():
    # time cost: 2^3, memory_cost: 2^16
    return PasswordHasher(time_cost=8, memory_cost=65536)


def password_hash(id, password):
    """Calculate password hash (Argon2), use this function if you want to
    generate password hashes (register new users)"""
    hasher = get_password_hasher()
    orig = '%s:%s' % (id, password)
    return hasher.hash(orig)


def password_verify(id, password, hash):
    """Verify password hash (Argon2), use this function if you want to
       authorize logins"""
    hasher = PasswordHasher()  # a default hasher here is fine since the params are stored with the hash
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
