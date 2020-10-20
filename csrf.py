from flask import current_app, request, session


def generate_csrf():
    return "csrf_token"


class CSRFMiddleware:

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.extensions['csrf'] = self

        app.jinja_env.globals['csrf_token'] = generate_csrf
        app.context_processor(lambda: {'csrf_token': generate_csrf})


        @app.before_request
        def csrf_protect():
            if not request.endpoint:
                return

            view = app.view_functions.get(request.endpoint)
            dest = f'{view.__module__}.{view.__name__}'

            if dest in self._exempt_views:
                return

            self.protect()


    def protect(self):
        try:
            validate_csrf(self._get_csrf_token())
        except ValidationError as e:
            logger.info(e.args[0])
            self._error_response(e.args[0])

        if request.is_secure and current_app.config['WTF_CSRF_SSL_STRICT']:
            if not request.referrer:
                self._error_response('The referrer header is missing.')

            good_referrer = f'https://{request.host}/'

            if not same_origin(request.referrer, good_referrer):
                self._error_response('The referrer does not match the host.')

        g.csrf_valid = True  # mark this request as CSRF valid
