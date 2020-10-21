import os
import hashlib
from urllib.parse import urlparse
from flask import current_app, request, session, g
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import safe_str_cmp


CSRF_FIELD_NAME = 'csrf_token'
CSRF_HEADER_NAME_LIST = ['X-CSRFToken', 'X-CSRF-Token']
CSRF_ALLOWED_METHOD_LIST = ['POST', 'PUT', 'PATCH', 'DELETE']
CSRF_TOKEN_SALT = 'csrf_token_salt'


def generate_csrf():
    """
    產生 CSRF token
    """
    secret_key = current_app.secret_key

    if CSRF_FIELD_NAME not in g:
        s = URLSafeTimedSerializer(secret_key, salt=CSRF_TOKEN_SALT)

        if CSRF_FIELD_NAME not in session:
            session[CSRF_FIELD_NAME] = hashlib.sha1(os.urandom(64)).hexdigest()

        try:
            token = s.dumps(session[CSRF_FIELD_NAME])
        except TypeError:
            session[CSRF_FIELD_NAME] = hashlib.sha1(os.urandom(64)).hexdigest()
            token = s.dumps(session[CSRF_FIELD_NAME])

        setattr(g, CSRF_FIELD_NAME, token)

    return g.get(CSRF_FIELD_NAME)


def same_origin(current_uri, compare_uri):
    """
    檢查是否同源
    """
    current = urlparse(current_uri)
    compare = urlparse(compare_uri)

    return (
        current.scheme == compare.scheme
        and current.hostname == compare.hostname
        and current.port == compare.port
    )


class ValidationError(Exception):
    pass


class CSRFError(Exception):
    pass


def validate_csrf(data, secret_key=None, time_limit=None, token_key=None):
    """
    檢查 CSRF token 是否正確。
    """
    secret_key = current_app.secret_key
    time_limit = 30 * 60  # token 有效期限制為半小時

    if not data:
        raise ValidationError('No CSRF token.')

    if CSRF_FIELD_NAME not in session:
        raise ValidationError('No CSRF session token.')

    s = URLSafeTimedSerializer(secret_key, salt='wtf-csrf-token')

    try:
        token = s.loads(data, max_age=time_limit)
    except SignatureExpired:
        raise ValidationError('The CSRF token has expired.')
    except BadData:
        raise ValidationError('The CSRF token is invalid.')

    if not safe_str_cmp(session[CSRF_FIELD_NAME], token):
        raise ValidationError('The CSRF tokens do not match.')


class CSRFMiddleware:
    """
    CSRF Middleware for injecting CSRF token in template context
    """
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        在 Flask 的 template engine context 放入 csrf token
        以及安插請求前的處理
        """
        app.extensions['csrf'] = self

        app.jinja_env.globals['csrf_token'] = generate_csrf
        app.context_processor(lambda: {'csrf_token': generate_csrf})


        @app.before_request
        def csrf_protect():
            if not request.endpoint:
                return

            self.protect()


    def protect(self):
        """
        檢查 CSRF
        """
        # 當 HTTP METHOD 為指定的 method 時，才檢查
        if request.method not in CSRF_ALLOWED_METHOD_LIST:
            return

        try:
            validate_csrf(self._get_csrf_token())
        except ValidationError as e:
            self._error_response(e.args[0])

        # 檢查來源，不同時，也需要回應錯誤
        if request.is_secure:
            if not request.referrer:
                self._error_response('No referrer header.')

            good_referrer = f'https://{request.host}/'

            if not same_origin(request.referrer, good_referrer):
                self._error_response('The referrer does not match the host.')

        g.csrf_valid = True  # mark this request as CSRF valid

    def _get_csrf_token(self):
        """
        從表單或 header 裡取得csrf token
        """
        # 從表單中找
        base_token = request.form.get(CSRF_FIELD_NAME)

        if base_token:
            return base_token

        # 在標頭裡找 csrf token
        for header in CSRF_HEADER_NAME_LIST:
            csrf_token = request.headers.get(header)

            if csrf_token:
                return csrf_token

        return None

    def _error_response(self, reason):
        """
        丟出例外
        """
        raise CSRFError(reason)
