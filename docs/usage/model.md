# Improved Models

On the [previous page](dao.md), we've learned about using the DAO,
now let's explore how DAOModel enhances your database modeling experience.
This page explains the model-related features of DAOModel, including the shortcuts, utilities,
and additional features that make defining and working with database models more intuitive.

To understand the value that DAOModel brings, let's first compare it with SQLModel
(the foundation upon which DAOModel is built). This comparison will help you appreciate how
DAOModel extends SQLModel's capabilities to provide an even better developer experience.

## DAOModel vs SQLModel

DAOModel extends [SQLModel](https://sqlmodel.tiangolo.com/) to provide additional functionality
that makes working with database models easier and results in more readable code.
If you're already familiar with SQLModel, you'll find DAOModel adds
convenient methods and properties to simplify common operations.

### What is SQLModel?

[SQLModel](https://sqlmodel.tiangolo.com/) is a Python library that makes working with SQL databases easier by combining the data validation of
[Pydantic](https://docs.pydantic.dev/latest/) with the ORM capabilities of [SQLAlchemy](https://www.sqlalchemy.org/).

#### Why Database Models Matter

Without database models, you'd need to write raw SQL commands, manually validate data,
and handle type conversions yourself. This can be error-prone and time-consuming.

Database models solve these problems by providing a structured way to define your data.
You also get built-in validation and seamless conversion between Python objects and database records.

#### What SQLModel Provides

The purpose of SQLModel is to provide a way to:

- Define complete database tables with simple Python classes and type hints
- Validate data automatically based on those type hints
- Convert between Python objects and database records seamlessly
- Interact with your database using Python code instead of raw SQL

This allows you to work with your database in a more intuitive, type-safe way while reducing code.

For detailed information on how to use SQLModel, please refer to the [official SQLModel documentation](https://sqlmodel.tiangolo.com/).
Otherwise, let's move on to this library; DAOModel!

### Why Use DAOModel?

DAOModel builds on SQLModel's foundation to provide:

1. **Simplified Field Definitions** - Shortcuts for common field patterns like primary keys, foreign keys, and timestamps
2. **Automatic Table Naming** - Converts class names to snake_case for table names without manual configuration
3. **Enhanced Model Methods** - Convenient methods for working with primary keys, foreign keys, and model properties
4. **Improved Developer Experience** - Less of repetitive code and more of easy to follow logic

To begin exploring these features in detail, let's examine how DAOModel simplifies the process of defining database models.

## Defining Models

DAOModel simplifies database model definitions compared to vanilla SQLModel.
To understand the benefits, let's start with a sample code using only SQLModel:

> **Note:** Don't worry if this code block is overwhelming, DAOModel will help us fix that.

<details>
<summary>Click to view code that does not use DAOModel...</summary>
```python
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, ForeignKey, Column

def utc_now():
    return datetime.now()

class SubscriptionTier(Enum):
    BASIC = 'basic'
    PREMIUM = 'premium'
    ULTIMATE = 'ultimate'

class Artist(SQLModel, table=True):
    __tablename__ = 'artist'
    name: str = Field(primary_key=True)
    bio: Optional[str]
    albums: list['Album'] = Relationship()

class LivePerformanceEvent(SQLModel, table=True):
    __tablename__ = 'live_performance_event'
    venue: str = Field(primary_key=True)
    event_date: datetime = Field(primary_key=True)
    artist: str = Field(
        sa_column=Column(
            ForeignKey('artist.name', onupdate='CASCADE', ondelete='CASCADE')
        )
    )

class Album(SQLModel, table=True):
    __tablename__ = 'album'
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    title: str
    artist: str = Field(
        sa_column=Column(
            ForeignKey('artist.name', onupdate='CASCADE', ondelete='RESTRICT')
        )
    )
    songs: list['Song'] = Relationship()

class Song(SQLModel, table=True):
    __tablename__ = 'song'
    id: int = Field(primary_key=True)
    title: str
    album: Optional[UUID] = Field(
        sa_column=Column(
            ForeignKey('album.id', onupdate='CASCADE', ondelete='CASCADE')
        )
    )
    featuring: Optional[str] = Field(
        sa_column=Column(
            ForeignKey('artist.name', onupdate='CASCADE', ondelete='RESTRICT')
        )
    )
    track_details: dict = Field(default={}, sa_type=JSON)

class User(SQLModel, table=True):
    __tablename__ = 'user'
    username: str = Field(primary_key=True, sa_type=String(collation='NOCASE'))
    email: str = Field(unique=True)
    favorite_song: Optional[int] = Field(
        sa_column=Column(
            ForeignKey('song.id', onupdate='CASCADE', ondelete='SET NULL')
        )
    )
    date_joined: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={'onupdate': utc_now}
    )

class Subscription(SQLModel, table=True):
    __tablename__ = 'subscription'
    subscriber: str = Field(
        sa_column=Column(
            ForeignKey('user.email', onupdate='CASCADE', ondelete='RESTRICT'),
            primary_key=True
        )
    )
    to_artist: Optional[str] = Field(
        sa_column=Column(
            ForeignKey('user.username', onupdate='CASCADE', ondelete='RESTRICT'),
            primary_key=True
        )
    )
    tier: SubscriptionTier = SubscriptionTier.BASIC
```
</details>
</br>
Now let's look at how DAOModel improves the code with its field shortcuts and other features:

### Table Naming

```diff
- class Artist(SQLModel, table=True):
+ class Artist(DAOModel, table=True):
-     __tablename__ = 'artist'
```

DAOModel automatically converts class names to snake_case for table names (using `normalized_name()`).
No need to manually specify `__tablename__` unless you want a custom name.

For example, the class named `LivePerformanceEvent` will automatically use the table name `live_performance_event`.
```diff
- class LivePerformanceEvent(SQLModel, table=True):
+ class LivePerformanceEvent(DAOModel, table=True):
-     __tablename__ = 'live_performance_event'
```

Convenience methods provide access to both the normalized and documentation-friendly names:

```python
LivePerformanceEvent.normalized_name()  # Returns 'live_performance_event'
Album.normalized_name()                 # Returns 'album'
LivePerformanceEvent.doc_name()         # Returns 'Live Performance Event'
Album.doc_name()                        # Returns 'Album'
```

### Identifier
```diff
- name: str = Field(primary_key=True)
+ name: Identifier[str]
```

The `Identifier` typing makes defining primary keys more concise and readable
by allowing the column to be entirely defined within the typing.
Often, your Primary Keys have no other configuration
which means that using `Identifier` eliminates the need for `Field`, resulting in a simple definition.
```python
class Artist(DAOModel, table=True):
    name: Identifier[str]
    ...

class Song(DAOModel, table=True):
    id: Identifier[int]
    ...

class User(DAOModel, table=True):
    username: Identifier[str]
    ...
```

If you do still need additional configuration, you are free to use Field in combination with Identifier:
```python
class Album(DAOModel, table=True):
    id: Identifier[UUID] = Field(default_factory=uuid4)
```
> **Note:** You may include `primary_key=True` if you wish even though it would be redundant.

Composite primary keys may also be achieved with `Identifier`:
```python
class LivePerformanceEvent(DAOModel, table=True):
    venue: Identifier[str]
    event_date: Identifier[datetime]
    ...
```

Also seen in the above example, any type (that is supported by your DB) may be defined as an `Identifier`.

For information on how to work with primary keys in your code (such as getting primary key values or names),
scroll down to the [Primary Key Management](model.md#primary-key-management) section.
Otherwise, let's talk about UUIDs more as it may be an `Identifier` type you find yourself using often.

### UUID
```diff
- id: UUID = Field(primary_key=True, default_factory=uuid4)
+ id: Identifier[UUID]
```

As previously mentioned, when using DAOModel, you may define your primary keys with `Identifier`.
But DAOModel also automatically handles specific field types, one of which being `UUID`.

Whenever DAOModel sees a field type of `UUID` it automatically configures it to generate a new uuid by default.
This helps to achieve our goal of short and sweet code that can quickly be read and understood
since it is unburdened by additional technical details. Another example of this is the dict type.

### Dict
```diff
- track_details: dict = Field(default={}, sa_type=JSON)
+ track_details: dict = Field(default={})
```
If you wish to store a dict within your database table, you will need to set the sa (SQLALchemy) type to JSON to
communicate how the database should store this special data type.
DAOModel does this for you automatically. Not only do these shortcuts and automations reduce your code,
they may allow for your field definition to be reduced even further.
Such is the case in our `Song` model which no longer needs to explicitly configure multiple options.
Since default is the only argument, native vanilla SQLModel functionality allows us to skip the `Field` function call.
```python
class Song(DAOModel, table=True):
    ...
    track_details: dict = {}
```
> **Note:** SQLModel has many more great QoL features over SQLAlchemy.
> If you were unaware of this one, I recommend you read up on its [Features](https://sqlmodel.tiangolo.com/features/).

### Case-Insensitive Strings
```diff
- username: str = Field(primary_key=True, sa_type=String(collation='NOCASE'))
+ username: no_case_str = Field(primary_key=True)
```

DAOModel supports automatic collation for case-insensitive string matching using the no_case_str marker type.
Whenever DAOModel sees a field type of no_case_str, it automatically configures the database column to use
COLLATE NOCASE (or the equivalent collation clause for your database).
This allows you to query string fields without worrying about case sensitivity.
```python
class User(DAOModel, table=True):
    username: no_case_str = Field(primary_key=True)
```

### Model References
```diff
- artist: str = Field(foreign_key='artist.name')
+ artist: Artist
```

_Model References_ are a great feature of DAOModel,
and they make the biggest difference when it comes to simplifying your model definitions.
In vanilla SQLModel, Foreign Keys must be explicitly mapped to the appropriate table column.
In DAOModel, the mapping is automated when you set the field type be one of your DAOModel models.
The table column type in the database will automatically match the Identifier type of the referenced model.
This means that in the above example, the Python type is `Artist` but the actual type stored will be `str`.

But that is not where it ends. DAOModel configures cascades for you as well!

#### CASCADE Updates/Deletes
```diff
- artist: str = Field(
-     sa_column=Column(
-         ForeignKey('artist.name', onupdate='CASCADE', ondelete='CASCADE')
-     )
- )
+ artist: Artist
```

If you are familiar with relational databases, you likely enjoy the ease of cascading changes to your data.
This means that if table _A_ references table _B_. Then any change to table _B_ will also reflect in table _A_.
While this may seem natural to some, it is not the default behavior of your SQLAlchemy tables.
DAOModel aims to change that by making cascades standard for all referenced fields.
This eliminates the complex SQLAlchemy column configuration required when using vanilla SQLModel.

But what's that you say, `ondelete='CASCADE' sounds dangerous!`? Don't worry, DAOModel has a solution to that!

#### Protected
```diff
- artist: str = Field(
-     sa_column=Column(
-         ForeignKey('artist.name', onupdate='CASCADE', ondelete='RESTRICT')
-     )
- )
+ artist: Protected[Artist]
```

If you wish to instead restrict the deletion of referenced Foreign Key columns,
simply use the Protected typing along with the model reference.
That will set `ondelete=RESTRICT` to ensure the foreign row cannot be deleted if it is referenced by existing data.

Or maybe you want to allow deletion but preserve the row referencing the deleted data.
In SQLAlchemy, that would be done by setting `ondelete='SET NULL'`.

#### SET NULL
```diff
- favorite_song: Optional[int] = Field(
-     sa_column=Column(
-         ForeignKey('song.id', onupdate='CASCADE', ondelete='SET NULL')
-     )
- )
+ favorite_song: Optional[Song]
```

With DAOModel, the `SET NULL` behavior is assumed when you mark the reference as `Optional`.
> **Note:** `Optional` will be covered more [below](model.md#required-vs-optional)

#### Custom Behavior
```diff
- album: Optional[UUID] = Field(
-     sa_column=Column(
-         ForeignKey('album.id', onupdate='CASCADE', ondelete='CASCADE')
-     )
- )
+ album: Optional[Album] = Field(foreign_key='auto', ondelete='CASCADE')
```
If the default configurations don't meet your needs, you may combine DAOModel references with the SQLModel Field
to achieve your wanted functionality while still keeping your code concise and readable.
In the above example, we wish to make the column Optional but have ondelete _CASCADE_ rather than _SET NULL_.
> **Note:** The `foreign_key` argument here is actually redundant but is required to set `ondelete='CASCADE'`
> so we just set it to _'auto'_ to indicate that the mapping is automatically taken care of.
> Regardless of this value, DAOModel will set the foreign_key based on the typing.

Another option is to use the `ReferenceTo` class which provides
a clean way to specify the target column and any additional configuration options.

#### ReferenceTo
```diff
- album: Optional[UUID] = Field(
-     sa_column=Column(
-         ForeignKey('album.id', onupdate='CASCADE', ondelete='CASCADE')
-     )
- )
+ album: Optional[Album] = ReferenceTo(Album.id, ondelete='CASCADE')
```

`ReferenceTo` is a powerful feature that allows you to explicitly define foreign key mappings.
It accepts a target parameter which can be:

- The foreign column as seen above
- A string in the format 'table.column'
- Excluded completely (as long as the typing defines the model)

ReferenceTo is particularly useful if you:

- Have a circular dependency between files/models (or even within a single model)
```python
class Song(DAOModel, table=True):
    id: Identifier[int]
    next_song: Optional[int] = ReferenceTo('song.id')
```
- Are referencing a non-Identifier field
```python
class Subscription(DAOModel, table=True):
    ...
    subscriber: Identifier[str] = ReferenceTo(User.email)
    ...
```
- Want the typing to reflect the stored type (`int`, `str`, etc.) rather than the model type (`Album`, `Artist`, etc.)
```python
artist: str = ReferenceTo(Artist.name)
```
- Need to configure the field behavior beyond the defaults
```python
album: Optional[Album] = ReferenceTo(ondelete='CASCADE')
```
- Prefer the SQLModel style of defining the relationship but still want the cascades/etc.
```python
favorite_song: Optional[int] = ReferenceTo(Song.id)
```

ReferenceTo will help cover most of your relationship scenarios,
but as always, you can use Field or Relationship if you'd rather.
Although, in some cases, even that is unnecessary.

#### Reference Collections
```diff
- albums: list['Album'] = Relationship()
+ albums: list['Album']
```

A subtle difference, but DAOModel detects collections of references for you.
SQLModel requires the Relationship be explicitly defined.
This feature can reduce line length as well as eliminate an additional import.

Now let's move on to discuss Optional fields more.

### Required vs Optional
DAOModel handles optional fields slightly differently from vanilla SQLModel.
In your SQLModel definitions non-primary-key fields are nullable by default.
This means that to make a field required, you must add `nullable=False` as an argument to the Field.
DAOModel takes a more explicit approach. All fields with the Optional typing are `nullable=True`
while any field not typed with Optional is `nullable=False` meaning it is required.

### Modifier Order
We have mentioned a few typings which we refer to as _Modifiers_ which include:

- Identifier
- Protected
- Optional

These modifiers can be combined to suite your needs, but they must be written in the correct order (as listed above).
The Song and Subscription models showcase these combinations:
```python
class Song(DAOModel, table=True):
    ...
    featuring: Protected[Optional[Artist]]
    ...

class Subscription(DAOModel, table=True):
    owner: Identifier[Protected[User]]
    to_artist: Identifier[Protected[Optional[Artist]]]
    ...
```

### Timestamp Fields
```diff
- date_joined: datetime = Field(default_factory=utc_now)
+ date_joined: datetime = CurrentTimestampField
- updated_at: datetime = Field(
-     default_factory=utc_now,
-     sa_column_kwargs={'onupdate': utc_now}
- )
+ updated_at: datetime = AutoUpdatingTimestampField
```

Timestamp fields with proper UTC handling are simplified to single-line declarations.

Now that we've explored each of DAOModel's field shortcuts individually, let's see how they work together in real-world scenarios.

### Complete Example

The following example demonstrates how DAOModel's features combine to create clean, readable model definitions.
This shows how DAOModel can significantly reduce your code, making your models easier to understand and maintain.

Here's the complete code using DAOModel:
```python
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from daomodel import DAOModel
from daomodel.fields import no_case_str, Identifier, Protected, CurrentTimestampField, AutoUpdatingTimestampField, Field, ReferenceTo

class SubscriptionTier(Enum):
    BASIC = 'basic'
    PREMIUM = 'premium'
    ULTIMATE = 'ultimate'

class Artist(DAOModel, table=True):
    name: Identifier[str]
    bio: Optional[str]
    albums: list['Album']

class LivePerformanceEvent(DAOModel, table=True):
    venue: Identifier[str]
    event_date: Identifier[datetime]
    artist: Artist

class Album(DAOModel, table=True):
    id: Identifier[UUID]
    title: str
    artist: Protected[Artist]
    songs: list['Song']

class Song(DAOModel, table=True):
    id: Identifier[int]
    title: str
    album: Optional[Album] = ReferenceTo(ondelete='CASCADE')
    featuring: Protected[Optional[Artist]]
    track_details: dict = {}

class User(DAOModel, table=True):
    username: Identifier[no_case_str]
    email: str = Field(unique=True)
    favorite_song: Optional[Song]
    date_joined: datetime = CurrentTimestampField
    updated_at: datetime = AutoUpdatingTimestampField

class Subscription(DAOModel, table=True):
    subscriber: Identifier[Protected[str]] = ReferenceTo(User.email)
    to_artist: Identifier[Protected[Optional[Artist]]]
    tier: SubscriptionTier = SubscriptionTier.BASIC
```

We've discussed many helpful shortcuts provided by DAOModel when defining your models.
Please do not feel like you have to use these. Use the ones you like and use vanilla SQLModel for everything else.
Gain, DAOModel is an extension of SQLModel and is designed to improve your coding experience, not completely change it.

### Caveats

DAOModel makes a few changes to how models are defined, so in some situations
inheriting from DAOModel instead of SQLModel could break existing functionality.
We have already mentioned some of these but will reiterate here.

#### Table Names
Table names are configured to be snake_case which differs from SQLModel.
This won't matter for new tables, but existing SQLModel tables may not align once switched to DAOModel.

For example,
```python
class UserAccount(SQLModel, table=True):
    ...
```
creates a table named `useraccount`

while
```python
class UserAccount(DAOModel, table=True):
    ...
```
won't reuse the `useraccount` table but will instead make one named `user_account`.

If this causes problems, such as when refactoring your existing project to use DAOModel,
you may instead import the backwards compatible DAOModel class:
```python
from daomodel.backwards_compatibility import DAOModel
```

## Working with DAOModel Instances

So far, we've focused on how DAOModel simplifies the definition of database models.
But the benefits don't stop there! Once you've defined your models, DAOModel provides a rich set of
methods for working with model instances, making it easier to access and manipulate your data.

This page covers the various methods available on DAOModel instances and classes.
These methods make it easier to work with your models and perform common operations.

### Database Actions
We've already discussed how a DAO can be automatically created to instantly provide CRUD operations for your models.
All of that documentation is found on the [DAO](dao.md) page. For the sake of our example code,
let's assume you do not have a populated database to just [Read](dao.md#read) into memory.

### Constructing a Model Instance
With vanilla SQLModel, you construct a model instance the same way you would any other Class.
```python
artist = Artist(name='The Beatles')
show = LivePerformanceEvent(venue='Rooftop of Apple Records', event_date=datetime(1969, 1, 30), artist=artist.name)
```

In addition to that, DAOModel provides the [Create](dao.md#create) functionality.
```python
artist = daos[Artist].create('The Beatles')

# create with additional field values
user = daos[User].create_with(username='cod', email='cod@theinternet.com')

# create with an auto-generated UUID
album = daos[Album].create_with(title='Abbey Road', artist=artist.name)

# create using an auto-incremented id
song = daos[Song].create(next_id())

subscription = daos[Subscription].create_with(subscriber=user.email, tier=SubscriptionTier.PREMIUM)
```

### Primary Key Management

::: daomodel.DAOModel.get_pk
```python
Artist.get_pk()  # Returns the primary key column(s), in this case, the artist.name column
```

::: daomodel.DAOModel.get_pk_names
```python
Artist.get_pk_names()  # Returns ['name']
LivePerformanceEvent.get_pk_names()  # Returns ['venue', 'event_date']
Album.get_pk_names()  # Returns ['id']
```

::: daomodel.DAOModel.get_pk_values
```python
artist.get_pk_values()  # Returns ('The Beatles',)
show.get_pk_values()  # Returns ('Rooftop of Apple Records', datetime(1969, 1, 30))
```

::: daomodel.DAOModel.get_pk_dict
```python
user.get_pk_dict()  # Returns {'username': 'cod'}
subscription.get_pk_dict()  # Returns {'subscriber': 'cod@theinternet.com', 'to_artist': None}
```

### Foreign Key Management

::: daomodel.DAOModel.get_fks
Assuming the [above example code](#complete-example):
```python
Album.get_fks()  # Returns {Artist.name}
Song.get_fks()  # Returns {Album.name, Artist.name}
```

::: daomodel.DAOModel.get_fk_properties
Assuming the [above example code](#complete-example):
```python
Album.get_fk_properties()  # Returns {Album.artist}
Song.get_fk_properties()  # Returns {Song.album, Song.featuring}
```

::: daomodel.DAOModel.get_references_of
Assuming the [above example code](#complete-example):
```python
Song.get_references_of(Artist)  # Returns {Song.featuring}
User.get_references_of(Song)  # Returns {User.favorite_song}
```

### Property Access

Property access methods allow you to interact with model properties in a flexible and powerful way.
These methods provide filtering options and different ways to access property data.

::: daomodel.DAOModel.get_properties

::: daomodel.DAOModel.get_property_names

::: daomodel.DAOModel.get_property_values

::: daomodel.DAOModel.get_value_of
```python
album.get_value_of('artist')  # 'The Beatles'
album.get_value_of(Album.title)  # 'Abbey Road'
```
This method provides a convenient way to get the value of a single property from a model instance.
It's particularly useful when you need to dynamically access a specific field value without dealing with dictionaries.

::: daomodel.DAOModel.get_values_of
This is useful when you need a subset of specific known properties rather than filtering based on conditions.
Column references and column names can be combined, such as in the following function call.
```python
show.get_values_of(LivePerformanceEvent.venue, 'artist')
# {'venue': 'Rooftop of Apple Records', 'artist': 'The Beatles'}
```

### Model Manipulation

::: daomodel.DAOModel.set_values
```python
song.set_values(title='Oh! Darling', album=album.id)
```

::: daomodel.DAOModel.copy_model
```python
other_song = daos[Song].create(next_id())
# Copy all non-PK values from one song to another
other_song.copy_model(song)

another_song = daos[Song].create_with(next_id(), title='Golden Slumbers')
# Copy specific fields only
another_song.copy_model(song, 'album')
```

### String Representation and Equality

::: daomodel.DAOModel.__eq__
```python
other_artist = Artist(name='The Beatles', bio='The Fab Four')

# Equality is based on primary key only
return artist == other_artist
# Returns True even though one has a bio because they share the same primary key 
```

::: daomodel.DAOModel.__str__
```python
# String representation is based on primary key
str(user)  # Returns 'cod'

# For composite keys
str(subscription)  # Returns '('cod', None)'
```

## Next Steps

You now understand how to define Models as well as create a [DAO](dao.md) layer for said models.
The next logical step is to create a [Service Layer](service.md) to provide methods for interacting with your models.
Continue to the next page to learn all about the BaseService offered by DAOModel.
