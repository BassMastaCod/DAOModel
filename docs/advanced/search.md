# Searching Models

A Model [DAO](../usage/dao.md) includes powerful, built-in search capabilities that make it easy to find and filter data.
This is all done through the `find` function which replaces complex SQL queries with function calls that are quick to write and easy to read.

Searches can range from simple equality checks to compound conditions using operators.
Of course, a standard [Query](../usage/dao.md#query) could be used, but utilizing **DAOModel** is the simpler way to:

- Find specific records by their properties
- Filter data based on complex conditions
- Paginate large result sets
- Order results by specific properties
- Identify duplicate or unique values

Let's explore these capabilities using a library management system as an example.

## Basic Search

Imagine a library management system with _authors_, _books_, and _borrowers_:

```python
class Author(DAOModel, table=True):
    id: Identifier[int]
    name: str
    nationality: Optional[str]
    birth_year: Optional[int]

class Book(DAOModel, table=True):
    isbn: Identifier[str]
    title: str
    author_id: Author
    genre: str
    publication_year: int
    available: bool
    pages: int

class Borrower(DAOModel, table=True):
    id: Identifier[int]
    name: str
    email: Optional[str]
    membership_type: str
    active: bool
    join_date: datetime
    notes: Optional[str]
```

The simplest way to search these models is by using the `find` method with exact value matches:

```python
# Find all Canadian authors
canadian_authors = author_dao.find(nationality='Canadian')

# Find all books in the Mystery genre
mystery_books = book_dao.find(genre='Mystery')

# Find all active borrowers
active_borrowers = borrower_dao.find(active=True)
```

We can also search for records based on multiple criteria:

```python
# Find authors that are the same age as me
american_authors = author_dao.find(nationality='American', birth_year=1991)

# Find new books that are still on the shelf
new_books = book_dao.find(publication_year=2025, available=True)
```

The `find` function returns a `SearchResults` object. Let's look into that class more.

## Search Results

`SearchResults` is a list-like object containing the matching entries.
In fact, the `SearchResults` class extends Python's built-in `list` so it behaves exactly like a list.

```python
# Iterate through results
for book in mystery_books:
    print(f'{book.title} by Author #{book.author_id}')

# Check the total number of results
total_mystery_books = len(mystery_books)

# Narrow to the first 3 results
first_three_books = mystery_books[:3]
```

The `SearchResults` class has some added convenience methods as well:

::: daomodel.dao.SearchResults.first
```python
# Get the first result for Dracula
dracula = book_dao.find(title='Dracula').first()
```

::: daomodel.dao.SearchResults.only
```python
# We expect a single result
try:
    tolkien = author_dao.find(name='J. R. R. Tolkien').only()
except ValueError:
    print('Found multiple authors named Tolkien')
```

Most of the time, you likely have several search results. If those results grow too large, pagination is an option.

## Pagination

Pagination allows you to retrieve a subset of results from a larger result set.
This is essential for large amounts of data that cannot fit in memory.
It is also useful for displaying results one portion at a time.
Or perhaps only a few results are needed for a specific task.

To use pagination, specify the page number and number of results per page using the `_page` and `_per_page` parameters:

```python
# Get the first page of mystery books, 10 per page
page1 = book_dao.find(genre='Mystery', _per_page=10)

# Get the second page
page2 = book_dao.find(genre='Mystery', _page=2, _per_page=10)
```

!!! warning
    If you specify `page` without `per_page`, a `MissingInput` error will be raised

`page1` and `page2` are both `SearchResults`, but now with a fraction of the total results.
Information about the current page and full results are available through the following `SearchResults` properties.

```python
# Display pagination information
print(f'Showing page {page2.page} of {page2.total_pages}')
        # Showing page 2 of 6

print(f'Displaying {page2.page_start}-{page2.page_end} of {page2.total} results')
        # Displaying 11-20 of 62 results

print(f'Continue to the next {page2.per_page} matches')
        # Continue to the next 10 matches
```

To make the first few pages useful, be sure to sort the items in a meaningful order.

## Ordering Results

By default, search results are ordered using the primary key.
For _Books_, this means that they are sorted according to the _ISBN_ which is not very useful.
Thankfully, this can be configured with the `_order` parameter.

```python
# Order books by title
books_by_title = book_dao.find(_order=Book.title)

# Order books by publication year
books_by_year = book_dao.find(_order='publication_year')
```

!!! tip
    As seen above, fields can be referenced by either the class property, or the column name.

Both of the previous sorts are _ascending_, which is ideal for title but not for publication year.
We want to list the newer books first instead. That can be achieved with a `desc` expression.

```python
new_first = book_dao.find(_order=desc(Book.publication_year))
```

!!! tip
    `desc`, among other expressions, are available to import from `sqlmodel`.

Multiple columns can be specified when defining the order:

```python
# Order by length, but list available books first
books_ordered = book_dao.find(_order=(desc(Book.available), Book.pages))

# Order by name. For duplicated names, show active and most recent accounts first
borrowers_ordered = borrower_dao.find(_order=('name', desc('active'), desc('join_date')))
```

To support CLI and other _text only_ interfaces, `desc` can also be specified by prepending `!` to the column name.

```python
borrowers_ordered = borrower_dao.find(_order=('name', '!active', '!join_date'))
```

That is only the tip of the iceberg for searching, next we'll introduce **ConditionOperators**.

## Advanced Filtering

Advanced filtering may be done using `ConditionOperators`.
These operators are shortcuts of commonly used expressions. 
The operators cover value comparisons, collection checks, and existence checks.

### Comparison Operators

Comparison operators allow filtering based on numeric comparisons:

```python
from daomodel.util import GreaterThan, LessThan, GreaterThanEqualTo, LessThanEqualTo, Between

# Find books published after 2000
modern_books = book_dao.find(publication_year=GreaterThan(2000))

# Find books published prior to the 20th century
old_books = book_dao.find(publication_year=LessThan(1900))

# Find books that cost between $10 and $20
eighties_books = book_dao.find(publication_year=Between(1980, 1989))

# Find books with at least 1000 pages
long_books = book_dao.find(pages=GreaterThanEqualTo(1000))

# Find books no more than 200 pages
short_books = book_dao.find(pages=LessThanEqualTo(200))
```

### Collection Operators

Collection operators allow matching against a set of values:

```python
from daomodel.util import AnyOf, NoneOf

# Find books in either Fantasy or Science Fiction genres
scifi_fantasy = book_dao.find(genre=AnyOf('Fantasy', 'Science Fiction'))

# Find books that are not Romance or Biography
not_romance_bio = book_dao.find(genre=NoneOf('Romance', 'Biography'))
```

### Existence Operators

Existence operators allow checking if a field has a value or not:

```python
from daomodel.util import is_set, not_set

# Find borrowers with notes
notes = borrower_dao.find(notes=is_set)

# Find borrowers that do not have an email address
missing_email = borrower_dao.find(email=not_set)
```

### Duplicate and Unique Values

**DAOModel** makes it easy to find records that share values for a specific property:

```python
# Find potential duplicate accounts
duplicated_names = borrower_dao.find(_duplicate=Borrower.name)
duplicated_emails = borrower_dao.find(_duplicate='email')

# Find books that have the same title
duplicated_titles = book_dao.find(_duplicate='title')
```

Similarly, non-duplicates can also be found:

```python
# Find nationalities that aren't well represented
authors = author_dao.find(_unique='nationality')
nationalities = {author.nationality for author in authors}
```

We can even find duplicates or uniques across related models:

```python
# Find authors with only one book
single_book_authors = author_dao.find(_unique=Book.author_id)

# Find authors with multiple available books
authors_on_shelf = author_dao.find(_duplicate='book.available')
```

That mostly covers the `find` functionality of a DAO, but there is still some customization that can be done.

## Excluding Fields from Search

For security, or just to clean up an API, `find()` can be disabled for specific properties. 
Use the `Unsearchable` type to mark fields in a model:

```python
class Borrower(DAOModel, table=True):
    id: Identifier[int]
    name: str
    email: str
    membership_type: str
    active: bool
    join_date: datetime
    notes: str
    ssn: Unsearchable[str]  # Sensitive data - not searchable
```

If you try to search by an unsearchable field, an `UnsearchableError` will be raised:

```python
try:
    borrower_dao.find(ssn='123456789')  # Error: ssn is unsearchable
except UnsearchableError:
    print('Cannot search for unsearchable field')
```

This applies to all search operations, including ordering and finding duplicates:

```python
try:
    borrower_dao.find(_order=Borrower.ssn)  # Error
except UnsearchableError:
    print('Cannot order by unsearchable field')

try:
    borrower_dao.find(_duplicate=Borrower.ssn)  # Error
except UnsearchableError:
    print('Cannot find duplicates of unsearchable field')
```

## Customizing Search Behavior

TODO - Give example of overriding `filter_find()`.

## Search by Foreign Properties

TODO - Explain how to make foreign keys searchable (this might fit better within another section).

## Next Steps

- Define common query combinations using a [Service Layer](../usage/service.md)
- Learn about [Model Comparison and Diffing](model_diff.md)
