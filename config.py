import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI', 
        'mysql://root:password@localhost/seat_db'  # change 'password' to your MySQL root password
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
