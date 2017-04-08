import json
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
import urllib, urllib2, cookielib
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

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

#Reading the injection points list from the stored.json file

with open('stored.json') as injection_points_file:
    injection_points = json.load(injection_points_file)

#Read possible payloads from txt file

#with open('tmp_xss_payloads.txt') as payloads_file:
#    payloads = payloads_file.read().splitlines();
payloads = ["XSS"]
driver = webdriver.Firefox()

#Iterating through injection points, and trying each payload for them
for tmp in injection_points:
    url = tmp["action"]
    username = tmp["login"]["username"]
    password = tmp["login"]["password"]
    unamefield = "username"
    passwdfield = "password"
    btnfield = "login"
    attackString = "XSS"

    params = tmp["param"]
    method = tmp["method"]
    reflected_pages = tmp["reflected_pages"]

    #first do the login so that other pages which require login will pass
    match = re.search("https\:\/\/(.+)\.com\/",url)
    site = match.group(1)
    login_url = "https://"+site+".com/users/login.php"
    driver.get(login_url)
    time.sleep(4)

    uname = check_element_exists(unamefield,driver)
    passwd = check_element_exists(passwdfield,driver)
    btn = check_submit_exists(driver)

    if( uname and passwd and btn ):
        uname.send_keys(username)
        passwd.send_keys(password)
        btn.click()

    #Iterate through the all the payloads until something works
    for payload in payloads:
        
        #If get add the payload to url params and then execute url/button click
        if(method == "get"):
            get_values = "?"
            for param in params:
                get_values += param+"="+payload+"&"
            
            final_url = url+get_values
            print "In get, url is "+final_url+ "\n"
            driver.get(final_url)

        #If post add the payload to UI fields
        if(method == "post"):
            driver.get(url)
            #put the payload in each of the params and add to url_params list        
            for param in params:
                paramfield = check_element_exists(param,driver)
                if(paramfield):
                    paramfield.send_keys(payload)
            print "In post\n"
            btn = check_submit_exists(driver)
            btn.click()

        success_flag = 0
        #open reflected page and see if payload has come successfully through PXSS
        for page in reflected_pages:
            driver.get(page)
            time.sleep(5)
            try:
                while EC.alert_is_present():
                    alert = driver.switch_to_alert()
                    if attackString in alert.text:
                        print "exploit verified in " + driver.current_url
                    alert.accept()
                    time.sleep(2)
            except NoAlertPresentException:
                print "Cleared all alerts on page"
        break