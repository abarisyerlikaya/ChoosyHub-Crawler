# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo


class ChoosyhubCrawlerPipeline:
    def __init__(self):
        self.conn = pymongo.MongoClient(
            "mongodb+srv://admin:choosyhub@cluster0.axzel.mongodb.net/choosyhub?retryWrites=true&w=majority")
        self.db = self.conn["choosyhub"]
        self.products = self.db["products"]

    def process_item(self, item, spider):
        self.products.find_one_and_replace({"_id": item["_id"]},
                                           item,
                                           upsert=True)
        return item
