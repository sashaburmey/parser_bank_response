import scrapy
import json
import urllib
import datetime
import requests
from bank1.items import Bank1Item

class BankSpider(scrapy.Spider):
    handle_httpstatus_list = [429]
    def __init__(self):
        self.date = datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%Y")
        res = requests.get(url='http://www.banki.ru/bitrix/components/banks/universal.select.region/ajax.php?baseUrl=&appendUrl=&prependUrl=&type=city&type=city')
        self.city = self.parse_city(res)

    def parse_city(self, response):
        city_url = []
        json_city = json.loads(response.text)
        for item in json_city['data']:
            cu = item['url']
            cs = cu.split('/')
            city_url.append({'url':cs[3]+'/'+cs[4], 'region_name': item['region_name']})
        return city_url


    name = "bank"
    def start_requests(self):
        # modes = ['first','second','selectiveTour','memoryBook']
        modes = ['first']
        for mode in modes:
            url = 'http://www.banki.ru/services/responses/?mode='+mode+'&date='+self.date+'&json=1'
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        json_bank = json.loads(response.body)
        for item in json_bank['banksData']:
            bank_id = json_bank['banksData'][item]['code']
            url = 'http://www.banki.ru/services/responses/bank/'+bank_id
            yield scrapy.Request(url=url, callback=self.parse1_5)

    def parse1_5(self, response):
        prop_bank = {}
        prop_bank['count_res'] = response.xpath(".//li[@class='company-properties__item']/div[@itemprop='count']/text()").extract_first()
        prop_bank['nation_rating'] = response.xpath(".//li[@class='company-properties__item' and position()=2]/div[position()=2]/text()").extract_first()
        prop_bank['nation_number'] = response.xpath(".//span[@itemprop='average']/text()").extract_first()
        prop_bank['average'] = response.xpath(".//li[@class='company-properties__item' and position()=3]/div[position()=2]/text()").extract_first()
        prop_bank['solution'] = response.xpath(".//li[@class='company-properties__item' and position()=4]/div[position()=2]/text()").extract_first()
        prop_bank['answers'] = response.xpath(".//li[@class='company-properties__item' and position()=6]/div[position()=2]/text()").extract_first()
        for city in self.city:
            url = response.url + 'city/' +  city['url']
            yield scrapy.Request(url=url, callback=self.parse2)


    def parse2(self, response):
        cats = ['autocredits', 'deposits', 'debitcards','businessdeposits', 'remote', 'hypothec', 'creditcards', 'businesscredits', 'leasing', 'corporate', 'credits', 'restructing']
        for cat in cats:
            url = response.url + 'product/' + cat + '/?ajax=1'
            yield scrapy.Request(url=url, callback=self.parse3)

    def parse3(self, response):
        href = response.xpath(".//a[@itemprop='summary']/@href").extract()
        if len(href)>0:
            for hr in href:
                url = 'http://www.banki.ru' + hr
                yield scrapy.Request(url=url, callback=self.parse4)

    def parse4(self, response):
        res_bank = {}
        res_bank['title'] = response.xpath(".//h1[@itemprop='summary']/text()").extract_first()
        res_bank['description'] = response.xpath(".//div[@itemprop='description']/").extract_first()
        res_bank['rating'] = response.xpath(".//span[@itemprop='rating']/meta/@content").extract_first()
        res_bank['coments'] = response.xpath(".//a[@href='#comments']/span/text()").extract_first()
        res_bank['reviewer'] = response.xpath(".//span[@itemprop='reviewer']/text()").extract_first()
        res_bank['views'] = response.xpath(".//div[@class='inline-elements inline-elements--x-small']/span/text()").extract_first()
        res_bank['status'] = response.xpath(".//*[contains(@class,'response-status')]").extract_first()
        res_bank['dtreviewed'] = response.xpath(".//time[@itemprop='dtreviewed']/text()").extract_first()
        bank_answer = response.xpath(".//div[@id='bankAnswer']/").extract_first()
        if bank_answer is not None:
            res_bank['bank_answer'] = True
