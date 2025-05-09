# DAOModel
An instant CRUD layer for your Python models (Powered by
[SQLModel](https://sqlmodel.tiangolo.com/) /
[Pydantic](https://docs.pydantic.dev/latest/) /
[SQLAlchemy](https://www.sqlalchemy.org/)).

* Eliminate repetitive work by auto-creating your DAOs
* Make your code more straightforward and readable
* Write less code, meaning:
    * have a usable product sooner
    * less testing
    * less potential for bugs

## Purpose
Assembled from a collection of duplicated logic found across several projects,
this library serves as a starting point for your database-backed Python project.
Though great for complex apps, it's also a great starting point for simple projects.
DAOModel will benefit new developers the most by providing a straight forward start to writing code.

A goal of my libraries is to remove upfront hurdles to facilitate learning along the way.
Following the [Guides](https://daomodel.readthedocs.io/en/latest/docs/getting_started/),
anyone can get started without knowledge of relational databases or SQLAlchemy.
If any documentation or design is unclear,
please [submit a ticket](https://github.com/BassMastaCod/DAOModel/issues/new)
so that I can be sure that even beginners are able to benefit from this project.

## Features
* Expands upon SQLModel; works with your existing models
* SQLAlchemy under the hood; keep existing logic while using DAOModel functions for new code
* Advanced search capabilities without raw SQL
* Quality-of-life additions

Looking for more? Check out my other projects on [GitHub](https://github.com/BassMastaCod)

## Installation
Python 3.10+ is required.

SQLModel, SQLAlchemy, and all other dependencies will be installed with the pip cmd:
```
pip install DAOModel
```
or, given that this project is a development tool, you will likely add _DAOModel_ to `requirements.txt` or `pyproject.toml`.

Next, move on to the [Getting Started](https://daomodel.readthedocs.io/en/latest/docs/getting_started/) page to begin developing your DAOModels.

## Caveats

### Database Support
Most testing has been completed using SQLite, though since SQLModel/SQLAlchemy
support other database solutions, DAOModel is expected to as well.

Speaking of SQLite, this library configures Foreign Key constraints to be enforced by default in SQLite.

### Table Names
Table names are configured to be snake_case which differs from SQLModel.
This can be adjusted by overriding `def __tablename__` in your own child class.

### Unsupported Functionality
Not all functionality will work as intended through DAOModel.
If something isn't supported, [submit a ticket](https://github.com/BassMastaCod/DAOModel/issues/new) or pull request.
And remember that you may always use what you can and then
override the code or use the query method in DAO to do the rest.
It should still save you a lot of lines of code.
