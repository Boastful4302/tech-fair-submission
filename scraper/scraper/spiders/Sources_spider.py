from pathlib import Path

import scrapy
import json
class SourceSpider(scrapy.Spider):
    name = "source"
    def parse_da_source(self,response):
        yield {
            "source_url":response.url,
            "page_title":response.css("title::text").get(),
            "status":response.status
        }
    def start_requests(self):
        with open("sources.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            link = item.get("source_url")
            if link:
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_da_source

                )
    