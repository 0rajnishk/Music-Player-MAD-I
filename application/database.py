from application import app
from flask_sqlalchemy import SQLAlchemy


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db= SQLAlchemy(app)

from application import models


with app.app_context():
    # db.drop_all()
    db.create_all()