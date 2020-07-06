import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from datetime import timedelta

app=Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///testdb.sqlite3'
app.secret_key = os.urandom(20)
# app.config['SECRET_KEY'] = 'bod\xda\x96?\x91\xd7\xf5)&\xa1\xc2]\x84\x13\x9f'
# app.config['SQLALCHEMY_DATABASE_URI'] =os.environ.get('DATABASE_URL')
# app.config['SECRET_KEY'] =os.environ.get('SECRET')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_DURATION']= timedelta(seconds=60)
db= SQLAlchemy(app)
from routes import *

db.create_all()
db.session.commit()