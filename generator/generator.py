import os
import json
from pprint import pprint

exploitPath = '../payload_injector/confirmed_exploits'
loginPath = '../webcrawler/webcrawler/setup.json'
# usernameField = ("username", "user", "email", "id")
usernameField = "username"
passwordField = "password"
logoutText = "logout"
submitButtonText = "login"
attackString = "XSS"
errorFlag = False

# functions
def askFilename(filename):
	valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
	if os.path.isfile(filename):
		print "Overwrite existing " + filename + " ? [Y/n]"
		response = raw_input().lower()
		if response == '':
			print "Overwriting..."
			return True
		elif response in valid:
			overwriteFile = valid[response]
			return True
		else:
			return False
	else:
		return True


# assume there is only confirmed exploits json files
for exploitFile in os.listdir(exploitPath):
	with open(exploitPath+"/"+exploitFile) as exploit_data_file:    
		exploitData = json.load(exploit_data_file)
    
	#pprint(exploitData)	

	siteList = []

	# Grab list of sites to watch for
	for x in exploitData: # x is a dict_obj
		#print x['reflected_page'].split('/')[2]
		#print x.keys()[0].split('/')[2] # extract just the site name
		#siteList.append(x.keys()[0].split('/')[2]) #rXSS
		
		if len(x['reflected_pages']) > 0:
			siteList.append(x['reflected_pages'][0].split('/')[2]) #pXSS
		else:
			print "No reflected_pages in " + exploitFile + " ??"
			errorFlag = True

	if not errorFlag:
		loginNo = int(exploitFile.split("login_")[1].split(".")[0])
		siteName = siteList[0].split(".")[0]
		fileName = "generated/" + siteList[0].replace('.','_') + "_login_" + str(loginNo) + "_script.py"
		overwriteFile = True
	
		while True:
			if askFilename(fileName):
				break

		if not overwriteFile:
			print "Enter new filename:"
			response = raw_input().lower()
			fileName = response

		print "Creating " + fileName

		attackScript = open(fileName, "w")		

		#===================== Writing imports ===============================
		initial = '#!/usr/bin/python\n\n'
		imports = "import re\n"

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

		#===================== Initialise values==============================
		initialiseVals = "# blacklist of button values to avoid\n"
		initialiseVals += "blacklist = (\"cancel\", \"remove\", \"delete\")\n"

		print "\nWriting variables to initiliase..."
		attackScript.write(initialiseVals)
		print "Written variables to initiliase...\n"

		#===================== Logging In ====================================
		username = None
		password = None
		url = None

		# Grab login page from setup
		with open(loginPath) as login_data_file:    
		    loginData = json.load(login_data_file) # data is a list_obj

		for x in loginData: # x is a dict_obj
			if siteList[0] == x['starting_url'].split('/')[2]:
				username = x['logins'][loginNo]['username']
				password = x['logins'][loginNo]['password']
				url = x['logins'][loginNo]['url']

		if not username or not password or not url:
			print "Error in login credentials"
			attackScript.close()
			sys.exit("Login credential error")

		print "Using User: " + username + "  Pwd: " + password 
		print "With login page " + url

		loginCredentials = "username = \"" + username + "\"\n"
		loginCredentials += "password = \"" + password + "\"\n"
		loginCredentials += "url = \"" + url + "\"\n\n"

		attackScript.write(loginCredentials)

		#===================== Attacking =====================================
		# via requests
		requestsStart = "\n#===== Start of requests powered attacker====\n"
		requestsStart += "requests.packages.urllib3.disable_warnings(InsecureRequestWarning)\n"
		requestsStart += "session = requests.session()\n\n"
		requestsStart += "urlComponents = url.split(\"/\")\n"
		requestsStart += "root = urlComponents[0]+\"//\"+ urlComponents[2]\n\n"
		print "\nWriting Start of Requests powered attacker..."
		attackScript.write(requestsStart)
		print "Written Start of Requests powered attacker..."

		# useful functions for attacking
		requestsFunc = "def check_for_more_form(r):\n"
		requestsFunc += "	checkForForm = True\n"
		requestsFunc += "	while checkForForm:\n"
		requestsFunc += "		insideForm = False\n"
		requestsFunc += "		submitForm = False\n"
		requestsFunc += "		newTarget = None\n"
		requestsFunc += "		formMethod = None\n"
		requestsFunc += "		param = {}\n\n"
		requestsFunc += "		# check if need to submit form again (eg. if there is a preview stage)\n"
		requestsFunc += "		for line in r.text.splitlines():\n"
		requestsFunc += "			if \"<form\" in line.lower():\n"
		requestsFunc += "				found =  re.match(r\".*action\s*=\s*\\\"\s*([^\\\"]*)\s*\\\"\", line, re.IGNORECASE)\n"
		requestsFunc += "				if found:\n"
		requestsFunc += "					newTarget = found.group(1)\n"
		requestsFunc += "					if \"http\" not in newTarget:\n"
		requestsFunc += "						newTarget = root + newTarget\n"
		requestsFunc += "				found =  re.match(r\".*method\s*=\s*\\\"\s*([^\\\"]*)\s*\\\"\", line, re.IGNORECASE)\n"
		requestsFunc += "				if found:\n"
		requestsFunc += "					formMethod = found.group(1)\n"
		requestsFunc += "				insideForm = True\n"
		requestsFunc += "				param.clear()\n"
		requestsFunc += "				print \"entered form\"\n"
		requestsFunc += "			elif \"</form\" in line.lower():\n"
		requestsFunc += "				insideForm = False\n"
		requestsFunc += "				print \"exited form\"\n"
		requestsFunc += "			if insideForm:\n"
		requestsFunc += "				if \"input\" in line.lower() and \"submit\" in line.lower():\n"
		requestsFunc += "					if any(s in line.lower() for s in blacklist):\n"
		requestsFunc += "						newTarget = None\n"
		requestsFunc += "						formMethod = None\n"
		requestsFunc += "						param.clear\n"	
		requestsFunc += "				elif \"input\" in line:\n"	
		requestsFunc += "					name = \"\"\n"
		requestsFunc += "					value = \"\"\n"
		requestsFunc += "					found =  re.match(r\".*name\s*=\s*\\\"\s*([^\\\"]*)\s*\\\"\", line, re.IGNORECASE)\n"
		requestsFunc += "					if found:\n"
		requestsFunc += "						name = found.group(1)\n"
		requestsFunc += "					found =  re.match(r\".*value\s*=\s*\\\"\s*([^\\\"]*)\s*\\\"\", line, re.IGNORECASE)\n"
		requestsFunc += "					if found:\n"
		requestsFunc += "						value = found.group(1)\n"
		requestsFunc += "					if not found or not value.strip():\n"
		requestsFunc += "						insideForm = False\n"
		requestsFunc += "						newTarget = None\n"
		requestsFunc += "						formMethod = None\n"
		requestsFunc += "						param.clear()\n"
		requestsFunc += "					param.update({name:value})\n"
		requestsFunc += "					print name + \" \" + value\n"
		requestsFunc += "				elif \"textarea\" in line:\n"
		requestsFunc += "					insideForm = False\n"
		requestsFunc += "					newTarget = None\n"
		requestsFunc += "					formMethod = None\n"
		requestsFunc += "					param.clear()\n\n"		
		requestsFunc += "		if newTarget and formMethod:\n"
		requestsFunc += "			print newTarget\n"
		requestsFunc += "			if \"post\" in formMethod.lower():\n"
		requestsFunc += "				r = session.post(newTarget, data=param, verify=False)\n"
		requestsFunc += "			elif \"get\" in formMethod.lower():\n"
		requestsFunc += "				r = requests.get(url, params=param, verify=False)\n"
		requestsFunc += "		else:\n"
		requestsFunc += "			checkForForm = False\n\n"
		print "\nWriting useful functions of Requests powered attacker..."
		attackScript.write(requestsFunc)
		print "Written useful functions of Requests powered attacker..."

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

		def loop_params(method, param):
			string =""
			link = "="
			a = ""
			if method:
				link = ":"
				a = "\""
			for y in param:
				count = param.index(y)
				string += a + param[count]['key'] + a + link +"\"" + param[count]['value'] +"\""
				if (count+1) < len(param):
					string += ","	
			return string

		for x in exploitData: 
			requestsAtk += "url =\"" + x['reflected_pages'][0] + "\"\n"
			if "get" in x['method'].lower():
				print "get"
				requestsAtk += "exploit_data = {"
				requestsAtk += loop_params(True, x['params'])
				requestsAtk += "}\n"
				requestsAtk += "r = requests.get(url, params=exploit_data, verify=False)\n"
			elif "post" in x['method'].lower():
				print "post"
				requestsAtk += "exploit_data = dict("
				requestsAtk += loop_params(False, x['params'])
				requestsAtk += ") #build params\n"
				requestsAtk += "r = session.post(url, data=exploit_data, verify=False)\n"
			requestsAtk += "print \"attacked \" + url + \" ...\"\n"
			requestsAtk +="check_for_more_form(r)\n\n"
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
			# for y in x.keys():
			exploitedPage = x['reflected_pages'][0]
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


print "end"