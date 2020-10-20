import os 


class Config:
    DEBUG = os.environ.get('FLASK_DEBUG', "False").lower() == "true"
    SECRET_KEY = b'this_is_an_example'

