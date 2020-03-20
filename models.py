import datetime
import string 

from app import db

class Member(db.Model):
    __tablename__ = 'Member'

    chatID = db.Column(db.Integer, primary_key = True, unique = True, nullable = False)
    telehandle = db.Column(db.String(32), unique = True, nullable = False)
    modified_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    #one-to-many model
    # tasks = db.relationship('Task', back_populates = 'Task', uselist = True)

    #one-to-one model
    timetable = db.relationship('Timetable', back_populates = 'user', uselist = False)

    def __init__(self, chatID, telehandle):
        self.chatID = chatID
        self.telehandle = telehandle

    def __repre__(self, chatID):
        return '<this user {}>'.format(self.chatID)

    def serialize(self):
        return {
            'chatID' : self.chatID,
            'telehandle' : self.telehandle
                }

class Timetable(db.Model):
    __tablename__ = 'Timetable'

    classcode = db.Column(db.String(20), unique = False, primary_key = True, nullable = False)
    day = db.Column(db.String(3), unique = False, nullable = False)
    time = db.Column(db.String(20), unique = False, nullable = False)
    chat_id = db.Column(db.Integer, db.ForeignKey('Member.chatID'))
    modified_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    #one-to-one model
    user = db.relationship('Member', back_populates = 'timetable', uselist = False)

    def __init__(self, classcode, day, time, chat_id):
        self.chat_id = chat_id
        self.classcode = classcode
        self.day = day
        self.time = time


    def __repre__(self, user):
        return '<this user {}>'.format(self.user)

    def serialize(self):
        return {
            'chat_id' : self.chat_id,
            'classcode' : self.classcode,
            'day' : self.day,
            'time' : self.time
                }
