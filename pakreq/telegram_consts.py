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
Please visit {url} for the full list of requests.
"""

REQUEST_BRIEF_INFO = """\
ID: {id} <b>{name}</b> (<i>{rtype}</i>): {description}
"""

REGISTER_FIRST = """\
You have to <b>register</b> or <b>link</b> your account first.
Please refer to /help for detailed usage.
"""

TOO_FEW_ARGUMENTS = """\
Too <b>few</b> arguments.
Please refer to /help for detailed usage.
"""

TOO_MANY_ARUGMENTS = """\
Too <b>many</b> arguments.
Please refer to /help for detailed usage.
"""

NO_PENDING_REQUESTS = """\
No pending request.
"""

INVALID_REQUEST = """\
Invalid request, please refer to /help for detailed usage.
"""

IS_ALREADY_IN_THE_LIST = """\
{rtype} {name} is <b>already</b> in the list.
"""

SUCCESSFULLY_ADDED = """\
Successfully added {name} to the {rtype} list, id of this request is {id}.
"""

REOPEN_FIRST = """\
<b>You have to reopen request {id} first.</b>
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
You have already registered.
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
Successfully linked this Telegram account to {username}.
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

UNLINK_SUCCESS = """\
Your Telegram account is now no longer associated with any pakreq account.
"""

UNLINK_NOTHING_TO_UNLINK = """\
You are current not associated with any pakreq account.
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

WHOAMI = """\
You are <b>{username}</b> and your user ID is <b>{id}</b>.
"""

SEARCH_RESULT = """\
<b>Results</b>:
{matches}

ONLY first 10 requests are shown, \
please visit {url} for the full list of requests.
"""

NO_MATCH_FOUND = """\
No match for <b>{keyword}</b> found.
"""

HELP_CRUFT = """\
A bot designed to <b>EXECUTE</b> Jelly.

Command list:
/ping - Pong!
/register [username] [password] - Register a new account.
/passwd &lt;password&gt; - Set new password.
/link [username] [password] - Link your Telegram ID to your pakreq account.
/unlink - Unlink any pakreq account that is associated with your Telegram ID.
/whoami - Get information of current account.
/pakreq &lt;package name&gt; [description] - Add a new pakreq.
/updreq &lt;package name&gt; [description] - Add a new updreq.
/optreq &lt;package name&gt; [description] - Add a new optreq.
/claim [package id] - Claim a request, leave [package] for a random claim.
/unclaim &lt;package id&gt; - Unclaim  a request.
/done &lt;package id&gt; - Mark a request as done.
/reject &lt;package id&gt; - Reject a request.
/reopen &lt;package id&gt; - Reopen a request.
/edit_desc &lt;package id&gt; [description] - Edit description.
/note &lt;package id&gt; [note] - Set a note for &lt;package id&gt;.
/list [package id] - List requests by id, up to 5 ids at a time.
/search &lt;keyword&gt; - Search requests.
/help - Show this help message.
"""


def error_msg(desc, detail='N/A'):
    return ERROR_MSG.format(err=desc, err_detail=detail)
