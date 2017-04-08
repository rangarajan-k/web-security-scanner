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

#Reading the injection points list from the stored.json file

with open('stored.json') as injection_points_file:
    injection_points = json.load(injection_points_file)

#Read possible payloads from txt file

with open('tmp_xss_payloads.txt') as payloads_file:
    payloads = payloads_file.read().splitlines();

driver = webdriver.Firefox()

#Iterating through injection points, and trying each payload for them
for tmp in injection_points:
    url = tmp["action"]
    username = tmp["login"]["username"]
    password = tmp["login"]["password"]
    unamefield = "username"
    passwdfield = "password"
    btnfield = "login"

    params = tmp["param"]
    method = tmp["method"]
    reflected_pages = tmp["reflected_pages"]

    match = re.search("https\:\/\/(.+)\.com\/",url)
    site = match.group(1)
    login_url = "https://"+site+".com/login.php"
    driver.get()
    uname = check_element_exists(unamefield,driver)
    passwd = check_element_exists(passwdfield,driver)
    btn = check_submit_exists(btnfield,driver)

    if( uname && passwd && btn )
        uname.send_keys(username)
        paswd.send_keys(password)
        btn.click()

    for payload in payloads:
        param_values = dict();
        
        if(method == "get")
            base_url = url
            get_values = "?"
            for param in params:
                get_values +=  
                
        
        if(method == "post")
            driver.get(url)
            #put the payload in each of the params and add to url_params list        
            for param in params:
                paramfield = check_element_exists(param)
                if(paramfield)
                    paramfield.send_keys(payload)
            

        success_flag = 0
        #open reflected page and see if payload has come successfully through PXSS
        for page in reflected_pages:
            driver.get(page)
            driver.implicitly_wait(20)

            if (payload_type == "alert")


                    




    print username
    
def check_element_exists(name,driver):
    try:
        inputElement = driver.find_element_by_name(name)
    except NoSuchELementException:
        return False
    return inputElement

def check_submit_exists(name,driver):
    try:
        inputElement = driver.find_element_by_xpath("//input[@type='submit']")
    except NoSuchELementException:
        return False
    return inputElement