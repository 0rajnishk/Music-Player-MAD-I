from flask import Flask, render_template

app = Flask(__name__)

from application import database
from application import controllers
with app.app_context():
    
    controllers.addadmin()

