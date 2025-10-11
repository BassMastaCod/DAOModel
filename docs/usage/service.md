# Service Layer

On the [previous page](model.md), we've learned about DAOModel methods,
now let's explore how to build a service layer on top of your DAOs.

## Overview

The [service layer](https://medium.com/@navroops38/understanding-the-service-layer-in-software-architecture-df9b676b3a16)
of a codebase provides functionality beyond basic [CRUD](dao.md#crud-operations).
Though less useful for straightforward applications, this layer keeps your code organized and [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself). 
Here are examples of logic you may find within a service layer:

- Bulk operations (conducting CRUD operations on multiple records)
- CRUD requiring preceding calculations (calculating a subtotal before storing an invoice)
- Validation (ensuring a calendar date is available before finalizing a booking)
- Working with [Transactions](dao.md#transactions)

The DAOModel library contains an extendable base for your service layer class,
offering core functionality which you can build into a full-featured service.

## Features

- Direct DAO Access
- Bulk Operations
- Transaction Management
- Model Merging
- Simple Service Creation
- Extendable for custom business logic
- Multi-DAO Support

### Service Types

DAOModel provides two variations of the service layer base,
each having their own useful shortcuts and functions.

#### BaseService

A standard service class having access to each of your existing DAOs.

BaseService offers:

- Access to the DAOFactory through the `daos` property
- [Bulk Operations](#bulk-operations)

#### SingleModelService

An extension of **BaseService** specifically designed around working with a single model type.

SingleModelService offers:

- Access to the model DAO through the `self.dao` property
- [Bulk Operations](#bulk-operations)
- [Model Merging](#merging-models)

## Usage

### Creating a Service

To create a service, you need a **DAOFactory** instance and, for **SingleModelService**, a primary model class:

```python
# Create a multi-DAO service
multi_service = BaseService(daos)

# Create a service for a specific model class
student_service = SingleModelService(daos, Student)
```

### Accessing the DAO

When using **SingleModelService**, you can access the DAO for the model through the `dao` property:

```python
# Access the DAO for CRUD actions
student = service.dao.get(1)
```

The same DAO is accessible using the **BaseService**, the code is just a bit more verbose since the model must be specified:

```python
# Access the DAO for CRUD actions
student = service.daos[Student].get(1)
```

### Bulk Operations

The `bulk_update` function is used to modify multiple entries/models at once without writing any SQL:

::: daomodel.base_service.BaseService.bulk_update

### Merging Models

The `SingleModelService` class provides a `merge` method for combining two models:

::: daomodel.base_service.SingleModelService.merge
```python
# Merge student1 into student2
service.merge(student1, 2)
```

This is particularly useful for scenarios such as:

- Resolving multiple accounts discovered for a single person
- Combining two classes into one
- Consolidating notes from different sources

When merging models, you may need to resolve conflicts between the source and destination.
See [Conflict Resolution](TODO) for more information.

### Extending the Services

You can extend either service class to add additional functionality:

```python
class StudentService(SingleModelService):
    def __init__(self, daos):
        super().__init__(daos, Student)

    def promote_to_next_grade(self, student):
        student.grade += 1
        self.dao.commit(student)
```

If you find yourself writing the same function for several of your services,
consider submitting a pull request to have it added to the base classes.
This will reduce help improve the library for everyone while reducing the amount of code you need to write.

## Next Steps

You now have a basic understanding of how to create your Models, Repository layer (DAO), and Service layer.
That may be all you need for your project. If not, you likely want to continue by creating a Controller layer.
If that is your next step, you will find my [Fast-Controller](https://pypi.org/project/Fast-Controller/) library essential.
Fast-Controller takes your DAOModels and automatically gives you a full-featured REST API.
This is perfect for rounding off your backend; making it accessible as a microservice
or available to a frontend such as a website/mobile app.

Otherwise, feel free to explore the advanced features of DAOModel:

- [DAOFactory](../advanced/dao_factory.md) for managing multiple DAOs
- [Model Comparison and Diffing](../advanced/model_diff.md) for more details on how model merging works
- [Search](../advanced/search.md) for advanced search capabilities
- [Testing](../advanced/testing.md) for utilities to make testing your code a breeze
