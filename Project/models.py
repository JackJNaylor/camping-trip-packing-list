


# User Class
from flask_login import UserMixin
from . import db


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