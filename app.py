import telebot
import schedule
import time
import requests 
import request #must alw import this first before the from flask import request LOL
from flask import Flask, request, Response, jsonify
import os
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from collections import OrderedDict 
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = ''
bot = telebot.TeleBot(token=TOKEN)

#knownUsers = [] #https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/detailed_example/detailed_example.py
majordatelist = []
meetingdatelist = []
commands = {  # command description used in the "help" command
	'start'       : 'Initialize the bot',
	'help'        : 'Gives you information about the available commands',
	'majordates'  : 'Important dates to take note for particular module',
	'majordatesreminder'    : 'Returns a list of all important dates and what so important about it',
	'delmajordates': 'deletes existing record with particular date',
	'end'         : 'to end majordate'
} #just for reference sake
users_state = {'get deadlines': 0, 'get desc': 0, 'get deldate': 0, 'get meetingdate':0, 'get meetingvenue':0} 

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
from models import Member, Timetable, Group, Maj_Dates, Meeting

@app.route('/', methods = ['POST']) # binds URL to view function
def index():
	if request.headers.get('content-type') == 'application/json':
		json_string = request.get_json()
		write_json(json_string, 'telebot.json')
		update = telebot.types.Update.de_json(json_string)
		bot.process_new_updates([update])
		return "!",200 #refer to https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/webhook_examples/webhook_flask_echo_bot.py

