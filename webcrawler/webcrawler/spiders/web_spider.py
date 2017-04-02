import scrapy
import json
from scrapy.spiders import CrawlSpider
from scrapy.spiders.init import InitSpider
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import Rule
from webcrawler.items import FormItem
from scrapy.http import Request


class WebSpider(InitSpider):
    name = "web"
    start_urls = []
    login_urls = []
    login_details = []
    app_index = 0
    login_index = 0
    total_login = 0

    rules = [Rule(link_extractor=LxmlLinkExtractor(), callback='parse_form', follow=False)]
    with open('setup.json') as setup_file:
        data = json.load(setup_file)

    # def __init__(self, app_index=0, *args, **kwargs):
    #     super(WebSpider, self).__init__(*args, **kwargs)
    #     self.app_index = app_index

    def init_request(self):
        self.logger.info("Init Request")
        self.start_urls.append(self.data[self.app_index]["starting_url"])
        self.total_login = len(self.data[self.app_index]['logins'])

        for login in self.data[self.app_index]["logins"]:
            self.login_urls.append(login['url'])
            self.login_details.append({'username': login['username'], 'password': login['password']})

        # Login first before crawling starts
        return Request(url=self.login_urls[self.login_index], callback=self.login)

    def parse_form(self, response):
        self.logger.info("Parse URL: %s", response.url)
        items = []
        for formPosition in range(0, len(response.css('form'))):
            form = response.css('form')[formPosition]
            item = FormItem()
            action = response.css('form::attr(action)').extract()[formPosition]
            actionPage = response.urljoin(action)
            item['action'] = actionPage
            item['method'] = response.css('form::attr(method)').extract()[formPosition]
            item['param'] = []
            item['reflected_pages'] = [response.url]
            if response.url != actionPage:
                item['reflected_pages'].append(actionPage)
            for param in form.css('input::attr(name)').extract():
                item['param'].append(param)
            items.append(item)
        yield {'key': items}

    def login(self, response):
        self.logger.info("Login")
        # Search for login form and login
        for form_position in range(0,len(response.css('form'))):
            form = response.css('form')[form_position]
            params = [param for param in form.css('input::attr(name)').extract()]
            if params == ['username', 'password']:
                return [scrapy.FormRequest.from_response(
                    response,
                    formnumber=form_position,
                    formdata=self.login_details[self.login_index],
                    callback=self.after_login
                )]
        # Couldn't found login form, log error
        self.logger.critical("Couldn't found form for login!")

    def after_login(self, response):
        self.logger.info("After Login")
        # check login succeed before going on
        if not self.login_details[self.login_index]['username'] in response.body:
            self.logger.critical("Login failed")
            return None
        else:
            self.logger.info("Login succeed")
            return self.initialized