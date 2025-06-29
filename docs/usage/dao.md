# Using the DAO

The [previous page](../getting_started.md) concluded with access to a DAO instance.
This page explains the basic operations available through your new DAO interface.

For the examples on this page, we'll assume the following sample DAOs.
```python
from daomodel import DAO, DAOModel
from daomodel.fields import Identifier

class Customer(DAOModel, table=True):
    id: Identifier[int]
    name: str
    email: str

# Model with a composite primary key
class OrderDetail(DAOModel, table=True):
    order_id: Identifier[int]
    line_number: Identifier[str]
    product_code: Identifier[bytes]
    quantity: int

dao = DAO(Customer, db)
order_dao = DAO(OrderDetail, db)
```
> **Note:** `db` in the above code is from [Getting Started](../getting_started.md#configure-and-initialize-your-db).
> <br>`Identifier` defines a field as a Primary Key which will be described on the [Model](model.md#identifier) page.

## CRUD Operations

The DAO class provides a complete set of **C**reate, **R**ead, **U**pdate, and **D**elete operations for your DAOModel instances.
These operations make it easy to interact with your database without writing SQL queries.

### Create

Creating new records in your database is straightforward with the DAO.

::: daomodel.dao.DAO.create
```python
# Create a new customer with just the primary key
customer = dao.create(1) # Creates a Customer with id=1

# Create an OrderDetail having multiple primary key values
order = order_dao.create(42, 'A123', b'PRD001') 
```

If you wish to set more properties than just the primary key, you will want to use the `create_with` method.

::: daomodel.dao.DAO.create_with
```python
# Create a customer with specific values
customer = dao.create_with(id=3, name='John Smith', email='john@example.com')
```
> **Note:** The `create_with` method requires the primary key values to be provided as keyword arguments.

If you wish to create a model without adding it to the database, you can set the `insert` parameter to False.

```python
customer = dao.create_with(id=4, name='Guest User', insert=False)
```

If using `insert=False` you will then need to explicitly call `insert` if you wish to add the row to the DB.

::: daomodel.dao.DAO.insert
```python
# Create a model without inserting it
customer = dao.create_with(id=5, name='Alice Brown', email='alice@example.com', insert=False)

# Insert it into the database
dao.insert(customer)
```

After adding to the database, you will now be able to read the data.

### Read

The DAO provides several methods to retrieve data from your database.

::: daomodel.dao.DAO.get
```python
# Get a customer by primary key
customer = dao.get(1)  # Gets Customer with id=1

# Get an order detail with a composite primary key
order = order_dao.get(42, 'A123', b'PRD001')  # Again, order must match the model definition
```

The `get_with` method expands upon `get` by optionally applying additional values.

::: daomodel.dao.DAO.get_with
```python
# Get a customer and modify its properties
customer = dao.get_with(id=1, name='Updated Name')
```
> **Note:** Like `create_with`, the `get_with` method requires keyword arguments for the primary key.

If you do not know the primary key values, you can search for a record based on other properties.

::: daomodel.dao.DAO.find
Searching is covered in more detail on the [Search](search.md) page.

If you only need to know if a model is in the DB, the `exists` method can help with that.

::: daomodel.dao.DAO.exists
```python
# Check if a customer exists by creating a temporary instance
temp_customer = Customer(id=1)
if dao.exists(temp_customer):
    print('Customer exists!')
```
> **Note:** If you don't have the model instance, a `get` call within a `try` block may be simpler.

### Update

The DAO provides methods to easily update existing records.

::: daomodel.dao.DAO.commit
```python
# Get a customer and update it
customer = dao.get(1)
customer.name = 'New Name'
dao.commit()  # Save changes

# Or use get_with to update in less steps
customer = dao.get_with(id=1, name='Another Name')
# Save changes and refresh the model reference to continue using it
dao.commit(customer)
print(customer.name)  # prints 'Another Name'
```

Alternatively, you can use the `upsert` method to store the updated record regardless of if it exists.

::: daomodel.dao.DAO.upsert
```python
# Create a model that may or may not exist
customer = Customer(id=10, name='Maybe New', email='maybe@example.com')

# Create row if id=10 doesn't exist, or update row if already present
dao.upsert(customer)
```

If it is the primary key values you need to change, both `commit` and `upsert` may not work as you intend.
The `rename` method handles this for you.

::: daomodel.dao.DAO.rename
```python
# Get an existing customer
customer = dao.get(1)

# Rename (change primary key)
dao.rename(customer, 100)  # Changes id from 1 to 100

# When renaming composite keys, pass all primary key values in order
order = order_dao.get(42, 'A123', b'PRD001')
# Change order_id, and product_code (but not line_number)
order_dao.rename(order, 43, 'A123', b'PRD002')
```

### Delete

Finally, if you need to delete a record, the DAO provides that method too.

::: daomodel.dao.DAO.remove
```python
# Get a customer
customer = dao.get(1)

# Remove it
dao.remove(customer)

# Or remove using a temporary instance
dao.remove(Customer(id=2))  # raises NotFound if it isn't in the database
```

## Transactions

The DAO supports transactions to ensure data integrity when performing multiple operations. A transaction is a sequence
of database operations that are treated as a single unit of work.
Either the transaction completes all the operations (committed), or none of them (rolled back).
This ensures data consistency and helps maintain the integrity of your database.

To better understand this concept, let's consider an example. If you're transferring money between two accounts,
you want both the withdrawal and deposit to either succeed together or fail together -
you don't want one to happen without the other. _Transactions_ provide this "all-or-nothing" guarantee.

To enter _transaction mode_, use the `start_transaction` method.

::: daomodel.dao.DAO.start_transaction
```python
# Start a transaction
dao.start_transaction()

try:
    # Perform multiple operations
    customer1 = dao.create_with(id=1, name='Transaction Test 1')
    customer2 = dao.create_with(id=2, name='Transaction Test 2')
    
    # Commit the transaction
    dao.commit()
except Exception as e:
    # Rollback on error
    dao.rollback()
    print(f'Transaction failed: {e}')
```

#### commit
As you can see above, [commit()](#update) is how you finalize a transaction.
It saves all pending changes to the database and exits transaction mode.
If you wish to follow up with an additional transaction, you can call `start_transaction` again.
If you wish to back out of all changes instead of committing them, you can see that is done through a rollback.

::: daomodel.dao.DAO.rollback
```python
dao.start_transaction()

# Make some changes
customer = dao.create_with(id=100, name='Will be rolled back')

# Decide to cancel these changes
dao.rollback()

# The customer won't be in the database
try:
    dao.get(100)  # This will raise NotFound
except NotFound:
    print('Customer was not created due to rollback')
```

It may not be obvious at this time if you will want to use transactions, but just remember
it is here to simplify the process if you do find you need to _group_ some actions together.

## Query

The DAO provides access to SQLAlchemy's powerful query interface for other, unsupported operations.

```python
query = dao.query

# Example: Update all customers with '@example.com' email to have 'Example Customer' as their name
query.filter(Customer.email.like('%@example.com')).update(
    {'name': 'Example Customer'},
    synchronize_session=False
)

# Don't forget to commit the changes
dao.commit()
```

All the information you need for SQLAlchemy querying can be found in their [ORM Querying Guide](https://docs.sqlalchemy.org/orm/queryguide/index.html).
So if something is not supported directly with DAOModel, you are able to use SQLAlchemy instead.
Or, if you feel it is a good feature, [submit a ticket](https://github.com/BassMastaCod/DAOModel/issues/new) to request it be added to DAOModel.

## Next Steps

Now that you understand how to use the DAO, let's move on to the details of [Models](model.md) on the next page.
You will see how the DAOModel library can vastly reduce the amount of code it takes to design your database tables.
