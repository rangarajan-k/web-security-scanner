# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FormItem(scrapy.Item):
    action = scrapy.Field()
    login = scrapy.Field()
    method = scrapy.Field()
    param = scrapy.Field()
    reflected_pages = scrapy.Field()

    def __eq__(self, other):
        return self['action'] == other['action'] and self['method'] == other['method'] and self['param'] == other['param']




