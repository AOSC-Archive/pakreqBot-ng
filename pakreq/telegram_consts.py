# telegram_consts.py

"""
Constant strings for telegram.py
"""

REQUEST_DETAIL = """\
<b>{name}</b>:
  <b>ID</b>: {id}
  <b>Status</b>: {status}
  <b>Type</b>: {rtype}
  <b>Description</b>: {desc}
  <b>Requester</b>: {req_name}({req_id})
  <b>Packager</b>: {pak_name}({pak_id})
  <b>Created on</b>: {date}
  <b>Note</b>: {eta}

"""

FULL_LIST = """
Please visit {url} for the full listing.
"""

REQUEST_BRIEF_INFO = """\
ID: {id} <b>{name}</b> (<i>{rtype}</i>): {description}
"""

REGISTER_FIRST = """\
You have to <b>register</b> or <b>link</b> your account first.
Please refer to /help for full usage.
"""

TOO_FEW_ARGUMENTS = """\
Too <b>few</b> arguments.
Please refer to /help for full usage.
"""

TOO_MANY_ARUGMENTS = """\
Too <b>many</b> arguments.
Please refer to /help for full usage.
"""

NO_PENDING_REQUESTS = """\
No pending request.
"""

INVALID_REQUEST = """\
Invalid request, use /help to view the full usage.
"""

IS_ALREADY_IN_THE_LIST = """\
{rtype} {name} is <b>already</b> in the list.
"""

SUCCESSFULLY_ADDED = """\
Successfully added {name} to the {rtype} list, id of this request is {id}.
"""

CLAIM_FIRST = """\
<b>You have to claim request {id} first.</b>
"""

ACTION_SUCCESSFUL = """\
Successfully <b>{action}ed</b> request <b>{id}</b>.
"""

REQUEST_NOT_FOUND = """\
<b>Request ID {id} not found.</b>
"""

ALREADY_REGISTERED = """\
You've already registered.
"""

USERNAME_ALREADY_TAKEN = """\
Username {username} already taken, please specify another one by:
<code>/register [username] [password]</code>
"""

REGISGER_SUCCESS = """\
Registeration successful, your username is {username}.
"""

PASSWORD_EMPTY = """\
You password is empty right now, please set a new password by:
<code>/passwd [password]</code>
"""

LINK_SUCCESS = """\
Successfully linked {username} to this telegram account.
"""

INCORRECT_CREDENTIALS = """\
Link unsuccessful: Incorrect username or password.
"""

PASSWORD_UPDATE_SUCCESS = """\
Password set successfully.
"""

FULL_LIST_PRIVATE_ONLY = """\
Listing all requests is only allowed in private chats.
"""

PROCESS_SUCCESS = """\
Successfully processed request {id}.
"""

ONLY_REQUESTER_CAN_EDIT = """\
Only requester can edit the description for request {id}.
"""

ERROR_MSG = """\
Sorry, this bot has encountered an error: {err}
Details: {err_detail}

Please try again later and/or\
 open a new ticket at https://github.com/AOSC-dev/pakreqBot-ng/issues/new
"""

HELP_CRUFT = """\
A bot designed to <b>EXECUTE</b> Jelly.

Command list:
/pakreq [package] [description] - Add a new pakreq.
/updreq [package] [description] - Add a new updreq.
/optreq [package] [description] - Add a new optreq.
/claim [package] - Claim a request, leave [package] for a random claim.
/unclaim [package] - Unclaim  a request.
/done [package] - Mark a request as done.
/eta [package] [date(format:YYYY-mm-dd)] - Set an ETA for a request.
/reject [package] [reason] - Reject a request with [reason].
/list [package] - List pending requests.
/dlist [package] - List done requests.
/rlist [package] - List rejected requests.
/passwd [new password] - Set new password.
/register [user name] - Register a new user.
/subscribe - Subscribe.
/unsubscribe - Unsubscribe.
/help - Show this help message.
"""


def error_msg(desc, detail='N/A'):
    return ERROR_MSG.format(err=desc, err_detail=detail)
