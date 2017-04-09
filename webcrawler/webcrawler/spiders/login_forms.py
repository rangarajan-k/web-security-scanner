import sys
from argparse import ArgumentParser
from collections import defaultdict
from lxml import html
import urlparse
import re

USERNAME_REGEX = re.compile('user|name|admin|root|email|login', re.IGNORECASE)
USERNAME_FIELDS = ['text', 'email']

PASSWORD_REGEX = re.compile('pass|key', re.IGNORECASE)

def check_login_form(form, setup_username_key, setup_password_key):
    username_key = None
    password_key = None
    inputs = form.css('input');
    
    # Check setup values
    if setup_username_key is not None and setup_password_key is not None:
        has_username_key = False
        has_password_key = False
        for input in inputs:
            name = input.css('::attr(name)').extract_first()
            if name == setup_username_key:
                has_username_key = True
            elif name == setup_password_key:
                has_password_key = True
        return setup_username_key, setup_password_key if has_username_key and has_password_key else None, None
    else:
        for input in inputs:
            name = input.css('::attr(name)').extract_first()
            type = input.css('::attr(type)').extract_first()
            if name is None:
                continue
            if type == 'password' and PASSWORD_REGEX.search(name):
                password_key = name
            if type in USERNAME_FIELDS and USERNAME_REGEX.search(name):
                username_key = name
    return username_key, password_key

def fill_login_form_data(form, login_details):
    username_key = login_details['username_key']
    password_key = login_details['password_key']
    form_data = dict()
    inputs = form.css('input');
    for input in inputs:
        name = input.css('::attr(name)').extract_first()
        type = input.css('::attr(type)').extract_first()
        value = input.css('::attr(value)').extract_first()
        if name is not None: # As input with no name is not processed to server
            if name == username_key:
                form_data[username_key] = login_details['username']
            elif name == password_key:
                form_data[password_key] = login_details['password']
            elif type == 'button' or type == 'submit': # Skip all button and submit
                continue
            elif value is not None: # Use preset value
                form_data[name] = value
            elif type == 'radio' or type == 'checkbox': # Set True to all radio and checkbox
                form_data[name] = True;
            else:
                form_data[name] = 'randomtext'
    return form_data              
