import telebot
from telebot import types
import schedule
import time
import requests 
import request #must alw import this first before the from flask import request LOL
from flask import Flask, request, Response, jsonify
import os
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast, DATE
from sqlalchemy.ext.associationproxy import association_proxy
from datetime import datetime, date, timedelta
from collections import OrderedDict 
from apscheduler.schedulers.background import BackgroundScheduler
import ast
from multiprocessing import Process, Manager
from os import path, getenv
import csv

TOKEN = ''#change this to ur TOKEN
bot = telebot.TeleBot(token=TOKEN)

#knownUsers = [] #https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/detailed_example/detailed_example.py
majordatelist = []
meetingdatelist = []
meetingvenuelist = []
groupidlist = []
chat_idlist = []
telehandlelist = []
groupsmemberbelongto = []
groupsnamememberbelongto = []
savedgroupid = []
commitlist = []
printcommontime = []
activegroupid = []
activechatid = []
convert_to_binary_dict = {}

commands = {  # command description used in the "help" command
	'start'       : 'Initialize the bot',
	'help'        : 'Gives you information about the available commands',
	'majordates'  : 'Important dates to take note for particular module',
	'majordatesreminder'    : 'Returns a list of all important dates and what so important about it',
	'delmajordates': 'deletes existing record with particular date for majordates',
	'setmeeting'   : 'set new meeting',
	'meetingreminder': 'Returns a list of all meetings coming up',
	'delmeeting'   : 'deletes existing record with particular date for meeting',
	'settask' : 'set new task for individual in a group',
	'deltask' : 'delete task created for an individual inside a group',
	'taskreminder' : 'Returns all tasks due for particular group to an individual',
	'end'         : 'to end commands'
} #just for reference sake

users_state = {'get deadlines': 0, 'get desc': 0, 'get deldate': 0, 'get meetingdate':0, 'get meetingvenue':0,'get meetingagenda':0,'get delmeeting':0,'get taskusername':0,'get taskdatedesc':0,'get files':0} 
#multiple groups need dict of dict. u wna check what is the user state of ea particular group
#{'-12345567':{users_state}} #to handle all the groups' users_state
multigroup = {}
user_state = {'get deltask':0,'get deltaskdate':0, 'get taskreminder':0}
multippl = {}

filenamedict = {}
group_one_schedule = {
	'Mon': [[900,1000], [1000,1100], [1100,1200], [1200,1300], [1300,1400], [1400,1500], [1500,1600], [1600,1700], [1700,1800], [1800,1900]],
	'Tue': [[900,1000], [1000,1100], [1100,1200], [1200,1300], [1300,1400], [1400,1500], [1500,1600], [1600,1700], [1700,1800], [1800,1900]],
	'Wed': [[900,1000], [1000,1100], [1100,1200], [1200,1300], [1300,1400], [1400,1500], [1500,1600], [1600,1700], [1700,1800], [1800,1900]],
	'Thu': [[900,1000], [1000,1100], [1100,1200], [1200,1300], [1300,1400], [1400,1500], [1500,1600], [1600,1700], [1700,1800], [1800,1900]],
	'Fri': [[900,1000], [1000,1100], [1100,1200], [1200,1300], [1300,1400], [1400,1500], [1500,1600], [1600,1700], [1700,1800], [1800,1900]]
	}

# DOWNLOADS_FOLDER = os.path.abspath  #r"C:/Users/Jolene Pek/Downloads/SMU/SMT203/heroku/heroku"
def write_json(data,filename = 'trytelebot.json'):
	with open(filename, 'w') as f:
		json.dump(data,f,indent=4,ensure_ascii=False) 

# def find_at(msg):
# 	for text in msg:
# 		if '@' in text:
# 			return text

app = Flask(__name__)
# app.debug = True

# Step 03: add database configurations here
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://projectuser:password@localhost:5432/projectdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Step 04: import models
from models import MemberGroupTask, Member, Timetable, Group, Maj_Dates, Meeting, group_member_table

@app.route('/', methods = ['POST']) # binds URL to view function
def index():
	if request.headers.get('content-type') == 'application/json':
		json_string = request.get_json()
		write_json(json_string, 'telebot.json')
		update = telebot.types.Update.de_json(json_string)
		bot.process_new_updates([update])
		return "!",200 #refer to https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/webhook_examples/webhook_flask_echo_bot.py

