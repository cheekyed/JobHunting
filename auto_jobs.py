from __future__ import print_function
from bs4 import BeautifulSoup
from robobrowser import RoboBrowser
import socket 
import os
import sys 
import datetime 
import pickle
import time 
import sqlite3
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

browser  = RoboBrowser(parser='html.parser')
pageCounter = 1 
careersUrl= 'https://careersonline.unsw.edu.au/students/jobs/Bookmarks?page='
jobInfo = []

def internet_on():
	try:
		socket.create_connection(("www.google.com", 80))
		print('internet connection is on')
	except OSError:
		print('no internet connection')
		sys.exit()
	return

def login(): 
	browser.open(careersUrl+str(pageCounter))
	form = browser.get_form(action = '/providers/ldap/login/1?returnURL=%2Fstudents%2Fjobs%2FBookmarks%3Fpage%3D1')
	form['LDAPUsername'].value = sys.argv[1]
	form['LDAPPassword'].value = sys.argv[2]
	browser.submit_form(form)
	print( "successfully login to UNSW careers")
	return

def num_pages():
	pageList = browser.find('ul',attrs={'class' : 'pagination'})
	if pageList == None:
		return 1
	else:
		listItems = pageList.find_all('li')
		print('total number of bookmarked pages = ' + str(len(listItems)-1))
		return len(listItems) -1 


def getJobData(inputPages):
	global pageCounter
	while pageCounter <= inputPages:
		print('\n')
		browser.open(careersUrl+str(pageCounter))
		print('Scraping from page ' + str(pageCounter))
		jobList = browser.find('div', attrs={'class' : 'list-group job-list'})
		jobItems= jobList.find_all('div', attrs={'class' : 'list-group-item'})
		for job in jobItems:
			jobAttributes = []
			dateHtml = job.find('div', attrs={'class' : 'job-list-close'})
			date = dateHtml.text.strip().split(' - ')[1].replace(',','')
			formattedDateObject = datetime.datetime.strptime(date, '%d %b %Y').date()
			formattedDateString = formattedDateObject.strftime('%Y-%m-%d')
			jobHeading = job.find('div', attrs={'class' : 'col-sm-8 list-group-item-heading'})
			jobRole = jobHeading.find('h4').text.strip()
			company = jobHeading.find('h5').text.strip()
			jobAttributes.append(formattedDateString)
			jobAttributes.append(company)
			if 'new' in jobRole:
				jobAttributes.append(jobRole.replace('(new)','').replace('\n','').replace('\r','').strip())
			else:	
				jobAttributes.append(jobRole)
			jobInfo.append(jobAttributes)
		pageCounter+=1
	print('\n')
	print(jobInfo)
	return
 
def setup_db():
	try:
		conn = sqlite3.connect("jobCalender.db")
	except:
		sys.exit()
		print("cannot connect to the database")
	cursor = conn.cursor()
	#cursor.execute("Drop table CALENDER;")
	cursor.execute("CREATE TABLE IF NOT EXISTS CALENDER (CALENDER_ID VARCHAR(255), SUMMARY TEXT);")
	conn.close()
	print('\ndatabase setup')
	return 

def setup_calenderApi():  
	SCOPES = ['https://www.googleapis.com/auth/calendar']
	creds = None
	# The file token.pickle stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.pickle'):
		with open('token.pickle', 'rb') as token:
			creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				'credentials.json', SCOPES)
			creds = flow.run_local_server()
		# Save the credentials for the next run
		with open('token.pickle', 'wb') as token:
			pickle.dump(creds, token)

	service = build('calendar', 'v3', credentials=creds)
	print('calender Api setup')
	return service

def QueryCalenderId():
	try:
		conn = sqlite3.connect("jobCalender.db")
	except:
		sys.exit()
		print("cannot connect to the database")
	cursor = conn.cursor()
	selectStatement = "SELECT CALENDER_ID FROM CALENDER WHERE SUMMARY = 'Job Hunting';"
	cursor.execute(selectStatement)
	result = cursor.fetchone()
	conn.close()
	print(result)
	return result 

def remove_calender(service,inputResult):
	if result != None:
		service.calendarList().delete(calendarId=result[0]).execute()
		time.sleep(5)
		print('removed calender')
	return 
	

def create_calender(service,inputResult): 
	calender = {
		"summary": "Job Hunting"
			}
	createdCalendar = service.calendars().insert(body=calender).execute()
	print (createdCalendar['id'])
	time.sleep(5)
	print('calender created')
	try:
		conn = sqlite3.connect("jobCalender.db")
	except:
		sys.exit()
		print("cannot connect to the database")
	cursor = conn.cursor()
	insertStatement = "INSERT INTO CALENDER VALUES ('%s','Job Hunting');" %createdCalendar['id']
	deleteStatement = "DELETE FROM CALENDER WHERE SUMMARY = 'Job Hunting';"
	if result == None:
		cursor.execute(insertStatement)
	else:
		cursor.execute(deleteStatement)
		cursor.execute(insertStatement)
	conn.commit()
	conn.close()
	print('calender id inserted into database')
	time.sleep(2)
	return createdCalendar['id']

def insert_events(service,inputCalenderId):
	for date,company,role in jobInfo:

		event=	{
			"end": {
				"date": date
			},
			"start": {
				"date": date
			},
			"reminders": {
				"useDefault": False,
				"overrides": [
				{
					"method": "popup",
					"minutes": 3780
				}
				]
			},
			"summary": role + '\n'+ company
			}
		event = service.events().insert(calendarId=inputCalenderId, body=event).execute()
		print ('Event created: %s' % (event.get('htmlLink')))
	return


if __name__ == '__main__':
	internet_on()
	login()
	totalPages=num_pages()
	getJobData(totalPages)
	setup_db()
	service = setup_calenderApi()
	result = QueryCalenderId()
	remove_calender(service,result)
	currentCalenderId= create_calender(service,result)
	insert_events(service,currentCalenderId)