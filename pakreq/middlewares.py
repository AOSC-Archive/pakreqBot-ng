# middlewares.py

"""
Middlewares and the setup of middlewares
"""

import aiohttp_jinja2

from aiohttp import web


async def handle_404(request):
    """404 handler"""
    return aiohttp_jinja2.render_template('404.html', request, {})


async def handle_500(request):
    """500 handler"""
    return aiohttp_jinja2.render_template('500.html', request, {})


def create_error_middleware(overrides):
    """Create error middleware"""
    @web.middleware
    async def error_middleware(request, handler):
        """Error middlewares"""
        try:
            response = await handler(request)

            override = overrides.get(response.status)
            if override:
                return await override(request)

            return response

        except web.HTTPException as ex:
            override = overrides.get(ex.status)
            if override:
                return await override(request)

            raise

    return error_middleware


def setup_middlewares(app):
    """Setup middlewares"""
    error_middleware = create_error_middleware({
        404: handle_404,
        500: handle_500
    })
    app.middlewares.append(error_middleware)
