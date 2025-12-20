from pathlib import Path

import scrapy


class ScrapingSpider(scrapy.Spider):
    name = "scraping"
    def __init__(self, topic:str, *args, **kwargs):
        super(ScrapingSpider, self).__init__(*args,**kwargs)
        #topic = topic.replace(" ", "_")
        self.start_urls = ["https://en.wikipedia.org/wiki/" + topic]
#       self.search_string = "https://www.google.com/search?q=" + topic

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = f"Info-{page}.html"
        citations = response.css("a.external::attr(href)").getall()
        for link in citations:
            yield {
                "source_url": link
            }
        Path(filename).write_bytes(response.body)
        