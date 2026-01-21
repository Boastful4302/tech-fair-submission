from pathlib import Path
import os
import scrapy
import json

cur_dir = Path(__file__).resolve()
cur_dir = str(cur_dir).split('\\')
cur_dir = cur_dir[:-2]
sep = "\\"
cur_dir = sep.join(cur_dir)

class SourceSpider(scrapy.Spider):
    name = "sources"
    output_dir = "document_folder"

    def parse_da_source(self,response):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        yield {
            "source_url":response.url,
            "page_title":response.css("title::text").get(),
            "status":response.status
        }
        page = response.url.split("/")[-2]
        filename = f"{self.output_dir}\Info-{page}.html"


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
    