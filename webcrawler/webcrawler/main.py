import os
import json
import time
from scrapy import cmdline

DEBUG = False

if DEBUG:
    app_index = 9
    login_index = -1
    command = "scrapy crawl web -a app_index=%s -a login_index=%s -o stored.json" % (app_index, login_index)
    cmdline.execute(command.split())
else:
    dir_path = os.path.dirname(os.path.realpath(__file__)).replace(' ', '\ ')  # web-security-scanner/webcrawler/webcrawler
    output_path = '%s/crawler_output/' % dir_path
    command_tml = 'scrapy crawl web -a app_index=%s -a login_index=%s -o '
    file_name_tml = 'app_%s_login_%s.json'

    # clear output folder
    os.system("rm -r %s" % output_path)

    # data is taken from setup.json
    with open('setup.json') as setup_file:
        data = json.load(setup_file)
    for app_index in range(0, len(data)):
        # if login len == 0 just return -1
        if len(data[app_index]['logins']) == 0:
            login_index = -1
            file_name = file_name_tml % (app_index, login_index)
            output_file_uri = output_path + file_name

            command = command_tml % (app_index, login_index)
            command += output_file_uri
            print('------------------------------ Start Crawl: app_%s_login_%s ------------------------------- ' % (
            app_index, login_index))
            os.system(command)
            print('------------------------------ End Crawl: app_%s_login_%s --------------------------------- ' % (
            app_index, login_index))
            time.sleep(1)
            continue

        for login_index in range(0, len(data[app_index]['logins'])):
            file_name = file_name_tml % (app_index, login_index)
            output_file_uri = output_path + file_name

            command = command_tml % (app_index, login_index)
            command += output_file_uri
            print('------------------------------ Start Crawl: app_%s_login_%s ------------------------------- ' % (app_index, login_index))
            os.system(command)
            print('------------------------------ End Crawl: app_%s_login_%s --------------------------------- ' % (app_index, login_index))
            time.sleep(1)


