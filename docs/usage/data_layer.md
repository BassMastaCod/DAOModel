# DataLayer

The **DataLayer** makes it easy to set up your database and work with your models. Think of it as a helpful tool that handles the boring database setup stuff for you.

## What is DataLayer?

DataLayer is a simple way to:
- Set up your database without writing lots of code
- Create DAOs (the objects that help you save and find your data)
- Keep everything organized and clean

You don't need to worry about the technical details - DataLayer handles them for you.

## Basic Setup

Here's how to get started with DataLayer:

```python
from daomodel.db import DataLayer
from myapp.models import Customer, Order

# Create a DataLayer with a file to store your data
data_layer = DataLayer(sqlite_path='myapp.db')

# Set up all your database tables
data_layer.init_db()

# Now you can work with your data
with data_layer.dao_context() as daos:
    customer_dao = daos[Customer]
    order_dao = daos[Order]

    # Create some data
    customer = customer_dao.create_with(id=1, name='John Doe')
    order = order_dao.create_with(id=100, customer_id=1, total=99.99)
```

That's it! DataLayer took care of all the database setup for you.

## Using Different Databases

### SQLite File Database (Recommended for beginners)

```python
# This creates a file called 'myapp.db' to store your data
data_layer = DataLayer(sqlite_path='myapp.db')
```

### Other Databases

If you need to use a different database like PostgreSQL or MySQL, you can provide your own database connection:

```python
from sqlalchemy import create_engine
from daomodel.db import DataLayer

# Connect to a PostgreSQL database
engine = create_engine('postgresql://user:password@localhost/mydb')
data_layer = DataLayer(engine=engine)
```

## Working with Your Data

Once you have DataLayer set up, you use it with a `with` statement. This makes sure everything gets cleaned up properly when you're done:

```python
with data_layer.dao_context() as daos:
    # Get the DAO for your model
    customer_dao = daos[Customer]

    # Create a new customer
    new_customer = customer_dao.create_with(name='Jane Smith', email='jane@example.com')

    # Find customers
    all_customers = customer_dao.find_all()
    jane = customer_dao.find_by_id(new_customer.id)
```

## Why Use DataLayer?

DataLayer makes your life easier by:

1. **Less Code**: You don't need to write lots of setup code
2. **Automatic Cleanup**: It handles closing database connections for you
3. **Consistent Setup**: All your DAOs work the same way
4. **Easy to Understand**: Simple, clear methods that do what you expect

## Complete Example

Here's a full example showing how to use DataLayer:

```python
from sqlmodel import Field
from daomodel import DAOModel
from daomodel.db import DataLayer

# Define your model
class Customer(DAOModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: str

# Set up the database
data_layer = DataLayer(sqlite_path='customers.db')
data_layer.init_db()

# Work with your data
with data_layer.dao_context() as daos:
    customer_dao = daos[Customer]

    # Add some customers
    john = customer_dao.create_with(id=1, name='John Doe', email='john@example.com')
    jane = customer_dao.create_with(id=2, name='Jane Smith', email='jane@example.com')

    # Find all customers
    customers = customer_dao.find_all()
    print(f"We have {len(customers)} customers")

    # Find a specific customer
    found_customer = customer_dao.find_by_id(1)
    print(f"Found: {found_customer.name}")
```

## Advanced: DAOFactory

If you need more control over how your database sessions work, you can use **DAOFactory**. This is more technical and usually not needed for simple applications:

```python
from sqlalchemy.orm import sessionmaker
from daomodel.db import DAOFactory, create_engine

# More manual setup
engine = create_engine('sqlite:///myapp.db')
session_factory = sessionmaker(bind=engine)

# Use DAOFactory for more control
with DAOFactory(session_factory) as daos:
    customer_dao = daos[Customer]
    # ... work with your data
```

Most of the time, DataLayer is all you need. Only use DAOFactory if you have specific requirements that DataLayer doesn't handle.

## Next Steps

Now that you've mastered the basics, explore the advanced features:
- [Advanced Search](../advanced/search.md) - Powerful search functionality beyond simple equality checks
- [Model Diff](../advanced/model_diff.md) - Compare models, track changes, and resolve conflicts
