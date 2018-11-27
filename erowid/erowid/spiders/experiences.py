# -*- coding: utf-8 -*-
import scrapy
import re


class ExperiencesSpider(scrapy.Spider):
    name = 'experiences'
    allowed_domains = ['www.erowid.org']
    start_urls = ['https://www.erowid.org/experiences/exp_list.shtml']

    custom_settings = {
        'FEED_FORMAT':'jsonlines',
        'FEED_URI':'file:///tmp/erowid.json',
    }

    def parse(self, response):
        # follow links to categories
        for href in response.xpath('//li/a[contains(@href, "subs")]/@href'):
            yield response.follow(href, self.parse_category)

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

        data = response.css('.bodyweight-amount').xpath('./text()').extract_first()

        if data:
            experience['weight'] = data

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

        raw = []

        for tr in response.css('.footdata').xpath('.//tr'):
            for i in range(2):
                data = tr.xpath('./td[$col]//text()', col=i+1).extract_first()

                if data:
                    data = data.strip().replace('[','')

                    if len(data) > 0:
                        raw.append(data)

        for key, value in zip(['year', 'id', 'gender', 'age', 'published'], raw):
            if value == 'Not Given': continue

            experience[key] = value.split(': ')[-1]

        if len(raw) > 0:
            experience['tags'] = [tag.strip() for tag in re.sub('\([\d-]+\)', '', raw[-1]).replace(':',',').split(',')]

        ## text

        experience['text'] = ''.join(response.css('.report-text-surround').xpath('./text()').extract()).strip().replace('\r','')

        return experience