@bot.message_handler(commands=['start'])
def send_welcome(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		chat_id = message.from_user.id
		try:
			new_group = Group(groupid=str(group_id), commontime = str(group_id*2)) #the commontime shd be the calculator but i lazy craft now
			db.session.add(new_group)
			try: #the try except and finally appear a few times in this app.py. its for error handling purposes. see https://stackoverflow.com/questions/8870217/why-do-i-get-sqlalchemy-nested-rollback-error
				db.session.commit()
			except:
				db.session.rollback()
				raise
			finally:
				db.session.close()
			bot.send_message(group_id,'Welcome! \nThe different functions are as follows:\n/majordates: Input any major dates to take note of for the whole group~ \n/majordatesreminder: Return all your major dates\n/delmajordates: Remove records of a particular major date')
		except:
			bot.send_message(group_id,'Welcome again! \nThe different functions are as follows:\n/majordates: Input any major dates to take note of for the whole group~ \n/majordatesreminder: Return all your major dates\n/delmajordates: Remove records of a particular major date')
			
	else: #wrote this to just test for personal msging w bot.. actually no need de
		group_id = None
		chat_id = id
		bot.send_message(chat_id,'group_id is {}, chat_id is {}'.format(group_id,chat_id))

@bot.message_handler(commands=['majordates'])
def send_introduction(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		bot.send_message(group_id,'Please input a date and time in the format dd/mm/yyyy')
		users_state['get deadlines'] = 1 #waiting specific reply to /majordates

@bot.message_handler(commands=['majordatesreminder'])
def majordatesreminder(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
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
		for i in range (0,len(majordatelist)):
			response[majordatelist[i]] = majordesclist[i]

		ordered = OrderedDict(sorted(response.items(), key=lambda t: t[0]))

		#bot.send_message(group_id,str(ordered))
		#bot.send_message((group_id), ('Your major dates are the following:\n {}, {}'.format()
		for k,v in ordered.items():
			newk = datetime.strptime(k, "%Y-%m-%d").strftime('%d/%m/%Y')
			bot.send_message(group_id, '{}, {}'.format(newk,v))
		
		#(majordate,majordesc) for majordate,majordesc in zip(majordatelist,majordesclist)))
		majordatelist.clear()
		majordesclist.clear()
		response.clear()
		
@bot.message_handler(commands=['delmajordates'])
def del_msg(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		bot.send_message(group_id,'Please input a date that you no longer wish to keep track of')
		users_state['get deldate'] = 1
		

@bot.message_handler(commands=['end'])
def end(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		bot.send_message(group_id,'Thank you for all the inputs')
		users_state['get desc'] = 0
		users_state['get deadlines'] = 0
		users_state['get deldate'] = 0

@bot.message_handler(commands=['setmeeting'])
def setmeeting(message):
	id = message.chat.id #shd be negative number if grp
	if id < 0:
		group_id = id
		bot.send_message(group_id,'Please input the datetime of the meeting in the format dd/mm/yyyy hh:mm')
		users_state['get meetingdate'] = 1 #waiting specific reply to /setmeeting

@bot.message_handler(func=lambda message: True, content_types=['text'])
def msg_deadlines(message):
	# if message.chat.type == 'private':
	# 	chat_id = message.chat.id
	# 	bot.send_message(chat_id,'are you working?')
	if message.chat.type == 'group' or message.chat.type == 'supergroup':
		if users_state["get deadlines"] == 1: #if the text is specifically right after /majordates refer to line 90
			group_id = message.chat.id
			text = message.text
			try:
				majordate = datetime.strptime(text, "%d/%m/%Y")
				majordatelist.append(majordate)
				bot.send_message(group_id,'Please describe what is due by this date')
				users_state["get desc"] = 1 #waiting specific reply to above message
				users_state["get deadlines"] = 0 #no longer waiting for /majordates so 0 since it's alr over
			except:
				bot.send_message(group_id, 'Please try again with valid date and time in format dd/mm/yy')
				users_state["get deadlines"] = 1 #still waiting for valid repsonse to /majordate
		
		elif users_state["get desc"] == 1 and users_state["get deadlines"] == 0:
			group_id = message.chat.id
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
			bot.send_message(group_id, 'Please input another date and time in format dd/mm/yy or type /end to end majordates')
			users_state['get desc'] = 0
			users_state['get deadlines'] = 1

		elif users_state["get deldate"] == 1:
			group_id = message.chat.id
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
				bot.send_message(group_id,'All records for this date are deleted successfully~ Please input another date in format dd/mm/yy to delete or type /end to end deldate')
				users_state["get deldate"] = 1
			except:
				bot.send_message(group_id, 'Please try again with valid date and time in format dd/mm/yyyy')
				users_state["get deldate"] = 1

		elif users_state["get meetingdate"] == 1: #if the text is specifically right after /majordates refer to line 90
			group_id = message.chat.id
			text = message.text
			try:
				meetingdate = datetime.strptime(text, "%d/%m/%Y %H:%M")
				majordatelist.append(meetingdatelist)
				bot.send_message(group_id,'Where will your meeting be held?')
				users_state["get meetingvenue"] = 1 #waiting specific reply to above message
				users_state["get meetingdate"] = 0 #no longer waiting for /setmeeting so 0 since it's alr over
			except:
				bot.send_message(group_id, 'Please try again with valid datetime in format dd/mm/yyyy hh:mm')
				users_state["get meetingdate"] = 1 #still waiting for valid repsonse to /setmeeting

			

def check_dates():
	#result = SomeModel.query.with_entities(SomeModel.col1, SomeModel.col2)
	due_date = (datetime.today() + timedelta(days=3)).date() 
	rows_with_reminder = Maj_Dates.query.filter_by(deadline=due_date)
	due_date_format = datetime.strptime(str(due_date), "%Y-%m-%d").strftime('%d/%m/%Y') #convert 2020-04-02 to 02/04/2020
	
	for row in rows_with_reminder:
		group_id = row.groupid
		desc =  row.major_desc
		bot.send_message(group_id, desc +' is due in 3 days on {}!'.format(due_date_format))

sched = BackgroundScheduler(daemon=True)
sched.add_job(check_dates,trigger='cron', hour='22', minute='00') #flask scheduler to check if need to remind anyone everyday at 10pm
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
	bot.set_webhook(url='https://200e76f5.ngrok.io') #https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/webhook_examples/webhook_flask_heroku_echo.py
	return "!", 200 #change url linked to local host. can be heroku also but i have issues w heroku so I used ngrok instead.

if __name__ == "__main__":
	app.run(debug = True, use_reholder = False,host="0.0.0.0", port=int(os.environ.get('PORT', 5000))) #use_reholder is to make sure flask dont initialise twice https://stackoverflow.com/questions/9449101/how-to-stop-flask-from-initialising-twice-in-debug-mode

#https://www.youtube.com/watch?v=jhFsFZXZbu4
#https://pypi.org/project/pyTelegramBotAPI/
