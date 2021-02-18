import scrapy


class HepsiburadaSpider(scrapy.Spider):
    name = "hepsiburada"
    start_urls = [
        "https://www.hepsiburada.com/cep-telefonlari-c-371965?siralama=yorumsayisi"]
    root_url = "https://www.hepsiburada.com"

    # Parse pages in the product category
    def parse(self, response):
        last_page = int(response.css(
            "div#pagination ul li:last-child a::text").extract()[-1])

        for page in range(1, last_page + 1):
            yield scrapy.Request(self.start_urls[0] + "&sayfa=" + str(page), callback=self.parse_single_page)

    # Parse one result page
    def parse_single_page(self, response):
        all_products = response.css(
            "div#productresults ul li.search-item div.box.product")

        for product in all_products:
            number_of_reviews = product.css(
                "span.number-of-reviews").extract_first()

            if number_of_reviews is not None:
                product_url = product.css("a::attr(href)").extract_first()
                product_url = self.root_url + product_url

                if product_url is not None:
                    yield scrapy.Request(product_url, callback=self.parse_single_product)

    # Parse one product
    def parse_single_product(self, response):
        url = response.request.url

        name = response.css(
            "div.product-information header.title-wrapper h1.product-name#product-name::text"
        ).extract_first()

        price = response.css(
            "div.product-information div.product-price-wrapper div.product-price-and-ratings span.price::attr(content)"
        ).extract_first()

        rating = response.css(
            "div.product-information div.product-price-and-ratings a#productReviews span.rating-star::text"
        ).extract_first()

        number_of_reviews = response.css(
            "div.product-information div.product-price-and-ratings div#comments-container a.product-comments span::attr(content)"
        ).extract_first()

        pictures = response.css(
            'div#productDetailsCarousel a.cloudzoom picture::attr(data-cloudzoom)'
        ).extract()

        if name is not None:
            for i in range(0, len(pictures)):
                pictures[i] = pictures[i][pictures[i].find("https:"):-1]

            item = {
                "_id": url,
                "name": name.strip(),
                "price": float(price) if price is not None else 0.0,
                "rating": float(rating.strip().replace(",", ".")),
                "number_of_reviews": int(number_of_reviews),
                "number_of_comments": 0,
                "pictures": pictures,
                "comments": []
            }

            yield scrapy.Request(url + "-yorumlari?sayfa=1", callback=self.parse_reviews, meta={"item": item})

        else:
            yield scrapy.Request(response.request.url, callback=self.parse_single_page)

    # Parse reviews of a product
    def parse_reviews(self, response):
        current_page = response.css(
            "div.paginationBarHolder div.hermes-PaginationBar-module-3KhN9 ul li.hermes-PageHolder-module-Zrt7N span::text"
        ).extract_first()

        last_page = response.css(
            "div.paginationBarHolder div.hermes-PaginationBar-module-3KhN9 ul li:last-child span::text"
        ).extract_first()

        reviews = response.css(
            "div.hermes-ReviewList-module-crpVC div.paginationOverlay div.paginationContentHolder div.hermes-ReviewCard-module-34AJ_"
        )

        for review in reviews:
            comment = review.css(
                'div.hermes-ReviewCard-module-3Y36S span[itemprop="description"]::text'
            ).extract_first()

            if comment is not None:
                stars = review.css(
                    'div.hermes-RatingPointer-module-1OKF3 svg[xmlns="http://www.w3.org/2000/svg"] path[fill="#f28b00"]'
                ).extract()

                date = review.css(
                    'div.hermes-ReviewCard-module-3tT1_ span.hermes-ReviewCard-module-3fj8Y[itemprop="datePublished"]::attr(content)'
                ).extract_first()

                comment = (comment.strip() if comment is not None else None)
                rating = len(stars)

                comment_obj = {
                    "rating": rating,
                    "date": date,
                    "comment": comment
                }

                response.meta["item"]["comments"].append(comment_obj)
                response.meta["item"]["number_of_comments"] = response.meta["item"]["number_of_comments"] + 1

        # There is only one page or current page is last page
        if current_page is None or current_page == last_page:
            yield response.meta["item"]

        # Else, continue scraping reviews
        else:
            current_url = response.request.url

            if "sayfa=" in current_url:
                next_url = current_url[:current_url.rfind(
                    "=") + 1] + str(int(current_page) + 1)

            else:
                next_url = current_url + "?sayfa=" + str(int(current_page) + 1)

            yield scrapy.Request(next_url, callback=self.parse_reviews, meta={"item": response.meta["item"]})
