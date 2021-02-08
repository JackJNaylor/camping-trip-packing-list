from flask import Flask, render_template, url_for, redirect, request, flash
from flask_mongoengine import MongoEngine, Document
from mongoengine.queryset.visitor import Q
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from weatherbit.api import Api
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import math
from datetime import datetime, date


api_key = "075766a67b234c07800263424262e964"
api = Api(api_key)
api.set_granularity('daily')
app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {
    'db': 'Packer',
    'host': 'mongodb+srv://jacknaylor:mongoPass@cluster0.xohuk.mongodb.net/Packer?retryWrites=true&w=majority'
}

db = MongoEngine(app)
app.config['SECRET_KEY'] = 'klasjdlkhjlkgjoqi9ejlinalksdjhflkjaee'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
weather_url = "https://api.weatherbit.io/v2.0/forecast/daily"

# Weather code sets
RainCodes = {300, 301, 302, 500, 501, 502, 511, 520, 521, 522}
SnowCodes = {600, 601, 602, 610, 611, 612, 621, 622, 623}
ThunderCodes = {200, 201, 202, 230, 231, 232, 233}


# User Class
class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    name = db.StringField()
    email = db.StringField(max_length=30)
    password = db.StringField()


# Packing Items Class
class PackingItem(db.Document):
    meta = {'collection': 'packing_items'}
    ItemName = db.StringField()
    Required = db.BooleanField()
    Weather = db.StringField()
    MaxTemp = db.IntField()
    MinTemp = db.IntField()
    Unit = db.FloatField()
    UsageType = db.StringField()
    Group = db.StringField()


# Packing List Class
class PackingList(db.Document):
    meta = {'collection': 'packing_lists'}
    ListName = db.StringField()
    GroupList = db.ListField()
    IndividualList = db.ListField()
    OwnerIds = db.ListField()


