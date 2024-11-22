# DAOModel
An instant CRUD layer for your Python models (Powered by
[SQLModel](https://sqlmodel.tiangolo.com/)/
[Pydantic](https://docs.pydantic.dev/latest/)/
[SQLAlchemy](https://www.sqlalchemy.org/)).

Eliminate repetitive work by auto creating your DAOs.
There is no need to write SQL queries or recall how to work with
SQLAlchemy models when you are only looking to do basic functionality.

## Supported Functions
* `create`
* `insert`
* `update`
* `upsert`
* if `exists`
* `get`
* `find` (supports advanced searching, more details below)
* `remove`
* access to `query` (to do anything else not directly supported)

## Features
* DAOModel expands on SQLModel so no need to learn a new way to define your models.
* Existing SQLModel, Pydantic, and SQLAlchemy functionality is still accessible for anything not built into DAOModel.
* Provides many quality of life additions that I found to be repeated throughout my own projects.

## Usage
### Develop your SQLModel as usual:
```python
class Customer(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
```
More on this at [SQLModel's Documentation](https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#create-the-table-model-class)

### Inherit DAOModel in place of _SQLModel_
`DAOModel` acts as a middleman, adding methods to your class.
Yet `DAOModel` inherits from `SQLModel`
meaning your object still `isinstance(m, SQLModel)`.
```python
class Customer(DAOModel, table=True):
    id: int = Field(primary_key=True)
    name: str
```

### Configure and Initialize your database
This library doesn't really care how you setup your DB. Skip ahead if you already know how to do so.
Otherwise, you may find some of the library's built-in functionality useful.

#### Create your engine using DAOModel's helper function
```python
engine = create_engine("database.db")
```
This uses SQLite to store your data. If you don't need persistence,
an in-memory SQLite DB (perfect for testing) is achievable by excluding the path:
```python
engine = create_engine()
```
While good to start, when/if this doesn't meet your needs, please refer to
[SQLAlchemy's Docs on Engines](https://docs.sqlalchemy.org/core/engines_connections.html)

#### Initialize the Engine
Once you have your engine, you'll need to initialize each of the tables representing your models.
```python
init_db(engine)
```
This is simply a shortcut method of `SQLModel.metadata.create_all(engine)`.
> **NOTE:** Be sure your Models are all imported (if defined outside of this file)
> before executing this code or else those tables will not be included.

#### Create a DB session
```python
db = Session(engine)
```
Again, this isn't anything that is specific to DAOModel,
it is common across SQLModel, Flask, etc. so feel free to do this your own way.
There exist plenty of guides and tutorials or you can start with [SQLAlchemy's Docs on Sessions](https://docs.sqlalchemy.org/orm/session_basics.html)

<br>

Now you are ready to populate your database, but for that, we are going to use the DAO!

### Create a DAO for your DAOModel
Creating a DAO is simple enough, but you will need your db session your class that inherits DAOModel.
```python
DAO(Customer, db)
```
> **NOTE:** You pass the Class to DAO, not an instance of the Class

So there you have it, You now have a usable DAO layer for your model!
Let's look at the full code:

```python
class Customer(DAOModel, table=True):
    id: int = Field(primary_key=True)
    name: str

engine = create_engine("database.db")
init_db(engine)
db = Session(engine)
dao = DAO(Customer, db)
```
It may not be exactly what is wanted for your final product, but it gets you up and running quickly.
Just a few lines is all you need to get started!

### Using the DAO
The whole premise of an automatic DAO layer is to make your code more straightforward and readable.
Read the docs for more details, otherwise the following table should give a general understanding.

| Action                     | Method | Under the hood                        | Example                     | 
|----------------------------|--------|---------------------------------------|-----------------------------|
| Create a new object        | create | Adds values as new row to DB table    | `model = dao.create(23)`    |
| Insert an object           | insert | Adds object as new row to DB table    | `dao.insert(model)`         |
| Update an object           | update | Updates column values of a row        | `dao.update(model)`         |
| Update or insert an object | upsert | Updates or inserts row if not present | `dao.upsert(model)`         |
| Check if an object exists  | exists | Checks if any rows match object       | `if dao.exists(model):`     |
| Get an object              | get    | Selects row by primary key            | `model = dao.get(23)`       |
| Search for objects         | find   | Selects rows by column values         | `results = dao.find("Bob")` |
| Delete an object           | remove | Deletes row from DB table             | `dao.remove(model)`         |

Check out the Sample Code for a more thorough example.
You can even use it as a template for your own project!

## Searching
One of the best features about DAOModel is the robust search functionality.
Without assembling complicated SQL queries, you are able to search by specific columns.
```python
results = dao.find(name="Bob")
```
Said columns can even be foreign keys or columns from related tables
(provided those columns are defined as searchable).
Take a look at `test_dao_find.py` to see some examples.

### Is column value set?
Perhaps you don't want to search for _Bob_, but rather find all customers who do not have any 'name'.
Using `True` and `False` limits your results to rows having, or not having, a value.
```python
# find all nameless customers
results = dao.find(name=False)
```

### Duplicate (or unique) values
Sometimes your customers (or other data) gets added more than once.
Wouldn't it be great to easily find all of these duplicates? Say no more!
```python
# find all customers that share a name with another customer
results = dao.find(duplicate=Customer.name)
```
Now I can see that I have 3 customers named _Bob_ and 2 named _Joe_ without listing each other customer.

Or maybe it's the unique values you wish to see:
`dao.find(unique=Customer.name)` will provide all customers that don't share a name,
in this case, excluding all the _Bobs_ and _Joes_.

### Sorting
The order of your results can easily be specified.
By default, results are sorted by primary key.
But you can sort by any column, foreign key, or foreign property you desire.
```python
# sort by name and then id
results = dao.find(order=(Customer.name, Customer.id))
```
> NOTE: wrap a column with `desc()` to reverse the order

### All of the above
The previously stated options can be done together if needed:
```python
results = dao.find(name=True, region="US",
                   duplicate=Customer.name, unique=Customer.address,
                   order=desc(Customer.last_modified))
```

### Integrated Pagination
Pages of results come naturally for searches done with DAOModel DAOs.
Indicate the number of intended results using the `per_page` argument.
Optionally specify which page number to retrieve using the `page` argument.
```python
for result in dao.find(page=2, per_page=10):
```
As seen above, the returned SearchResults are directly iterable.
But they also include properties for the total number of results.
The page number and number of results per page are also included for convenience.

## Additional Functionality
### Commit on Demand
Each of the modifying actions in the table above will auto-commit.
However, if you wish to prevent this, include the argument `commit=False`
In that scenario, you will need to call `dao.commit()` explicitly.
This is most useful when conducting batch actions, or when you may wish to abort the changes.

### Copying values
Values (other than the primary key) can be copied from one model instance to another.
This is done through `model.copy_model(other_model)` or `model.copy_values(**dictionary)`.
Both the `create` and `get` functionality have copying built-in in the form of `create_with` and `get_with`.
```python
# create a new row but also populate the name column in the same line
model = dao.create_with(id=52, name="Bob")

# select the now existing row but reassign the name
model = dao.get_with(id=52, name="Joe")

# calling get_with does not modify the DB, so you need to explicitly update or commit
dao.update(model)
```

### DAOFactory
The DAOFactory allows you to easily open and close sessions as needed.


In order to use it, get yourself a [session factory](https://docs.sqlalchemy.org/orm/session_basics.html#using-a-sessionmaker) and then use a `with` statement.
```python
session_factory = sessionmaker(engine)
with DAOFactory(session_factory) as daos:
    dao = daos[Customer]
```

Again, this may not fit your needs exactly,
but you can inherit from DAOFactory in order to create your own solution.

### Auto-increment ID
The [SQLModel Tutorial](https://sqlmodel.tiangolo.com/tutorial/automatic-id-none-refresh/)
discusses how to have an auto incrementing primary key.
This library contains a utility called `next_id()` that,
when passed as an argument, will not specify an ID so that it is auto generated.
```python
model = dao.create(next_id())
```
This code is equivalent to passing `None` as the argument.
However, the named method makes the line easier to understand.

## Caveats
Most testing has been completed using SQLite, though since SQLModel/SQLAlchemy
support other database solutions, DAOModel is expected to as well.

Speaking of SQLite, this library configures Foreign Key constraints to be enforced by default in SQLite.

Table names are configured to be snake_case which differs from SQLModel.
This can be adjusted by overridding `def __tablename__` in your own child class.

Not all functionality will work as intended through DAOModel.
If something isn't supported, submit a ticket or pull request.
And remember that you may always use what you can and then
override the code or use the query method in DAO to do the rest.
It should still save you a lot of lines of code.