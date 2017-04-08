import os
import json

dir_path = os.path.dirname(os.path.realpath(__file__)).replace(' ', '\ ') # web-security-scanner/webcrawler/webcrawler
output_path = '%s/crawler_output/' % dir_path
command_tml = 'scrapy crawl web -a app_index=%s -a login_index=%s -o '
file_name_tml = 'app_%s_login_%s.json'

# clear output folder
os.system("rm -r %s" % output_path)

# data is taken from setup.json
with open('setup.json') as setup_file:
    data = json.load(setup_file)
for app_index in range(0, len(data)):
    for login_index in range(0, len(data[app_index]['logins'])):
        file_name = file_name_tml % (app_index, login_index)
        output_file_uri = output_path + file_name

        command = command_tml % (app_index, login_index)
        command += output_file_uri
        os.system(command)
