import os
import json

if os.environ.get('COMPUTERNAME')=='CAPTAIN2020':
    with open(r'C:\Users\captian2020\Documents\config_files\config_whatSticks.json') as config_file:
        config = json.load(config_file)
elif os.environ.get('TERM_PROGRAM')=='Apple_Terminal':
    with open('/Users/nick/Documents/config_files/whatSticks.json') as config_file:
        config = json.load(config_file)
else:
    with open('/home/ubuntu/environments/config.json') as config_file:
        config = json.load(config_file)




class Config:
    SECRET_KEY = config.get('SECRET_KEY_DMR')
    SQLALCHEMY_DATABASE_URI = config.get('SQL_URI_WHAT_STICKS')
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = config.get('MAIL_PASSWORD_KM')
    MAIL_USERNAME = config.get('MAIL_USERNAME_KM')
    DEBUG = True
    WSH_HOME_DIR=os.path.join(os.path.dirname(__file__))
    UPLOADED_FILES_FOLDER = os.path.join(os.path.dirname(__file__), 'static/files_uploaded')
    BOKEH_THEME = config.get('BOKEH_THEME')
    # UTILITY_FILES_FOLDER = os.path.join(os.path.dirname(__file__), 'static/files_utility')
    # QUERIES_FOLDER = os.path.join(os.path.dirname(__file__), 'static/queries')
    # FILES_DATABASE = os.path.join(os.path.dirname(__file__), 'static/files_database')
