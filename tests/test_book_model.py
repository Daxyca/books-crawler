from src.app.models.book import Book


def test_book_model():
    book = Book(
        name="Test Book",
        category="Fiction",
        currency="£",
        price_excl_tax=8.0,
        price_incl_tax=10.0,
        availability="In stock",
        num_reviews=5,
        rating="Five",
        image_url="http://example.com/image.jpg",
        source_url="http://example.com/book/1",
    )
    assert book.name == "Test Book"
    assert book.price_incl_tax == 10.0
