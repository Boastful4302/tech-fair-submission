from pathlib import Path

import scrapy
import json

cur_dir = Path(__file__).resolve()
cur_dir = str(cur_dir).split('\\')
cur_dir = cur_dir[:-2]
sep = "\\"
cur_dir = sep.join(cur_dir)

class SourceSpider(scrapy.Spider):
    name = "sources"
    
    def parse_da_source(self,response):
        yield {
            "source_url":response.url,
            "page_title":response.css("title::text").get(),
            "status":response.status
        }
        page = response.url.split("/")[-2]
        filename = f"Info-{page}.html"
        Path(filename).write_bytes(response.body)

    def start_requests(self):
        with open(cur_dir + "\sources.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            link = item.get("source_url")
            if link:
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_da_source

                )
    