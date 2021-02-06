from flask import Flask, render_template, url_for, redirect, request, flash
from flask_mongoengine import MongoEngine, Document
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from flask_pymongo import PyMongo
from weatherbit.api import Api
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests

api_key = "075766a67b234c07800263424262e964"
api = Api(api_key)
api.set_granularity('daily')
app = Flask(__name__)
# mongo = PyMongo()

# app.config['MONGO_URI'] = 'mongodb+srv://jacknaylor:mongoPass@cluster0.xohuk.mongodb.net/Packer?retryWrites=true&w=majority'
app.config['MONGODB_SETTINGS'] = {
    'db': 'Packer',
    'host': 'mongodb+srv://jacknaylor:mongoPass@cluster0.xohuk.mongodb.net/Packer?retryWrites=true&w=majority'
}

db = MongoEngine(app)
app.config['SECRET_KEY'] = 'klasjdlkhjlkgjoqi9ejlinalksdjhflkjaee'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# mongo.init_app(app)
weather_url = "https://api.weatherbit.io/v2.0/forecast/daily"


class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    name = db.StringField()
    email = db.StringField(max_length=30)
    password = db.StringField()


@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


class RegForm(FlaskForm):
    email = StringField('email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])


# parse location for weatherbit.io api, will only accept city, country for locations outside of the united states
def parse_location(location):
    location = location.replace(" ", "")
    split = location.split(',')
    # remove province code from location
    if split[-1] != 'USA' and len(split)>2:
        location = split[0] + "," + split[2]

    return location


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            existing_user = User.objects(email=form.email.data).first()
            if existing_user is None:
                hashpass = generate_password_hash(form.password.data, method='sha256')
                name = name = request.form.get('name')
                hey = User(name=name, email=form.email.data, password=hashpass).save()
                login_user(hey)
                return redirect(url_for('index'))
            else:
                flash('Email address already exists')
                return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated == True:
        return redirect(url_for('dashboard'))
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            check_user = User.objects(email=form.email.data).first()
            if check_user:
                if check_password_hash(check_user['password'], form.password.data):
                    login_user(check_user)
                    return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/submit', methods=('GET', 'POST'))
@login_required
def submit():
    # test_collection = mongo.db.test
    if request.method == 'POST':
        people = request.form.get('people')
        location = request.form.get('searchTextField')
        daterange = request.form.get('daterange')
        location = parse_location(location)
        print(location)
        # test_collection.insert_one({'itemName': 'Grill', 'Required': True, 'Weather': 'All', 'MaxTemp': None, 'MinTemp': None, 'unit': 1, 'type': 'Static' })
        params = {'city': location, 'key': api_key}
        # r = requests.get(url=weather_url, params=params)
        # data = r.json()
        # print(data['data'])

    return redirect(url_for('index'))


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))