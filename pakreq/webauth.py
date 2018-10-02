from aiohttp_security.abc import AbstractAuthorizationPolicy

import pakreq.db


class PakreqAuth(AbstractAuthorizationPolicy):
    def __init__(self, app):
        self.app = app
        super().__init__()

    async def authorized_userid(self, identity):
        return identity

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False
        return True
