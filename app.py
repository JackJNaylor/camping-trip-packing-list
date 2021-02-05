from flask import Flask, render_template, url_for, redirect, request
from weatherbit.api import Api

api_key = "075766a67b234c07800263424262e964"
api = Api(api_key)
api.set_granularity('daily')
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=('GET', 'POST'))
def submit():
    if request.method == 'POST':
        people = request.form.get('people')
        location = request.form.get('searchTextField')
        daterange = request.form.get('daterange')
        print(people)
        print(location)
        print(daterange)
        #location = location.replace(" ", "")
        # forecast = api.get_forecast(city="Raleigh,NC")
        forecast = api.get_forecast(city=str(location))
        print(forecast.get_series('temp'))
    return redirect(url_for('index'))
