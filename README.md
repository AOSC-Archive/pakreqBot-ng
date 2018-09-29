pakreqBot-ng
============

Gugugu  
<img src="https://upload.wikimedia.org/wikipedia/commons/4/43/Peace_dove.svg" alt="gugu" width="200" height="200"/>

TODO
----
- [ ] Web server
  - [ ] DB utility
    - [x] add, update requests/users
  - [ ] Auth
    - [x] ~~Telegram web auth~~ See below
    - [ ] Basic auth system
      - [ ] OAuth with other providers
  - [ ] Beautify
- [ ] Telegram bot
  - [ ] ~~Auth~~ Registeration and linking
    - [x] /register - Registeration
    - [x] /link - Link Telegram account to pakreq account
    - [x] /set_pw - Update password
    - [ ] /unlink - Unlink Telegram account
    - [ ] /set_username - Set username
  - [x] ~~Interact with web server~~ Access database directly
  - [ ] Basic functionality
    - [x] /list
    - [x] /pakreq, /updreq, /optreq
    - [x] /claim, /unclaim
    - [ ] /done, /reject
    - [ ] /set_eta
    - [ ] /help (Update needed)
...