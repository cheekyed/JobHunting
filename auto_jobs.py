from urllib.request import urlopen
from bs4 import BeautifulSoup
from robobrowser import RoboBrowser
import socket 
import os


careersUrl= 'https://careersonline.unsw.edu.au/students/jobs/Bookmarks?page=1'

def internet_on():
	try:
		socket.create_connection(("www.google.com", 80))
		print('internet connection is on\n')
	except OSError:
		print('no internet connection\n')
		sys.exit()
	return

def login():
	browser = RoboBrowser()
	browser.open(careersUrl)
	form = browser.get_form(action = '/providers/ldap/login/1?returnURL=%2Fstudents%2Fjobs%2FBookmarks%3Fpage%3D1')
	form['username'].value = 'z5118744'
	form['password'].value = 'Warcraft321!'
	browser.session.headers['Referer'] = careersUrl
	browser.submit_form(form)
	print(str(browser.select))


def main ():
	internet_on()
	login()



if __name__ == '__main__':
	main()



