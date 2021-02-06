from flask import Flask, render_template, url_for, redirect, request
from flask_pymongo import PyMongo
from weatherbit.api import Api
import requests

api_key = "075766a67b234c07800263424262e964"
api = Api(api_key)
api.set_granularity('daily')
app = Flask(__name__)
mongo = PyMongo()
app.config['MONGO_URI'] = 'mongodb+srv://jacknaylor:mongoPass@cluster0.xohuk.mongodb.net/Packer?retryWrites=true&w=majority'
mongo.init_app(app)
weather_url = "https://api.weatherbit.io/v2.0/forecast/daily"


# parse location for weatherbit.io api, will only accept city, country for locations outside of the united states
def parse_location(location):
    location = location.replace(" ", "")
    split = location.split(',')
    # remove province code from location
    if split[-1] != 'USA' and len(split)>2:
        location = split[0] + "," + split[2]

    return location


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=('GET', 'POST'))
def submit():
    if request.method == 'POST':
        people = request.form.get('people')
        location = request.form.get('searchTextField')
        daterange = request.form.get('daterange')
        location = parse_location(location)
        print(location)
        params = {'city': location, 'key': api_key}
        r = requests.get(url=weather_url, params=params)
        data = r.json()
        print(data['data'])

    return redirect(url_for('index'))
