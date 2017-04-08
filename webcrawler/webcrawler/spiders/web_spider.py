import scrapy
import json
import urlparse
from scrapy.spiders import CrawlSpider
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import Rule
from scrapy.http import Request
from webcrawler.items import FormItem


class WebSpider(CrawlSpider):
    name = "web"

    # Properties from main.py (command line execute)
    app_index = 0
    login_index = 1

    # Properties used by crawler
    total_items = []

    # data is taken from setup.json
    with open('setup.json') as setup_file:
        data = json.load(setup_file)
    # Properties from setup.json file
    total_login = 0
    login_details = []
    login_urls = []
    start_urls = []

    # Seen urls using for filter in process_links
    seen_urls = dict() # dict of "url" : "seen_time"
    MAX_SEEN = 5

    # Rule for CrawlSpider
    rules = [Rule(link_extractor=LxmlLinkExtractor(deny='logout'), callback='parse_url', process_links='process_links', follow=True)]

    def __init__(self, app_index=0, login_index=1, *args, **kwargs):
        super(WebSpider, self).__init__(*args, **kwargs)
        self.app_index = int(app_index)
        self.login_index = int(login_index)

    def start_requests(self):
        self.logger.info("Start Request")
        self.start_urls.append(self.data[self.app_index]["starting_url"])
        self.total_login = len(self.data[self.app_index]['logins'])

        for login in self.data[self.app_index]["logins"]:
            self.login_urls.append(login['url'])
            self.login_details.append({'username': login['username'], 'password': login['password']})

        # Login first before crawling starts
        return [Request(url=self.login_urls[self.login_index], callback=self.login, dont_filter=True)]

    # Skip link that crawler has seen its same url and param more than MAX_SEEN times
    def process_links(self, links):
        for link in links:
            url_parsed = urlparse.urlparse(link.url)
            url_without_query = url_parsed.scheme + "://" + url_parsed.netloc + url_parsed.path
            params = urlparse.parse_qsl(url_parsed.query)
            # allow link without param, will automatically being filtered if visited
            if len(params) == 0:
                yield link
                continue

            for x,y in params:
                url_without_query = url_without_query + "/" + x
            if url_without_query in self.seen_urls :
                self.seen_urls[url_without_query] += 1
                if self.seen_urls[url_without_query] > self.MAX_SEEN:
                    continue
            else:
                self.seen_urls[url_without_query] = 1
            yield link

    # Parse url
    def parse_url(self, response):
        self.logger.info("Parse URL: %s", response.url)

        # Parsing GET param
        url_parsed = urlparse.urlparse(response.url)
        item = FormItem()
        item['method'] = 'GET'
        url_without_query = url_parsed.scheme + "://" + url_parsed.netloc + url_parsed.path
        item['action'] = url_without_query
        item['param'] = []
        params = urlparse.parse_qsl(url_parsed.query)
        for x, y in params:
            item['param'].append(x)
        item['reflected_pages'] = [url_without_query]
        if len(item['param']) != 0 and item not in self.total_items:
            self.total_items.append(item)
            yield item

        # Parsing forms
        for formPosition in range(0, len(response.css('form'))):
            form = response.css('form')[formPosition]
            item = FormItem()

            # Action
            action = response.css('form::attr(action)').extract()[formPosition]
            action_page = response.urljoin(action)
            item['action'] = action_page
            # Method
            item['method'] = response.css('form::attr(method)').extract()[formPosition]
            # Reflected_page
            if not len(self.login_details) == 0:
                item['login'] = self.login_details[self.login_index]
            item['reflected_pages'] = [response.url]
            if response.url != action_page:
                item['reflected_pages'].append(action_page)
            # Param
            item['param'] = []
            for param in form.css('input::attr(name)').extract():
                item['param'].append(param)
            for param in form.css('textarea::attr(name)').extract():
                item['param'].append(param)

            if item not in self.total_items:
                self.total_items.append(item)
                yield item

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