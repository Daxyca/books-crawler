from datetime import datetime


def test_parse_book_page(parser, sample_book_html):
    url = "https://books.toscrape.com/catalogue/test-book.html"
    book = parser.parse_book_page(sample_book_html, url)

    assert book is not None
    assert book.name == "Test Book Name"
    assert book.description == "This is a test book description."
    assert book.category == "Fiction"
    assert book.price_excl_tax == 10.0
    assert book.price_incl_tax == 12.0
    assert book.num_reviews == 5
    assert book.availability == "In stock"
    assert book.rating == "Three"
    assert book.image_url == "https://books.toscrape.com/catalogue/media/image.jpg"
    assert book.source_url == url
    assert isinstance(book.crawl_timestamp, datetime)


def test_parse_catalogue_page(parser, sample_catalogue_html):
    current_url = "https://books.toscrape.com/catalogue/page1.html"
    urls = parser.parse_catalogue_page(sample_catalogue_html, current_url)

    expected = [
        "https://books.toscrape.com/catalogue/book1.html",
        "https://books.toscrape.com/catalogue/book2.html",
    ]
    assert urls == expected


def test_get_next_page_url(parser, sample_catalogue_html):
    current_url = "https://books.toscrape.com/catalogue/page1.html"
    next_url = parser.get_next_page_url(sample_catalogue_html, current_url)
    assert next_url == "https://books.toscrape.com/catalogue/page2.html"


def test_parse_book_page_missing_description(parser, sample_book_html):
    html_missing_desc = sample_book_html.replace(
        "<p>This is a test book description.</p>", "<p></p>"
    )
    url = "https://books.toscrape.com/catalogue/test-book.html"
    book = parser.parse_book_page(html_missing_desc, url)
    assert book.description is None


def test_parse_book_page_missing_image(parser, sample_book_html):
    html_missing_img = sample_book_html.replace('<img src="media/image.jpg"/>', "")
    url = "https://books.toscrape.com/catalogue/test-book.html"
    book = parser.parse_book_page(html_missing_img, url)
    assert book is None  # parser returns None on critical errors
