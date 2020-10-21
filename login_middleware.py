from flask import (
    redirect,
    request,
    session,
    has_request_context,
)


def _get_authenticated():
    is_authenticated = False
    if has_request_context():
        print(session)
        # TODO: more check.
        if 'user' in session:
            is_authenticated = True

    return is_authenticated


def _context_processor():
    return dict(is_authenticated=_get_authenticated())


class LoginMiddleware:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        '''
        配置，在 template context 裡增加 is_authenticated.
        '''
        is_authenticated = False

        app.context_processor(_context_processor)
