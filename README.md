# DAOModel
An instant CRUD layer for your Python models (Powered by
[SQLModel](https://sqlmodel.tiangolo.com/) /
[Pydantic](https://docs.pydantic.dev/latest/) /
[SQLAlchemy](https://www.sqlalchemy.org/)).

Eliminate repetitive work by auto-creating your DAOs.
There is no need to write SQL queries or recall how to work with
SQLAlchemy models when you are only looking to do basic functionality.

## Supported Functions
* `create`
* `insert`
* `update` (commit changes made to an entry)
* `upsert`
* `rename` (change the primary key values of an entry)
* if `exists`
* `get`
* `find` (supports advanced searching, more details below)
* `remove`
* access to `query` (to do anything else not directly supported)

## Features
* DAOModel expands upon SQLModel so no need to learn a new way to define your models.
* Existing SQLModel, Pydantic, and SQLAlchemy functionality is still accessible for anything not built into DAOModel.
* Provides many quality-of-life additions that I found to be repeated throughout my own projects.

Looking for more? Check out my other projects on [GitHub](https://github.com/BassMastaCod)

## Installation
Python 3.10+ is required.

SQLModel, SQLAlchemy, and all other dependencies will be installed with the pip cmd:
```
pip install DAOModel
```
or, given that this project is a development tool, you will likely add _DAOModel_ to `requirements.txt` or `pyproject.toml`.

Next, move on to the [Getting Started](https://daomodel.readthedocs.io/docs/getting_started) page to begin developing your DAOModels.

## Caveats
Most testing has been completed using SQLite, though since SQLModel/SQLAlchemy
support other database solutions, DAOModel is expected to as well.

Speaking of SQLite, this library configures Foreign Key constraints to be enforced by default in SQLite.

Table names are configured to be snake_case which differs from SQLModel.
This can be adjusted by overriding `def __tablename__` in your own child class.

Not all functionality will work as intended through DAOModel.
If something isn't supported, submit a ticket or pull request.
And remember that you may always use what you can and then
override the code or use the query method in DAO to do the rest.
It should still save you a lot of lines of code.
