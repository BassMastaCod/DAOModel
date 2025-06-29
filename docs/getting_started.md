# Getting Started with DAOModel

This guide will help you get started with **DAOModel** by showing you how to define your models and set up your database.

## Develop your SQLModel as usual
You may already have existing models written using **SQLModel**. If so, most of your work is already completed!
Otherwise, create a model such as the one below.

```python
class Customer(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
```

More on this at [SQLModel's Documentation](https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#create-the-table-model-class)

## Inherit DAOModel in place of SQLModel

`DAOModel` acts as a middleman, adding methods to your model class, turning it into a `DAOModel`.

```python
class Customer(DAOModel, table=True):
    id: int = Field(primary_key=True)
    name: str
```
> **Note:** Since `DAOModel` inherits from `SQLModel` your object still `isinstance(m, SQLModel)`.

## Configure and Initialize your DB

This library doesn't require you to set up your database in a specific manner.
[Skip ahead](#create-a-dao-for-your-daomodel) if you already know how to do so.
Otherwise, you may find some of the library's built-in functionality useful.

### 1. Create your engine using DAOModel's helper function

```python
engine = create_engine('database.db')
```

This uses **SQLite** to store your data. If you don't need persistence,
an in-memory **SQLite** DB is achievable by excluding the path:

```python
engine = create_engine()
```

While good to start, if/when this doesn't meet your needs, please refer to
[SQLAlchemy's Docs on Engines](https://docs.sqlalchemy.org/core/engines_connections.html)

### Initialize the Engine

Once you have your engine, you'll need to initialize each of the tables representing your models.

```python
init_db(engine)
```

This is simply a shortcut method of `SQLModel.metadata.create_all(engine)`.

> **Note:** Be sure your Models are all imported (if defined outside of this file)
> before executing this code or else those tables will not be included.

### Create a DB session

```python
db = Session(engine)
```

Again, this isn't anything specific to **DAOModel**, it is common across **SQLModel**, **Flask**, etc. so feel free to do this your own way.
There exist plenty of guides and tutorials, or you can start with [SQLAlchemy's Docs on Sessions](https://docs.sqlalchemy.org/orm/session_basics.html)

## Create a DAO for your DAOModel

At this point, you have a database and at least one model for your database.
This is about as far as **SQLModel** will take you before you must begin implementing your own logic.
The goal of **DAOModel** is to take you a little bit further and avoid writing code for common operations.
This will also abstract away the complexity of **SQLAlchemy** and make it easier to interact with your database.

With that said, creating a `DAO` is simple enough, but you will need your db session and your class that inherits `DAOModel`.

```python
DAO(Customer, db)
```

> **Note:** You pass the Class, not an instance of the Class, as the argument

All the tedious coding is handled by the `DAO` class.
It reads the definition of your model and provides your standard CRUD operations methods for the database session.

So there you have it, You now have a usable DAO layer for your model!
Let's look at the full code:

```python
from sqlmodel import Field, Session
from daomodel import DAOModel, DAO
from daomodel.db import create_engine, init_db

class Customer(DAOModel, table=True):
    id: int = Field(primary_key=True)
    name: str

engine = create_engine('database.db')
init_db(engine)
db = Session(engine)
dao = DAO(Customer, db)
```

The above may not be exactly what is wanted for your final product, but it gets you up and running quickly.
Just a few lines is all you need to get started!

## Next Steps

Now that you have set up your model and DAO, you can start using the DAO to interact with your database.
Continue to the [Using the DAO](usage/dao.md) section to learn more about the available operations.
