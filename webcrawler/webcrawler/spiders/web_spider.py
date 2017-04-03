import scrapy
import json
from scrapy.spiders import CrawlSpider
from scrapy.spiders.init import InitSpider
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import Rule
from webcrawler.items import FormItem
from scrapy.http import Request


class WebSpider(CrawlSpider):
    name = "web"
    start_urls = []
    login_urls = []
    login_details = []
    app_index = 0
    login_index = 1
    total_login = 0
    total_items = []

    rules = [Rule(link_extractor=LxmlLinkExtractor(deny='logout'), callback='parse_form', follow=True)]
    with open('setup.json') as setup_file:
        data = json.load(setup_file)

    # def __init__(self, app_index=0, *args, **kwargs):
    #     super(WebSpider, self).__init__(*args, **kwargs)
    #     self.app_index = app_index

    def start_requests(self):
        self.logger.info("Start Request")
        self.start_urls.append(self.data[self.app_index]["starting_url"])
        self.total_login = len(self.data[self.app_index]['logins'])

        for login in self.data[self.app_index]["logins"]:
            self.login_urls.append(login['url'])
            self.login_details.append({'username': login['username'], 'password': login['password']})

        # Login first before crawling starts
        return [Request(url=self.login_urls[self.login_index], callback=self.login, dont_filter=True)]

    def parse_form(self, response):
        self.logger.info("Parse URL: %s", response.url)
        for formPosition in range(0, len(response.css('form'))):
            form = response.css('form')[formPosition]
            item = FormItem()
            action = response.css('form::attr(action)').extract()[formPosition]
            action_page = response.urljoin(action)
            item['action'] = action_page
            item['method'] = response.css('form::attr(method)').extract()[formPosition]
            item['param'] = []
            item['login'] = self.login_details[self.login_index]
            item['reflected_pages'] = [response.url]
            if response.url != action_page:
                item['reflected_pages'].append(action_page)
            for param in form.css('input::attr(name)').extract():
                item['param'].append(param)
            if item not in self.total_items:
                self.total_items.append(item)
                yield item


    def extract_links(self, response):
        for link in LxmlLinkExtractor().extract_links(response):
            Request(url=link.url, callback=self.parse_form)
            return Request(url=link.url, callback=self.extract_links)

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
            return Request(url=response.url, dont_filter=True)