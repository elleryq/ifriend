import os 


class Config:
    # 除錯
    DEBUG = os.environ.get('FLASK_DEBUG', "False").lower() == "true"

    # SECRET_KEY
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'this_is_an_example').encode('ascii')

    # 上傳路徑
    UPLOAD_FOLDER = os.environ.get('FLASK_UPLOAD_FOLDER', './media')

    # 允許最大長度
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 只允許 1MB