@bot.message_handler(commands=['start'])
def start(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		group_name = message.chat.title
		bot.send_message(group_id,'Welcome! Can I get everyone in this group to reply me with \"hello\"! Press /end when all of you have done that!')
		try:
			new_group = Group(groupid=str(group_id),commontime = None,group_name=group_name) #the commontime shd be the calculator but i lazy craft now
			db.session.add(new_group)
			try: #the try except and finally appear a few times in this app.py. its for error handling purposes. see https://stackoverflow.com/questions/8870217/why-do-i-get-sqlalchemy-nested-rollback-error
				db.session.commit()
			except:
				db.session.rollback()
				raise
			finally:
				db.session.close()
			multigroup[str(group_id)] = users_state #{'get deadlines': 0, 'get desc': 0, 'get deldate': 0, 'get meetingdate':0, 'get meetingvenue':0,'get meetingagenda':0,'get delmeeting':0,'get taskusername':0,'get taskdatedesc':0, 'get deltask':0} 
		except:
			multigroup[str(group_id)] = users_state #{'get deadlines': 0, 'get desc': 0, 'get deldate': 0, 'get meetingdate':0, 'get meetingvenue':0,'get meetingagenda':0,'get delmeeting':0,'get taskusername':0,'get taskdatedesc':0, 'get deltask':0} 

@bot.message_handler(commands=['help'])
def help(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		chat_id = message.from_user.id
		# try:
		# 	new_group = Group(groupid=str(group_id), commontime = str(group_id*2)) #the commontime shd be the calculator but i lazy craft now
		# 	db.session.add(new_group)
		# 	try: #the try except and finally appear a few times in this app.py. its for error handling purposes. see https://stackoverflow.com/questions/8870217/why-do-i-get-sqlalchemy-nested-rollback-error
		# 		db.session.commit()
		# 	except:
		# 		db.session.rollback()
		# 		raise
		# 	finally:
		# 		db.session.close()
		# 	multigroup[str(group_id)] = {'get deadlines': 0, 'get desc': 0, 'get deldate': 0, 'get meetingdate':0, 'get meetingvenue':0,'get meetingagenda':0,'get delmeeting':0,'get taskusername':0,'get taskdatedesc':0, 'get deltask':0} 
		# 	bot.send_message(group_id,"""Welcome! 
		# 	The different functions are as follows:
		# 	/majordates: Input any major dates to take note of for the whole group 
		# 	/majordatesreminder: Return all your major dates
		# 	/delmajordates: Remove records of a particular major date
		# 	/setmeeting: Set a new meeting
		# 	/meetingreminder: Returns all upcoming meetings
		# 	/delmeeting: Remove records of a meeting with particular date""")
		# except:
		# 	multigroup[str(group_id)] = {'get deadlines': 0, 'get desc': 0, 'get deldate': 0, 'get meetingdate':0, 'get meetingvenue':0,'get meetingagenda':0,'get delmeeting':0,'get taskusername':0,'get taskdatedesc':0, 'get deltask':0} 
		bot.send_message(group_id,"""Welcome!
		The different functions for groups are as follows:
		/start: To capture all users again
		/majordates: Input major dates to take note of for this group
		/majordatesreminder: Return all your major dates
		/delmajordates: Remove records of a particular major date
		/sendcsvfiles: Send timetable csv files downloaded from BOSS
		/findcommontime: Calculate group's common time from timetable sent
		/setmeeting: Set a new meeting
		/meetingreminder: Returns all upcoming meetings
		/delmeeting: Remove records of a meeting with particular date
		/settask: Set new task for individual in a group
		/end: To end various commands""")
		multigroup[str(group_id)] = users_state
			
	else: #wrote this to just test for personal msging w bot.. actually no need de
		group_id = None
		chat_id = id
		telehandle = message.chat.username
		try:
			new_member = Member(chatID=chat_id, telehandle = telehandle) #the commontime shd be the calculator but i lazy craft now
			db.session.add(new_member)
			try: #the try except and finally appear a few times in this app.py. its for error handling purposes. see https://stackoverflow.com/questions/8870217/why-do-i-get-sqlalchemy-nested-rollback-error
				db.session.commit()
			except:
				db.session.rollback()
				raise
			finally:
				db.session.close()
			#bot.send_message(chat_id,'group_id is {}, chat_id is {}'.format(group_id,chat_id))
			bot.send_message(chat_id,"""Welcome!
		The different functions for individuals are as follows:
		/taskreminder: Returns all tasks due for an individual in a particular group
		/deltask: Delete task created for an individual in a group via private messaging the bot
		/end: To end various commands""")
			multippl[str(chat_id)] = user_state
		except:
			bot.send_message(chat_id,"""Welcome!
		The different functions for individuals are as follows:
		/taskreminder: Returns all tasks due for an individual in a particular group
		/deltask: Delete task created for an individual in a group via private messaging the bot
		/end: To end various commands""")
			multippl[str(chat_id)] = user_state
			pass


@bot.message_handler(commands=['majordates'])
def send_introduction(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		multigroup[str(group_id)] = users_state
		bot.send_message(group_id,'Please input a major date in the format dd/mm/yyyy')
		multigroup[str(group_id)]['get deadlines'] = 1 #waiting specific reply to /majordates

@bot.message_handler(commands=['majordatesreminder'])
def majordatesreminder(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		multigroup[str(group_id)] = users_state
		reminder = Maj_Dates.query.filter_by(groupid=str(group_id))
		majordatelist =[]
		majordesclist = []
		for r in reminder:
			#majordate = datetime.strptime(str(r.deadline.date()), "%Y-%m-%d").strftime('%d/%m/%Y')
			majordate = r.deadline.date()
			desc = r.major_desc
			majordatelist.append(str(majordate))
			majordesclist.append(desc)

		response = {}
		count=0
		for i in range (0,len(majordatelist)):
			count +=1
			response[str(count)] = [majordatelist[i],majordesclist[i]]
		count=0

		# ordered = OrderedDict(sorted(response.items(), key=lambda t: t[0]))
		ordered = OrderedDict(sorted(response.items(), key=lambda t:t[1][0]))
		#bot.send_message(group_id,str(ordered))
		#bot.send_message((group_id), ('Your major dates are the following:\n {}, {}'.format()
		
		if majordatelist == []:
			bot.send_message(group_id, 'No upcoming major date!')

		for k,v in ordered.items():
			newdate = datetime.strptime(v[0], "%Y-%m-%d").strftime('%d/%m/%Y')
			bot.send_message(group_id, 'Major date: {}, {}'.format(newdate,v[1]))
		
		#(majordate,majordesc) for majordate,majordesc in zip(majordatelist,majordesclist)))
		majordatelist.clear()
		majordesclist.clear()
		response.clear()
		
@bot.message_handler(commands=['delmajordates'])
def del_msg(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		multigroup[str(group_id)] = users_state
		bot.send_message(group_id,'Please input a major date that you no longer wish to keep track of in the format dd/mm/yyyy')
		multigroup[str(group_id)]['get deldate'] = 1
		
@bot.message_handler(commands=['end'])
def end(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		bot.send_message(group_id,'Thank you for all the inputs. Type /help to see the list of commands')
		multigroup[str(group_id)]["get desc"] = 0
		multigroup[str(group_id)]['get deadlines'] = 0
		multigroup[str(group_id)]['get deldate'] = 0
		multigroup[str(group_id)]['get meetingdate'] = 0
		multigroup[str(group_id)]['get meetingvenue'] = 0
		multigroup[str(group_id)]['get delmeeting'] = 0
		multigroup[str(group_id)]['get taskusername'] = 0
		multigroup[str(group_id)]['get taskdatedesc'] = 0
		multigroup[str(group_id)]['get files'] = 0
	if id > 0:
		chat_id = id	
		bot.send_message(chat_id,'Thank you for all the inputs. Type /help to see the list of commands')
		multippl[str(chat_id)]['get deltask'] = 0
		multippl[str(chat_id)]['get taskreminder'] = 0
		multippl[str(chat_id)]['get deltaskdate'] = 0
		savedgroupid.clear()

@bot.message_handler(commands=['setmeeting'])
def setmeeting(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		multigroup[str(group_id)] = users_state
		bot.send_message(group_id,'Please input the datetime of the meeting in the format dd/mm/yyyy hh:mm')
		multigroup[str(group_id)]['get meetingdate'] = 1 #waiting specific reply to /setmeeting

@bot.message_handler(commands=['meetingreminder'])
def meetingreminder(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		multigroup[str(group_id)] = users_state
		meetingreminder = Meeting.query.filter_by(groupid=str(group_id))
		datelist =[]
		venuelist = []
		agendalist = []

		for r in meetingreminder:
			meetingdate = r.meeting_datetime
			meetingvenue = r.venue
			meetingagenda = r.agenda
			datelist.append(str(meetingdate))
			venuelist.append(meetingvenue)
			agendalist.append(meetingagenda)
		# bot.send_message(group_id, datelist[0])
		response = {}
		count=0
		for i in range (0,len(datelist)):
			count +=1
			response[str(count)] = [datelist[i],venuelist[i], agendalist[i]]
		count=0

		# ordered = OrderedDict(sorted(response.items(), key=lambda t: t[0]))
		ordered = OrderedDict(sorted(response.items(), key=lambda t:t[1][0]))
		
		#bot.send_message(group_id,str(ordered))
		#bot.send_message((group_id), ('Your major dates are the following:\n {}, {}'.format()
		if datelist == []:
			bot.send_message(group_id, 'You do not have any upcoming meetings!')

		for k,v in ordered.items():
			newdatetime = datetime.strptime(v[0], "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y %H:%M:%S')
			bot.send_message(group_id, 'You have a meeting on {} at {} with the following agenda: {}'.format(newdatetime,v[1],v[2]))
		
		datelist.clear()
		venuelist.clear()
		agendalist.clear()
		response.clear()

		
		

@bot.message_handler(commands=['delmeeting'])
def delmeeting(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		multigroup[str(group_id)] = users_state
		bot.send_message(group_id,'Please input a meeting datetime that you no longer wish to keep track of in the format dd/mm/yyyy hh:mm')
		multigroup[str(group_id)]['get delmeeting'] = 1

@bot.message_handler(commands=['settask'])
def createtask(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		multigroup[str(group_id)] = users_state
		bot.send_message(group_id,'Please input a telegram username without the \'@\' (e.g. user) from this group to assign the task(s) to')
		multigroup[str(group_id)]['get taskusername'] = 1

# @bot.message_handler(commands=['tasksreminders'])
# def tasksreminders(message):
# 	id = message.chat.id #shd be negative number if grp
# 	if id < 0:
# 		group_id = id
# 		bot.send_message(group_id,'Please input a telegram username (eg Pekiee) the task(s) is for')
# 		multigroup[str(group_id)]['get taskusername'] = 1

@bot.message_handler(commands=['deltask'])
def deltask(message):
	id = message.chat.id #shd be +ve no cos only let ppl del thru pm
	if id > 0:
		chat_id = id
		multippl[str(chat_id)] = user_state
		groupsmemberbelongto.clear()
		groupsnamememberbelongto.clear()
		try:
			#chatid = Member.query.filter_by(chatID=chat_id).first()
			existing_group_member = MemberGroupTask.query.join(Member).join(Group).filter(Member.chatID == chat_id) #Group.query.join(Group.membergroup).filter_by(chatID = chatid).all()
			#chat_id = Member.query.filter_by(chatID=chat_id).first()#any dishes of rest -> any grp of indi
			#https://stackoverflow.com/questions/12593421/sqlalchemy-and-flask-how-to-query-many-to-many-relationship
			for e in existing_group_member:
				if e.group_id in groupsmemberbelongto:
					continue
				else:
					groupsmemberbelongto.append(e.group_id)
			
			for i in groupsmemberbelongto:
				groupname = Group.query.get(i).group_name
				groupsnamememberbelongto.append(groupname)

			markup = types.ReplyKeyboardMarkup(row_width=2)
			# markup = types.InlineKeyboardMarkup()
			for group in groupsnamememberbelongto:
				markup.add(types.InlineKeyboardButton(text=group))
			
			bot.send_message(chat_id, "Choose a group you want to delete your task from:", reply_markup=markup)
			multippl[str(id)]['get deltask'] = 1
			groupsmemberbelongto.clear()
			groupsnamememberbelongto.clear()

		except:
			bot.send_message(chat_id,'Did any of your groups you are in activate me inside?')

@bot.message_handler(commands=['taskreminder'])
def taskreminder(message):
	id = message.chat.id #shd be positive number if pm
	if id > 0:
		chat_id = id
		multippl[str(chat_id)] = user_state
		groupsmemberbelongto.clear()
		groupsnamememberbelongto.clear()
		try:
			existing_group_member = MemberGroupTask.query.join(Group).join(Member).filter(Member.chatID == chat_id)
			for e in existing_group_member:
				if e.group_id in groupsmemberbelongto:
					continue
				else:
					groupsmemberbelongto.append(e.group_id)

			for i in groupsmemberbelongto:
					groupname = Group.query.get(i).group_name
					groupsnamememberbelongto.append(groupname)

			markup = types.ReplyKeyboardMarkup(row_width=2)
			# markup = types.InlineKeyboardMarkup()
			for group in groupsnamememberbelongto:
				markup.add(types.InlineKeyboardButton(text=group))
			
			bot.send_message(chat_id, "Choose a group with tasks you need a reminder of:", reply_markup=markup)
			multippl[str(chat_id)]['get taskreminder'] = 1


		except:
			bot.send_message(chat_id,'Did any of your groups you are in activate me inside?')

@bot.message_handler(commands=['sendcsvfiles'])
def sendcsvfiles(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		group_name = message.chat.title
		multigroup[str(group_id)] = users_state
		bot.send_message(group_id,'Can all of you in {} send me your timetable csv files? Type /finecommontime when finished!'.format(group_name))
		multigroup[str(group_id)]['get files'] = 1
		filenamedict[str(group_id)] = []
		convert_to_binary_dict[str(group_id)] = []

@bot.message_handler(commands=['findcommontime'])
def findcommontime(message):
	group_id = message.chat.id
	try:
		group_commontime = Group.query.filter_by(groupid = str(group_id)).first().commontime
		mon = group_commontime[:56]
		tue = group_commontime[56:112]
		wed = group_commontime[112:168]
		thu = group_commontime[168:224]
		fri = group_commontime[224:]

		week = [(mon, 'mon'), (tue, 'tue'), (wed, 'wed'), (thu, 'thu'), (fri, 'fri')]

		final_output = []
		for day in week:
			current = compiler(day[0]) #current == [(16, '0'), (13, '1'), (1, '0'), (13, '1'), (13, '0')]
		#     print(day[1]) #day 
		#     print(binary_to_hour_v2(current)) #compiled timeslots in each day
			final_output.append((day[1], binary_to_hour_v2(current)))
		bot.send_message(group_id,'Your common times are as follows:\n'+ str(json.dumps(final_output, sort_keys=True, indent = 4)))
	except Exception as e:
		bot.send_message(group_id,str(e))
# @bot.message_handler(commands=['findcommontime'])
# def done(message):
# 	id = message.chat.id #shd be negative number if grp
# 	if id < 0:
# 		group_id = id
# 		activegroupid.append(group_id)
# 		bot.send_message(group_id,'Processing common time...')
# 		multigroup[str(group_id)]["get files"] = 0
		
# 		for k,v in filenamedict.items():
# 			if k == str(group_id):
# 				for filename in v:
# 					with open(r"{}".format(filename), 'r') as x:
# 						this_user_class_schedule = timetable_prep(x)
# 						timetable_filtering(this_user_class_schedule, group_one_schedule)
		
# 		show_avail_timeslots(group_one_schedule)		

@bot.message_handler(func=lambda message: True, content_types=['text'])
def allmessages(message):
	# if message.chat.type == 'private':
	# 	chat_id = message.chat.id
	# 	bot.send_message(chat_id,'are you working?')
	if message.chat.type == 'group' or message.chat.type == 'supergroup':
		group_id = message.chat.id
		if message.text == 'hello' or message.text == "\"hello\"":
			chat_id = message.from_user.id
			telehandle = message.from_user.username
			try:
				new_member = Member(chatID = chat_id, telehandle = telehandle)
				db.session.add(new_member)
				try: #the try except and finally appear a few times in this app.py. its for error handling purposes. see https://stackoverflow.com/questions/8870217/why-do-i-get-sqlalchemy-nested-rollback-error
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()
			except Exception as e:
				print(str(e))
			try:
				group_member = group_member_table.insert().values(group_id=str(group_id), chat_id=chat_id)
				db.session.execute(group_member)
				try: #the try except and finally appear a few times in this app.py. its for error handling purposes. see https://stackoverflow.com/questions/8870217/why-do-i-get-sqlalchemy-nested-rollback-error
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()
				# member = Member.query.get(chat_id)
				# memberlist.append(member)
				# group = Group.query.get(str(group_id))
				# group.membergroup = memberlist
				# bot.send_message(group_id,'are you working')
			except Exception as e:
				print(e)
			

		if multigroup[str(group_id)]["get deadlines"] == 1: #if the text is specifically right after /majordates refer to line 90
			text = message.text
			try:
				majordate = datetime.strptime(text, "%d/%m/%Y")
				majordatelist.append(majordate)
				bot.send_message(group_id,'Please describe what is due by this date')
				multigroup[str(group_id)]["get desc"] = 1 #waiting specific reply to above message
				multigroup[str(group_id)]["get deadlines"] = 0 #no longer waiting for /majordates so 0 since it's alr over
			except:
				bot.send_message(group_id, 'Please try again with valid date and time in format dd/mm/yyyy')
				multigroup[str(group_id)]["get deadlines"] = 1 #still waiting for valid repsonse to /majordate
		
		elif multigroup[str(group_id)]["get desc"] == 1:
			desc = message.text
			majordate = majordatelist[0]
			new_majordate = Maj_Dates(groupid=str(group_id), major_desc = desc, deadline = majordate)
			db.session.add(new_majordate)
			try:
				db.session.commit()
			except:
				db.session.rollback()
				raise
			finally:
				db.session.close()
			majordatelist.clear()
			bot.send_message(group_id, 'Please input another date and time in format dd/mm/yyyy or type /end to end majordates')
			multigroup[str(group_id)]['get desc'] = 0
			multigroup[str(group_id)]['get deadlines'] = 1

		elif multigroup[str(group_id)]["get deldate"] == 1:
			text = message.text
			try:
				del_majordate = datetime.strptime(text, "%d/%m/%Y")
				majordatedeleted = Maj_Dates.query.filter_by(groupid = str(group_id), deadline=del_majordate).delete()
				try:
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()
				bot.send_message(group_id,'All records for this major date are deleted successfully~ Please input another date in format dd/mm/yy to delete or type /end to end deldate')
				multigroup[str(group_id)]["get deldate"] = 1
			except:
				bot.send_message(group_id, 'Please try again with valid date and time in format dd/mm/yyyy')
				multigroup[str(group_id)]["get deldate"] = 1

		elif multigroup[str(group_id)]["get meetingdate"] == 1: #if the text is specifically right after /majordates refer to line 90
			text = message.text
			try:
				meetingdate = datetime.strptime(text, "%d/%m/%Y %H:%M")
				meetingdatelist.append(meetingdate)
				bot.send_message(group_id,'Please tell me the venue of your meeting')
				multigroup[str(group_id)]["get meetingvenue"] = 1 #waiting specific reply to above message
				multigroup[str(group_id)]["get meetingdate"] = 0 #no longer waiting for /setmeeting so 0 since it's alr over
			except:
				bot.send_message(group_id, 'Please try again with valid datetime in format dd/mm/yyyy hh:mm')
				multigroup[str(group_id)]["get meetingdate"] = 1 #still waiting for valid repsonse to /setmeeting
		
		elif multigroup[str(group_id)]["get meetingvenue"] == 1:
			meetingvenue = message.text
			meetingvenuelist.append(meetingvenue)
			bot.send_message(group_id,'Please tell me the agenda of your meeting')
			multigroup[str(group_id)]["get meetingagenda"] = 1 #waiting specific reply to above message
			multigroup[str(group_id)]["get meetingvenue"] = 0
			
		elif multigroup[str(group_id)]["get meetingagenda"] == 1:
			meetingagenda = message.text
			meetingdate = meetingdatelist[0]
			meetingvenue = meetingvenuelist[0]
			new_meeting = Meeting(groupid=str(group_id), venue = meetingvenue, meeting_datetime = meetingdate, agenda = meetingagenda)
			db.session.add(new_meeting)
			try:
				db.session.commit()
			except:
				db.session.rollback()
				raise
			finally:
				db.session.close()
			meetingdatelist.clear()
			meetingvenuelist.clear()
			bot.send_message(group_id, 'Please input the datetime of another meeting in the format dd/mm/yyyy hh:mm or type /end to end this command')
			multigroup[str(group_id)]['get meetingdate'] = 1
			multigroup[str(group_id)]['get meetingagenda'] = 0
		
		elif multigroup[str(group_id)]["get delmeeting"] == 1:
			text = message.text
			try:
				del_meeting = datetime.strptime(text, "%d/%m/%Y %H:%M")
				meetingdeleted = Meeting.query.filter_by(groupid = str(group_id), meeting_datetime=del_meeting).delete()
				try:
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()
				bot.send_message(group_id,'All records for this date are deleted successfully~ Please input another date in format dd/mm/yyyy to delete or type /end to end delmeeting')
				multigroup[str(group_id)]["get delmeeting"] = 1
			except:
				bot.send_message(group_id, 'Please try again with valid datetime in format dd/mm/yyyy hh:mm')
				multigroup[str(group_id)]["get delmeeting"] = 1

		elif multigroup[str(group_id)]["get taskusername"] == 1:
			text = message.text
			try:
				chat_id = Member.query.filter_by(telehandle=text).first().chatID
				existing_group_member = Group.query.join(Group.membergroup).filter_by(chatID = chat_id)
				telehandlelist.append(text)
				chat_idlist.append(chat_id)
				bot.send_message(group_id, 'Please input all the deadlines and tasks due by each deadline for {}!~\n'.format(telehandlelist[0])
				+ 'If he/she only has one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\'}\n' +
				'If he/she only has more than one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\', \'dd/mm/yyyy\': \'task2\', \'dd/mm/yyyy\': \'task3\'}')
				multigroup[str(group_id)]["get taskdatedesc"] = 1
				multigroup[str(group_id)]["get taskusername"] = 0
			except:
				bot.send_message(group_id, 'This user is not in your group! Please try to create the task again for telegram username in this group!')
				multigroup[str(group_id)]["get taskusername"] = 1

		elif multigroup[str(group_id)]["get taskdatedesc"] == 1:
			text = message.text
			try:
				taskdict = eval(text)
				count = 0
				for k,v in taskdict.items():
					count += 1
					try:
						taskdate = datetime.strptime(k, "%d/%m/%Y")
						# bot.send_message('iwork')
					except:
						bot.send_message(group_id, 'An invalid date was found!\nPlease input all the deadlines and tasks due by each deadline for {}!~\n'.format(telehandlelist[0])
					+ 'If he/she only has one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\'}\n' +
					'If he/she only has more than one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\', \'dd/mm/yyyy\': \'task2\', \'dd/mm/yyyy\': \'task3\'}')	
						multigroup[str(group_id)]["get taskdatedesc"] = 1
						

					if v is None:
						bot.send_message(group_id, 'An empty task was found!\nPlease input all the deadlines and tasks due by each deadline for {}!~\n'.format(telehandlelist[0])
				+ 'If he/she only has one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\'}\n' +
				'If he/she only has more than one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\', \'dd/mm/yyyy\': \'task2\', \'dd/mm/yyyy\': \'task3\'}')	
						multigroup[str(group_id)]["get taskdatedesc"] = 1
					
					else:
						taskdesc = str(v)

					chat_id = chat_idlist[0]
					new_task = MemberGroupTask(group_id=str(group_id), chat_id = chat_id, desc = taskdesc, deadline = taskdate)
					commitlist.append(new_task) #somehow cannot repeat dates eg{'8/4/2020':'1', '7/4/2020':'2','7/4/2020':'3'} only last output appears
					
				db.session.add_all(commitlist)

				try:
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()
				
				bot.send_message(group_id,'Added tasks for {}.\n'.format(telehandlelist[0])+'Please input another telegram username without the \'@\' (e.g. user) from this group to assign the task(s) to or type /end to end this command')
				telehandlelist.clear()
				commitlist.clear()
				chat_idlist.clear()
				multigroup[str(group_id)]["get taskdatedesc"] = 0
				multigroup[str(group_id)]["get taskusername"] = 1

			except Exception as e:
				bot.send_message(group_id, 'Please try again in the proper format!\nPlease input all the deadlines and tasks due by each deadline for {}!~\n'.format(telehandlelist[0])
				+ 'If he/she only has one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\'}\n' +
				'If he/she only has more than one deadline, please input the deadline in this format {\'dd/mm/yyyy\': \'task1\', \'dd/mm/yyyy\': \'task2\', \'dd/mm/yyyy\': \'task3\'}')	
				multigroup[str(group_id)]["get taskdatedesc"] = 1
			
	if message.chat.type == 'private':	
		chat_id = message.chat.id
		if multippl[str(chat_id)]["get deltask"] == 1:
			text = message.text
			groupname = text
			try:
				findgroupid = Group.query.filter_by(group_name=groupname).first().groupid
				existing_group_member = MemberGroupTask.query.join(Member).join(Group).filter(Member.chatID == chat_id,Group.groupid==str(findgroupid))
				savedgroupid.append(str(existing_group_member.first().group_id))
				savedgroupid.append(groupname)
				bot.send_message(chat_id, 'Please input a deadline of a task you no longer wish to keep track of for {} in the format dd/mm/yyyy'.format(groupname))
				multippl[str(chat_id)]["get deltask"] = 0
				multippl[str(chat_id)]["get deltaskdate"] = 1
			except:
				bot.send_message(chat_id, 'No records of you in this group. Please input a group you want to delete your task from')
				multippl[str(chat_id)]["get deltask"] = 1
				
		elif multippl[str(chat_id)]["get deltaskdate"] == 1:
			text = message.text		
			try:
				del_task = datetime.strptime(text, "%d/%m/%Y")
			except:
				bot.send_message(chat_id,'Date is in wrong format. Please input the deadline again in dd/mm/yyyy')
				multippl[str(chat_id)]["get deltaskdate"] = 1
			
			try:
				taskdeleted = MemberGroupTask.query.filter_by(group_id = savedgroupid[0], chat_id = chat_id, deadline=del_task).delete()
				try:
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()
				
				bot.send_message(chat_id,'All records for {} are deleted successfully~ Please input another date in format dd/mm/yyyy to delete another task deadline for {} or type /end to end this command'.format(text,savedgroupid[1]))
				savedgroupid.clear()
				multippl[str(chat_id)]["get deltaskdate"] = 1
			except:
				bot.send_message(chat_id,'Task deadline does not exist for you in this group. Please input another task deadline again in dd/mm/yyyy')
				multippl[str(chat_id)]["get deltaskdate"] = 1

		elif multippl[str(chat_id)]["get taskreminder"] == 1:	
			text = message.text
			groupname = text
			try:
				findgroupid = Group.query.filter_by(group_name=groupname).first().groupid
				existing_group_member = MemberGroupTask.query.join(Member).join(Group).filter(Member.chatID == chat_id,Group.groupid==str(findgroupid))
				savedgroupid.append(str(existing_group_member.first().group_id))
				savedgroupid.append(groupname)
				taskreminder = MemberGroupTask.query.filter_by(group_id = findgroupid,chat_id = chat_id)
				taskdatelist = []
				desclist = []

				for r in taskreminder:
					taskdate = r.deadline.date()
					taskdesc = r.desc
					taskdatelist.append(str(taskdate))
					desclist.append(taskdesc)
				
				response = {}
				count = 0
				for i in range (0,len(taskdatelist)):
					count+=1
					response[str(count)] = [taskdatelist[i],desclist[i]]
				count = 0

				ordered = OrderedDict(sorted(response.items(), key=lambda t: t[1][0]))

				if taskdatelist == []:
					bot.send_message(chat_id,'You do not have any upcoming tasks for {}!'.format(groupname))
				
				for k,v in ordered.items():
					newdate = datetime.strptime(v[0], "%Y-%m-%d").strftime('%d/%m/%Y')
					bot.send_message(chat_id, 'You have {} due on {} for {}'.format(v[1],newdate,groupname))
		
				#(majordate,majordesc) for majordate,majordesc in zip(majordatelist,majordesclist)))
				taskdatelist.clear()
				desclist.clear()
				response.clear()
				savedgroupid.clear()

				bot.send_message(chat_id, 'Type /taskreminder to be reminded of your tasks from another group or /end to end this command')
				multippl[str(chat_id)]["get taskreminder"] = 0

		
		#bot.send_message(group_id,str(ordered))
		#bot.send_message((group_id), ('Your major dates are the following:\n {}, {}'.format()



			except:
				bot.send_message(chat_id, 'No records of you in this group. Type /taskreminder to be reminded of your tasks from another group or /end to end this command')
				multippl[str(chat_id)]["get taskreminder"] = 0

def downloader(filenames,urls): #DONE
	filename=""
	while filename != "QUIT":
		try:
			filename=filenames.pop(0)
			url = urls.pop(0)
		except IndexError:
			time.sleep(5)
	   
		if filename and filename != "QUIT":
			print("Downloading:"+filename+ ' from '+ url)
			r = requests.get(url,stream=True)
			with open(os.path.abspath("{}".format(filename)), 'wb') as f: #os.path.abspath("mydir/myfile.txt")
				for chunk in r.iter_content(chunk_size=1024): 
					if chunk: 
						f.write(chunk)
			print("Download completed")
			
			with open(r"{}".format(filename), 'r') as x:
				chat_id = activechatid[0]
				this_user_class_schedule = timetable_prep(x)
				this_user_binary = convert_to_binary(this_user_class_schedule)
				convert_to_binary_dict[str(activegroupid[0])].append(this_user_binary)
				
				user = Member.query.get(chat_id)			
				user.freetime = this_user_binary
				try:
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()

				del_timetable = Timetable.query.filter_by(chat_id = chat_id).delete()
				try:
					db.session.commit()
				except:
					db.session.rollback()
					raise
				finally:
					db.session.close()

				try:
					for c in this_user_class_schedule:
						new_timetable = Timetable(chat_id = chat_id, class_code = c[3], day = c[0], start_time = c[1], end_time = c[2])
						db.session.add(new_timetable)
						try:
							db.session.commit()
						except:
							db.session.rollback()
							raise
						finally:
							db.session.close()

				except Exception as e:
					pass

			groupsin = Group.query.join(Group.membergroup).filter(Member.chatID == activechatid[0]).all()
			user = Member.query.get(chat_id)
			
			for group in groupsin:
				db.session.expunge_all()
				group_id = group.groupid	
				groupcommontime = Group.query.filter_by(groupid = str(group_id)).first().commontime
				if groupcommontime == None:
					bot.send_message(group_id,'here')
					finalgroup = Group.query.get(str(group_id))
					finalgroup.commontime = this_user_binary
					try:
						db.session.commit()
					except:
						db.session.rollback()
						raise
					finally:
						db.session.close()
				else:
					newcommontime = ''
					y = (user.freetime).split()
					z = (groupcommontime).split()
					for i in range(len(y)):
						summation = int(y[i]) + int(z[i])
						newcommontime += str(summation)

					groupcommontime = newcommontime
					try:
						db.session.commit()
					except:
						db.session.rollback()
						raise
					finally:
						db.session.close()
					
					newestcommontime = ''
					a = (groupcommontime).split()
					for i in range(len(y)):
						summation = int(a[i]) + int(this_user_binary[i])
						newestcommontime += str(summation)
					groupcommontime = newestcommontime
					try:
						db.session.commit()
					except:
						db.session.rollback()
						raise
					finally:
						db.session.close()

					
			user.freetime = this_user_binary
			try:
				db.session.commit()
			except:
				db.session.rollback()
				raise
			finally:
				db.session.close()


			bot.send_message(activegroupid[0],'Downloaded completed!')
			# bot.send_message(activegroupid[0],str(convert_to_binary_dict))
			multigroup[str(activegroupid[0])]['get files'] = 0
			activechatid.pop(0)
			activegroupid.pop(0)
			filename=""
		

def convert_to_binary(gotclass):
	freetime = ''
	for i in range(280):
		freetime += '0'
		
	for thisclass in gotclass:
		
		#Find the DAY of class
		if thisclass[0] == 'Mon':
			placement = 0
		elif thisclass[0] == 'Tue':
			placement = 56
		elif thisclass[0] == 'Wed':
			placement = 112
		elif thisclass[0] == 'Thu':
			placement = 168
		else:
			placement = 224
			
		#Starting Hour
		starting_placement = placement + ((int(thisclass[1][:2]) - 8) * 4) 
		
		#Starting Minute
		starting_min = int(thisclass[1][2:])
		if starting_min == 45:
			starting_placement += 3
		elif starting_min == 30:
			starting_placement += 2
		elif starting_min == 15:
			starting_placement += 1
	
	
		#Ending Hour
		ending_placement = placement + ((int(thisclass[2][:2]) - 8) * 4)
		
		#Ending Minute
		ending_min = int(thisclass[2][2:])
		if ending_min == 45:
			ending_placement += 3
		elif ending_min == 30:
			ending_placement += 2
		elif ending_min == 15:
			ending_placement += 1
			
		freetime = freetime[:starting_placement] + '1'*(ending_placement-starting_placement) + freetime[ending_placement:]
		
	return freetime

def timetable_prep(x): #converts a csv file into a list of users' classes eg: [('Mon', '1200', '1515', 'SMT202'), ('Wed', '815', '1130', 'DSA211')]
	x.readline()
	gotclass = []
	for i in x:
		x = i.replace('"',"").replace(':','')
		row = list(x.split(','))
		if row[6] == 'Enrolled' and row[7] == 'CLASS':
			gotclass.append((row[10], row[11], row[12], row[3]))
	return(gotclass)

def compiler(day):
	compiled = []
	counter = 0
	for i in range(56):
		if i == 0:
			pass    
		if day[i] == day[i-1]:
			counter += 1
		else:
			compiled.append((counter, day[i-1]))
			counter = 1
	compiled.append((counter, day[-1]))   #add the last block
	return compiled

def binary_to_hour_v2(day):
    hour_by_hour = [(1,'8'), (5,'9'), (9,'10'), (13,'11'), (17,'12'), (21,'13'), (25,'14'), 
             (29,'15'), (33,'16'), (37,'17'), (41,'18'), (45,'19'), (49,'20'), (53,'21')]

    prev_time = '800'
    prev_place = 1
    result = []
    for segment in range(len(day)): #segment == (16, '0')
        
        if day[segment][0] == 56:
            output = ('800-2200', day[segment][1])
            result.append(output)
            continue
        
                
        x = day[segment][0] + prev_place #x = 17,
        for i in range(len(hour_by_hour)):
            
            #For cases where timing falls in last block
            if x >52:
                if x == 53:
                    time = '2100'
                elif x == 54:
                    time = '2115'
                elif x == 55:
                    time = '2130'
                elif x == 56:
                    time = '2145'
                elif x == 57:
                    time = '2200'

            #For all other cases
            elif (x >= hour_by_hour[i][0]) and (x < hour_by_hour[i+1][0]):

                #settle the hour
                time = hour_by_hour[i][1]

                #settle the minute
                if x == hour_by_hour[i][0]:
                    time += '00'
                elif x-1 == hour_by_hour[i][0]:
                    time += '15'
                elif x-2 == hour_by_hour[i][0]:
                    time += '30'
                else:
                    time += '45'
            
        output = ((prev_time + '-' + time), day[segment][1])
        prev_time = time
        prev_place = x
        
        result.append(output)

    return dict(result)
# def show_avail_timeslots(group_schedule):
# 	for i in group_schedule:
# 		printcommontime.append(str(i+'\n'))
# 		for timeslot in group_schedule[i]:
# 			if timeslot != [0,0]:
# 				printcommontime.append(str(timeslot[0]) + ' - ' + str(timeslot[1]) + '\n')
	
# 	bot.send_message(activegroupid[0], 'Your free time slots are as follows:\n'+''.join(printcommontime))
# 	filenamedict[str(activegroupid[0])] = []
# 	activegroupid.clear()
# 	printcommontime.clear()



@bot.message_handler(content_types=['document'])	
def files(message):
	if message.chat.type == 'group' or message.chat.type == 'supergroup':
		group_id = message.chat.id
		if multigroup[str(group_id)]['get files'] == 1:
			chat_id = message.from_user.id
			activechatid.append(chat_id)
			activegroupid.append(group_id)
			manager = Manager()
			filenames = manager.list()
			urls = manager.list()
			download_process = Process(target=downloader, args=(filenames,urls,))
			download_process.daemon = True
			download_process.start()
			try:
				newfile=message.document
				bot.send_message(group_id,"Downloading file %s (%i bytes)" %(newfile.file_name, newfile.file_size))
				tfile=bot.get_file(newfile.file_id)
				filenames.append(newfile.file_name)
				filenamedict[str(group_id)].append(newfile.file_name)        
				#urls.append(tfile.file_path)
				urls.append('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, tfile.file_path))
			except AttributeError:
				pass
			
			#bot.send_message(group_id,str(filenamedict))

			# countgroupmembers = group_member_table.query.filter(group_member_table.group_id == str(group_id)).count()
			
			# if len(filenamedict[str(group_id)]) != countgroupmembers:
			# 	bot.send_message(group_id,'Waiting for all members to send me their timetable csv files')
			# 	multigroup[str(group_id)]['get files'] = 1
			# else:
			# 	for k,v in filenamedict.items():
			# 		if k == str(group_id):
			# 			for filename in v:
			# 				with open(r"{}".format(filename), 'r') as x:
			# 					this_user_class_schedule = timetable_prep(x)
			# 					timetable_filtering(this_user_class_schedule, group_one_schedule)	
				
			# 	bot.send_message(group_id, 'Your free time slots are as follows:\n'+show_avail_timeslots(group_one_schedule))

def check_dates():
	#result = SomeModel.query.with_entities(SomeModel.col1, SomeModel.col2)
	due_date = (datetime.today() + timedelta(days=2)).date() 
	rows_with_reminder_majordates = Maj_Dates.query.filter_by(deadline=due_date)
	rows_with_reminder_meeting = Meeting.query.filter(cast(Meeting.meeting_datetime, DATE)==due_date).all() #https://gist.github.com/danielthiel/8374607
	rows_with_reminder_task = MemberGroupTask.query.filter_by(deadline=due_date)
	#filter(func.DATE(db.Transaction.datetime) == date.today())
	due_date_format = datetime.strptime(str(due_date), "%Y-%m-%d").strftime('%d/%m/%Y') #convert 2020-04-02 to 02/04/2020
	
	for row in rows_with_reminder_majordates:
		group_id = row.groupid
		desc =  row.major_desc
		bot.send_message(group_id, desc +' is due in 2 days on {}!'.format(due_date_format))
	
	for row in rows_with_reminder_meeting:
		group_id = row.groupid
		meetingdatetime = row.meeting_datetime
		meetingvenue = row.venue
		meetingagenda = row.agenda
		formatteddatetime = datetime.strptime(str(meetingdatetime), "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y %H:%S')
		bot.send_message(group_id, 'A meeting on {} at {} for {} is coming up in 2 days!'.format(formatteddatetime,meetingvenue,meetingagenda))

	for row in rows_with_reminder_task:
		group_id = row.group_id
		findgroupname = Group.query.filter_by(groupid=group_id).first().group_name
		chat_id =  row.chat_id
		desc = row.desc
		bot.send_message(chat_id, desc +' is due in 2 days on {} for group {}!'.format(due_date_format,str(findgroupname)))

sched = BackgroundScheduler(daemon=True)
sched.add_job(check_dates,trigger='cron', hour='12', minute='15')
sched.add_job(check_dates,trigger='cron', hour='12', minute='20') #flask scheduler to check if need to remind anyone everyday at 10pm
sched.start()

# @bot.message_handler(func=lambda msg: msg.text is not None and '@' in msg.text)
# def at_answer(message):
# 	texts = message.text.split()
# 	at_text = find_at(texts)
# 	bot.reply_to(message,'https://instagram.com/{}'.format(at_text[1:]))


# while True:
# 	try:
# 		bot.polling()
# 	except:
# 		time.sleep(15)

# @bot.message_handler(commands=['start'])
# def start(message):
#     bot.reply_to(message, 'Hello, ' + message.from_user.first_name)

# @bot.message_handler(func=lambda message: True, content_types=['text'])
# def reply(message):
# 	if '@' in message.text:
# 		texts = message.text.split()
# 		at_text = find_at(texts)
# 		bot.reply_to(message,'https://instagram.com/{}'.format(at_text[1:]))
# 	else:
# 		bot.reply_to(message, message.text) #echo

# @server.route('/', methods=['POST'])
# def getMessage():
# 	bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
# 	msg = request.get_json()
# 	write_json(msg,'trytelebot.json')
# 	return "!", 200


@app.route("/")
def webhook():
	bot.remove_webhook()
	bot.set_webhook(url='https://1b952c20.ngrok.io') #https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/webhook_examples/webhook_flask_heroku_echo.py
	return "!", 200 #change url linked to local host. can be heroku also but i have issues w heroku so I used ngrok instead.

if __name__ == "__main__":
	app.run(debug = True, use_reholder = False,host="0.0.0.0", port=int(os.environ.get('PORT', 5000))) #use_reholder is to make sure flask dont initialise twice https://stackoverflow.com/questions/9449101/how-to-stop-flask-from-initialising-twice-in-debug-mode
	# sched.start()
	# sched.add_job(enable_interval, 'cron', minute='0', hour='16')
#https://www.youtube.com/watch?v=jhFsFZXZbu4
#https://pypi.org/project/pyTelegramBotAPI/
