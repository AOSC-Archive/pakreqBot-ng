REQUEST_DETAIL = """
<b>{name}:</b>
  <b>Type:</b> {type}
  <b>Description:</b> {desc}
  <b>Requester:</b> {req_name}({req_id})
  <b>Packager:</b> {pak_name}({pak_id})
  <b>Created on:</b> {date}
  <b>ETA:</b> {eta}
"""

ERROR_MSG = """
Sorry, this bot has encountered an error: {err}
Details: {err_detail}

Please open a new ticket at https://github.com/AOSC-dev/pakreqBot-ng/issues/new
"""

HELP_CRUFT = """
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
