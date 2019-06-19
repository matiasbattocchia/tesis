# -*- coding: utf-8 -*-
import scrapy
import re


class ExperiencesSpider(scrapy.Spider):
    name = 'experiences'
    allowed_domains = ['erowid.org']
    start_urls = ['https://www.erowid.org/experiences/exp_list.shtml']

    custom_settings = {
        'FEED_FORMAT':'jsonlines',
        'FEED_URI':'file:///tmp/erowid.json',
    }

    def parse(self, response):
        ## New way: access experiencies trying ids
        for id in range(0,120000):
            href = 'https://erowid.org/experiences/exp.php?ID={}'.format(id)
            yield response.follow(href, self.parse_experience)
            
        ## Old way: follow links to categories
        #for href in response.xpath('//li/a[contains(@href, "subs")]/@href'):
        #    yield response.follow(href, self.parse_category)

    def parse_category(self, response):
        # follow pagination links
        for href in response.xpath('//a[contains(img/@alt,"next")]/@href'):
            yield response.follow(href, self.parse_category)

        # follow links to experiences
        for href in response.xpath('//a[contains(@href, "exp.php?ID=")]/@href'):
            yield response.follow(href, self.parse_experience)

    def parse_experience(self, response):
        experience = {}

        experience['author'] = response.css('.author').xpath('./a/text()').extract_first()

        experience['cellar'] = bool(response.css('#report-rating-cellar-title').xpath('./text()').extract_first())

        experience['weight'] = response.css('.bodyweight-amount').xpath('./text()').extract_first()

        ## dose chart

        experience['doses'] = []

        for tr in response.css('.dosechart').xpath('.//tr'):
            dose = {}

            for i, column_name in enumerate(['time','amount','method','substance','form']):
                data = ''.join(tr.xpath('./td[$col]//text()', col=i+1).extract()) \
                    .replace('DOSE:','') \
                    .replace('(','') \
                    .replace(')','') \
                    .strip()

                if len(data) > 0:
                    dose[column_name] = data

            experience['doses'].append(dose)

        ## footdata

        rows = response.css('.footdata').xpath('.//tr')
        
        experience['year']      = rows[0].xpath('./td[1]//text()').extract_first()
        experience['id']        = rows[0].xpath('./td[2]//text()').extract_first()
        experience['gender']    = rows[1].xpath('./td[1]//text()').extract_first()
        experience['age']       = rows[2].xpath('./td[1]//text()').extract_first()
        experience['published'] = rows[3].xpath('./td[1]//text()').extract_first()
        experience['tags']      = rows[5].xpath('./td[1]//text()').extract_first()
        
        ## text

        experience['text'] = ''.join(response.css('.report-text-surround').xpath('./text()').extract()).strip().replace('\r','')

        return experience
