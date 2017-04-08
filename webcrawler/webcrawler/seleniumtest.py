from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
import time

#====================================
# Format for verifying using selenium
#====================================


# Create a new instance of the Firefox driver
driver = webdriver.Firefox()
usernameName = "username"
passwordName = "password"
submitText = "login"
username = "scanner1"
password = "scanner1"
logoutText = "logout"
attackString = "XSS"
# go to the google home page
driver.get("https://app1.com/users/login.php")

# the page is ajaxy so the title is originally this:
print driver.title

# find the element that's name attribute is q (the google search box)
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
# submit the form (although google automatically searches now without submitting)

time.sleep(3) # delay for page to load

if logoutText in driver.page_source: #.find("logout")
	print "logged in successfully"
else:
	print "not logged in sucessfully"

driver.get("https://app1.com/pictures/view.php?picid=15")

try:
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
