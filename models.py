import datetime
import string 

from app import db

class Member(db.Model):
	__tablename__ = 'Member'

	chatID = db.Column(db.Integer, primary_key = True, unique = True, nullable = False)
	telehandle = db.Column(db.String(32), unique = True, nullable = False)
	modified_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

	# one-to-one model
	timetable = db.relationship('Timetable', back_populates = 'user', uselist = False)

	# one-to-many model
	member_task = db.relationship('Task', back_populates='task_member', uselist=True, cascade='all, delete-orphan', lazy=True)

	
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
			'time' : self.time, 
				}

class Group(db.Model):
	__tablename__ = 'Group'

	groupid = db.Column(db.Integer, primary_key=True)
	# commontime = db.Column(db.list, unique=True, nullable=False)  
	# theres no way to make this a list/dict directly. will figure out soon

	# one-to-many model
	majdates_group = db.relationship('Maj_Dates', back_populates='group_majdates', uselist=True, cascade='all, delete-orphan', lazy=True)

	# one-to-many model
	meeting_group = db.relationship('Meeting', back_populates='group_meeting', uselist=True, cascade='all, delete-orphan', lazy=True)

	# one-to-many model
	group_task = db.relationship('Task', back_populates='task_group', uselist=True, cascade='all, delete-orphan', lazy=True)

	
	def __init__(self, groupid, commontime):
		self.groupid = groupid
		self.commontime = commontime

	def __repre__(self, groupid):
		return '<group {}>'.format(self.groupid)

	def serialize(self):
		return {
			'groupid': self.groupid, 
			'commontime': self.commontime,
		}

class Maj_Dates(db.Model):

	__tablename__ = 'maj_dates'

	id = db.Column(db.Integer, primary_key=True)
	groupid = db.Column(db.Integer, db.ForeignKey('Group.groupid'), nullable=False)
	major_desc = db.Column(db.String(80), unique=True, nullable=False)
	deadline = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
	
	group_majdates = db.relationship('Group', back_populates='majdates_group ')

	def __init__(self, id, groupid, major_desc, deadline):
		self.id = id
		self.groupid = groupid
		self.major_desc = major_desc
		self.deadline = deadline 
	
	def __repre__(self, id, groupid):
		return '<major date id {} for group {}>'.format(self.id, self.groupid)

	def serialize(self):
		return {
			'id': self.id,
			'groupid' : self.groupid,
			'major deadline description': self.major_desc,
			'deadline': self.deadline, 
		}

class Meeting(db.Model):
	__tablename__ = 'meeting'

	id = db.Column(db.Integer, primary_key=True)
	groupid = db.Column(db.Integer, db.ForeignKey('Group.groupid'), nullable=False)
	venue = db.Column(db.String(80))
	meeting_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
	agenda = db.Column(db.String(80), unique=True)

	group_meeting = db.relationship('Group', back_populates='meeting_group')

	def __init__(self, id, groupid, venue, meeting_datetime, agenda):
		self.id = id
		self.groupid = groupid
		self.venue = venue
		self.meeting_datetime = meeting_datetime
		self.agenda = agenda 
	
	def __repr__(self):
		return '<meeting id {} for group {} >'.format(self.id, self.groupid)

	def serialize(self):
		return {
			'id': self.id,
			'groupid' : self.groupid,
			'venue': self.venue,
			'date and time of meeting': self.meeting_datetime,
			'agenda': self.agenda 
		}


class Task(db.Model):
	__tablename__ = 'Task'
	id = db.Column(db.Integer, primary_key=True)
	chat_id = db.Column(db.Integer, db.ForeignKey('Member.chatID'), nullable=False)
	groupid = db.Column(db.Integer, db.ForeignKey('Group.groupid'), nullable=False)
	#member = db.Column(db.Float, unique=True, nullable=False) #see if we can store/keep track of members after first initialization, --> in-line keyboard # thinkn no nned cause back populate to user table alr
	header = db.Column(db.String(80), unique=True, nullable=False)
	deadline = db.Column(db.DateTime, unique=False, nullable=False) #try in-line text
	desc = db.Column(db.String(1000), unique=False, nullable=False)
	
	# one-to-many model
	task_member = db.relationship('Member', back_populates='member_task')
	
	# one-to-many model
	task_group = db.relationship('Group', back_populates='group_task')
	
	def __init__(self, header, deadline, desc):
		#self.member = member
		self.header = header
		self.deadline = deadline
		self.desc = desc

	def __repr__(self):
		return '<id {}>'.format(self.id)

	def serialize(self):
		return {
		    'id': self.id, 
		    #'member': self.member,
		    'header': self.header,
		    'deadline': self.deadline,
		    'desc': self.desc, #key on the left can be anything, but the reference on the right has to be linked to the things on top
		}
