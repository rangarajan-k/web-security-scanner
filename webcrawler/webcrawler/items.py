# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FormItem(scrapy.Item):
    action = scrapy.Field()
    method = scrapy.Field()
    param = scrapy.Field()
    reflected_pages = scrapy.Field()


