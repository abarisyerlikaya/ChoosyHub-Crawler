import scrapy
import json
from re import search


class TrendyolSpider(scrapy.Spider):
    name = "trendyol"
    # first product page
    start_urls = [
        "https://api.trendyol.com/websearchgw/v2/api/infinite-scroll/cep-telefonu-x-c103498?pi=1&storefrontId=0&culture=tr-TR&userGenderId=1&pId=0&scoringAlgorithmId=2&categoryRelevancyEnabled=false&isLegalRequirementConfirmed=false&searchStrategyType=DEFAULT"]
    root_url = ["https://www.trendyol.com", "https://api.trendyol.com/websearchgw/v2/api/infinite-scroll/cep-telefonu-x-c103498", "https://cdn.dsmcdn.com"]
    custom_settings = {"CONCURRENT_REQUESTS_PER_DOMAIN": 2}

    def parse(self, response):
        string = response.css("p::text").extract_first()
        my_dict = json.loads(string)

        if len(my_dict["result"]["products"]) != 0:

            all_products = my_dict["result"]["products"]

            for product in all_products:
                id = product["id"]
                merchantId = product["merchantId"]
                
                imageLinks = product["images"]
                i = 0
                while i < len(imageLinks):
                    imageLinks[i] = self.root_url[2] + imageLinks[i]
                    i += 1

                number_of_reviews = product["ratingScore"]["totalCount"] if "ratingScore" in product.keys(
                ) else 0
                rating = round(product["ratingScore"]["averageRating"], 1) if "ratingScore" in product.keys(
                ) else 0.0

                item = {
                    "_id": self.root_url[0] + product["url"],
                    "name": product["name"],
                    "price": product["price"]["discountedPrice"],
                    "rating":  rating,
                    "number_of_reviews": number_of_reviews,
                    "number_of_comments": 0,
                    "pictures": imageLinks,
                    "comments": []
                }

                if number_of_reviews >= 1:
                    comment_url = "https://api.trendyol.com/webproductgw/api/review/" + \
                        str(id) + "?userId=0&merchantId=" + str(merchantId) + \
                        "&storefrontId=1&culture=tr-TR&order=5&searchValue=&page=0"
                    yield scrapy.Request(comment_url, callback=self.parse_reviews, meta={"item": item})

            next_page = int(response.request.url[response.request.url.find("?pi=") + 4 : response.request.url.find("&")]) + 1
            
            new_url = self.root_url[1] + "?pi=" + str(
                next_page) + "&storefrontId=0&culture=tr-TR&userGenderId=1&pId=0&scoringAlgorithmId=2&categoryRelevancyEnabled=false&isLegalRequirementConfirmed=false&searchStrategyType=DEFAULT"

            yield scrapy.Request(new_url, callback=self.parse)

    def parse_reviews(self, response):
        string = response.css("p::text").extract_first()
        
        my_comment_dict = json.loads(string)  # all json
        number_of_comments = my_comment_dict["result"]["productReviews"]["totalElements"]
    
        # number of total pages
        number_of_pages = my_comment_dict["result"]["productReviews"]["totalPages"]
        # number of current page
        current_page = my_comment_dict["result"]["productReviews"]["page"] if "page" in my_comment_dict["result"]["productReviews"].keys() else 0
        # number of comments in the page
        comments_per_page = len(
            my_comment_dict["result"]["productReviews"]["content"])
        current_url = response.request.url  # current url

        for i in range(0, comments_per_page):

            comment = my_comment_dict["result"]["productReviews"]["content"][i]["comment"]
            rating = my_comment_dict["result"]["productReviews"]["content"][i]["rate"]
            date = my_comment_dict["result"]["productReviews"]["content"][i]["commentDateISOtype"]

            comment = {
                "comment": comment,
                "rating": rating,
                "date": date
            }

            response.meta["item"]["comments"].append(comment)
            response.meta["item"]["number_of_comments"] = number_of_comments

        if (current_page < number_of_pages):

            next_url = current_url[:current_url.rfind(
                "=") + 1] + str(current_page + 1)
            yield scrapy.Request(next_url, callback=self.parse_reviews, meta={"item": response.meta["item"]})

        else:
            yield response.meta["item"]