# RegForm for logging in
class RegForm(FlaskForm):
    email = StringField('email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])


# parse location for weatherbit.io api, will only accept city, country for locations outside of the united states
def parse_location(location):
    print(location)
    split = location.split(',')

    # remove province code from location
    if split[-1] != 'USA' and len(split)>2:
        location = split[0] + "," + split[2]

    return location


# parse weather data to get min and max temps and a set of all weather conditions
def parse_weather_data(data):
    conditions = set()
    for log in data:
        low = log['low_temp']
        high = log['max_temp']
        code = log['weather']['code']

        # initial min max
        if len(conditions) == 0:
            minTemp = low
            maxTemp = high
        if low < minTemp:
            minTemp = low
        if high > maxTemp:
            maxTemp = high

        if code in RainCodes or code in ThunderCodes:
            conditions.add("Rain")
        elif code in SnowCodes:
            conditions.add("Snow")

    return minTemp, maxTemp, conditions


# Make API call to WeatherBit.io to get 16 forecast and select data for selected dates
def get_weather(location, daterange):

    # get request for weather forecast based on city
    params = {'city': location, 'key': api_key}
    try:
        r = requests.get(url=weather_url, params=params)
        data = r.json()
        print(data['data'][0]['weather']['code'])

        # use dates to get trip length and indicies for relevant weather data
        today = date.today()
        daterange.replace(" ", "")
        split_date = daterange.split('-')
        split_start = split_date[0].split('/')
        split_end = split_date[1].split('/')
        start_date = date(int(split_start[2]), int(split_start[0]), int(split_start[1]))
        end_date = date(int(split_end[2]), int(split_end[0]), int(split_end[1]))
        trip = end_date-start_date
        trip_length = trip.days
        start = start_date - today
        end = end_date - today

        # account for python slice inclusivity and starting indicies
        start_index = int(start.days) + 1
        end_index = int(end.days) + 2

        # get weather data for trip dates
        new_data = data['data'][start_index:end_index]
        return new_data, trip_length
    except:
        print("an error has occured")


# get the packing list based on the weather
def get_list(data):
    low_temp, high_temp, conditions = parse_weather_data(data)
    if len(conditions) == 0:
        items = PackingItem.objects(Q(Required="True") | Q(MaxTemp__gte=low_temp) | Q(MinTemp__lte=high_temp))
    elif len(conditions) == 1:
        condition = conditions.pop()
        items = PackingItem.objects(Q(Required="True") | Q(MaxTemp__gte=low_temp) | Q(MinTemp__lte=high_temp) | Q(Weather=condition))
    else:
        items = PackingItem.objects(
            Q(Required="True") | Q(MaxTemp__gte=low_temp) | Q(MinTemp__lte=high_temp) | Q(Weather="Rain") | Q(Weather="Snow"))

    return items, conditions


# Generate packing list split into group and individual items with quantities of items
def get_quantities(item_list, trip_length, people):
    individual_list = []
    group_list = []
    for item in item_list:

        # Quantity is static
        if item.UsageType == "Singular":
            if item.Group =="True":
                entry = "1 " + str(item.ItemName)
                group_list.append(entry)
            else:
                entry = "1 " + str(item.ItemName)
                individual_list.append(entry)

        # Quantity depends only on number of people on trip
        if item.UsageType == "Personal":
            if item.Group == "True":
                quant = str(math.ceil(float(item.Unit) * people))
                entry = quant + " " + str(item.ItemName)
                group_list.append(entry)
            else:
                quant = str(math.ceil(float(item.Unit)))
                entry = quant + " " + str(item.ItemName)
                individual_list.append(entry)

        # quantity depends of trip length and number of people
        if item.UsageType == "Variable":
            quant = str(math.ceil(float(item.Unit) * people * trip_length))
            if item.Group == "True":
                entry = quant + " " + str(item.ItemName)
                group_list.append(entry)
            else:
                entry = quant + " " + str(item.ItemName)
                individual_list.append(entry)


        # Quantity depends only on length of trip
        if item.UsageType == "Daily":
            quant = str(math.ceil(float(item.Unit) * trip_length))
            if item.Group == "True":
                entry = quant + " " + str(item.ItemName)
                group_list.append(entry)
            else:
                entry = quant + " " + str(item.ItemName)
                individual_list.append(entry)

    return individual_list, group_list


# Store created list in DB for user to access later
def store_lists(list_name, individual_list, group_list):
    myList = PackingList(ListName=list_name, IndividualList=individual_list, GroupList=group_list, OwnerIds=[current_user.id])
    PackingList.objects.insert(myList)
    return myList.id


@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


# Check if user exists, if not register user and login
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()
    error = None
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
                error = "Email address already exists"
                print(error)
                return redirect(url_for('login', error=error))
    return render_template('register.html', form=form)


# Login function using RegForm
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            check_user = User.objects(email=form.email.data).first()
            if check_user:
                if check_password_hash(check_user['password'], form.password.data):
                    login_user(check_user)
                    return redirect(url_for('index'))
        else:
            error = "Incorrect email or password"
    return render_template('login.html', form=form, error=error)


@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


# Create List Based on Weather and Number of People
@app.route('/submit', methods=('GET', 'POST'))
@login_required
def submit():
    error = None
    if request.method == 'POST':
        list_name = request.form.get('listName')
        people = request.form.get('people')
        location = request.form.get('searchTextField')
        daterange = request.form.get('daterange')

        location = parse_location(location)

        try:
            data, trip_length = get_weather(location, daterange)

            item_list, conditions = get_list(data)

            individual_list, group_list = get_quantities(item_list, trip_length, float(people))

            list_id = store_lists(list_name, individual_list, group_list)


            return redirect(url_for('show_list', list_id=list_id))
        except:
            error = "No Weather Data Available, Please Enter Closest City/Town"
    return render_template('index.html', error=error)


# View a List
@app.route('/<list_id>')
@login_required
def show_list(list_id):
    list_object = PackingList.objects(id=list_id)
    my_list = list_object[0]
    return render_template('list.html', name=my_list.ListName, individual=my_list.IndividualList, group=my_list.GroupList, id=list_id)


# Show all lists for a user
@app.route('/my_lists')
@login_required
def my_lists():
    user_id = current_user.id
    all_lists = PackingList.objects(OwnerIds=user_id)
    return render_template('my_lists.html', my_lists=all_lists)


# Delete a List
@app.route('/delete/<list_id>')
@login_required
def delete(list_id):
    PackingList.objects(id=list_id).delete()
    return redirect(url_for('index'))


# Add a User to a List
@app.route('/add_owner/<list_id>', methods=['POST'])
@login_required
def add_owner(list_id):
    email = request.form.get('email')
    existing_user = User.objects(email=email).first()
    shared_list = PackingList.objects(id=list_id).get()
    if existing_user:
        if existing_user.id not in shared_list.OwnerIds:
            shared_list.OwnerIds.append(existing_user.id)
            shared_list.save()
    else:
        flash("Email invalid")

    return redirect(url_for('show_list', list_id=list_id))


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))