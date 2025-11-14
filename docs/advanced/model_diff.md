# Model Comparison and Diffing

Model Comparison isn't something you'll use in every project,
but when you do need it, you'll love the built-in integration.

_Model Comparison_ refers to examining differing data from a **DAOModel**.
Said data could be multiple entries or different versions of a single entry.

There are many use cases for comparing data:

- Highlight differences between model entries
- Track changes to an object over time
- Resolve conflicts when multiple users modify the same data
- Merge several data sources into one

This multifunctional tool consists of several components.
But everything stems from the `ModelDiff` class, so let's start there!

## ModelDiff

Imagine we are shopping for a new vehicle and wish to compare options:
```python
class EV(DAOModel, table=True):
    make: Identifier[str]
    model: Identifier[str]
    drivetrain: str
    acceleration: float
    battery_capacity: int
    range: int
    charging_speed: int
    screen_size: float
    price: int

model_3 = ev_dao.create_with(make='Tesla', model='Model 3',
    drivetrain='AWD',
    acceleration=4.2,
    battery_capacity=82,
    range=333,
    charging_speed=250,
    screen_size=15,
    price=42990
)

mach_e = ev_dao.create_with(make='Ford', model='Mustang Mach-E',
    drivetrain='AWD',
    acceleration=4.8,
    battery_capacity=91,
    range=310,
    charging_speed=150,
    screen_size=15.5,
    price=42995
)

bolt = ev_dao.create_with(make='Chevrolet', model='Bolt EUV',
    drivetrain='FWD',
    acceleration=7.0,
    battery_capacity=65,
    range=247,
    charging_speed=55,
    screen_size=10.2,
    price=28995
)

r1t = ev_dao.create_with(make='Rivian', model='R1T',
    drivetrain='AWD',
    acceleration=3.0,
    battery_capacity=135,
    range=328,
    charging_speed=200,
    screen_size=16,
    price=73900
)
```

Since we have a model, and some entries, a **ModelDiff** can be used to make a comparison between the entries.
ModelDiff is a fairly simple class to use. First, we construct a new one using two DAOModel instances.
```python
diff = ModelDiff(model_3, mach_e)
```
> !!! tip
>     This feature is designed and tested for comparing like models but, in theory, could work for unlike models.
>     For example, if the models are fairly similar, we could compare an EV, to a Hybrid, or ICE Vehicle.

Now that we have a diff object, we can get the values for each item:
```python
if 'price' in diff:  # returns true if the entries had different prices
    diff.get_left('price')  # returns the price of the Model 3
    diff.get_right('price')  # returns the price of the Mach E
    diff.all_values('price')  # returns an array of each value i.e. [42990, 42995]
```
> !!! info
>     Under the hood, a ModelDiff is simply a `dict` with additional functions.
>     Which means it is naturally compatible with other services such as serialization.

Viewing values isn't anything revolutionary. The main purpose of a ModelDiff is to compare the values,
but to do that, we must understand Preferences.

### Preference

#### Preference Enum

A **Preference** is an Enum with the following potential values:

- **LEFT**: Indicates preference for the _left_ side value
- **RIGHT**: Indicates preference for the _right_ side value
- **NEITHER**: Indicates that neither value is preferred
- **BOTH**: Indicates that both values are equally preferable
- **NOT_APPLICABLE**: Indicates that a preference does not apply in the given context

Calling `get_preferred` on a ModelDiff will return the Preference.

::: daomodel.model_diff.ModelDiff.get_preferred
```python
preferred_acceleration = diff.get_preffered('acceleration')
preferred_range = diff.get_preffered('range')
```

Testing the code above will result in a `NotImplementedError`
because ModelDiff does not automatically know your preferences.
To progress, preferences must be defined through Preference Rules.

### Preference Rules

Rules are passed in through the ModelDiff constructor as keyword arguments.
Each preference rule is specific to a field.
```python
diff = ModelDiff(model_3, mach_e, range=max, price=min)
```

Python allows for passing an entire `dict` as `**kwargs`.
This is especially convenient if we have many rules. 
```python
ev_rules = {
    # Assign a field to always be a specific Preference
    'make': Preference.NOT_APPLICABLE,
    'model': Preference.NOT_APPLICABLE,
    'battery_capacity': Preference.NOT_APPLICABLE,

    # Use an existing function to return the preferred value
    'range': max,
    'charging_speed': max,
    'screen_size': max,

    # Both min and max refer to the builtin functions
    'acceleration': min,
    'price': min,

    # Write your own rule function
    'drivetrain': custom_drivetrain_rule
}

diff = ModelDiff(model_3, mach_e, **ev_rules)
```

A PreferenceRule is one of two things:
 - A hardcoded Preference (LEFT, RIGHT, etc)
 - A function that calculates the Preference
> !!! tip
>     A PreferenceRule could technically be a static value (such as True or 'specific value')
>     but that feature is not fully developed. Let me know if you want that work completed!

#### Custom Rule Function

Let's take a look at `custom_drivetrain_rule` used above:
```python
# The ModelDiff provides the differing values to the custom rule as an argument
def custom_drivetrain_rule(*values: str) -> Preference | str:
    bad = {'FWD', 'RWD', '2WD'}  # these values are bad, we would never prefer them
    good = {'AWD', '4WD'}  # these are the values we want to have (we consider them equally good)

    # Find all the values that are good and thus should be preferred
    good_values = [v for v in values if v in good]

    match len(good_values):
        case 0:  # no good values
            return Preference.NEITHER
        case 1:  # only one of the values is good
            return good_values[0]  # return that value
        case _:  # multiple good values
            return Preference.BOTH
```

Notice that the parameter is a variable number of arguments.
Alternatively, named arguments or a single list argument are also supported.
```python
def custom_drivetrain_rule(left: str, right: str):
```
```python
def custom_drivetrain_rule(values: list[str]):
```
It all depends on your style, the ModelDiff code will adjust the function call as needed.

The other thing to note is that the function can return either a Preference or one of the string values.
Look again at the code, if there are 0 "good values", then a Preference of **NEITHER** is returned.
However, if there is 1 "good value", then that value is returned.
Even though the rule returns a string, that string will be translated to the appropriate Preference automatically.
```python
preference = diff.get_preferred('drivetrain')  # returns Preference.Left
```
!!! info
    This value conversion is what allows you to use existing functions like `max` and `min`.

Let's take another look at those rules and see how we can trim them down.

#### Excluding Rules

Some fields are set to `Preference.NOT_APPLICABLE`. We won't ever be comparing them, so let's just exclude those rules.
```diff
ev_rules = {
-   'make': Preference.NOT_APPLICABLE,
-   'model': Preference.NOT_APPLICABLE,
-   'battery_capacity': Preference.NOT_APPLICABLE,

    'range': max,
    'charging_speed': max,
    'screen_size': max,

    'acceleration': min,
    'price': min,

    'drivetrain': custom_drivetrain_rule
}
```
> !!! warning
>     The rules need not be all-inclusive, but do keep in mind that trying to
>     compare without an applicable rule will result in a `NotImplementedError`

#### Default Rule

Notice that multiple fields use the `max` function as a rule?
```python
ev_rules = {
    'range': max,
    'charging_speed': max,
    'screen_size': max,

    'acceleration': min,
    'price': min,

    'drivetrain': custom_drivetrain_rule
}
```

_Bigger_ isn't always _better_, but looks like most of the time it is.
If we set a default rule of `max` then we need not explicitly assign some of these rules.
```diff
ev_rules = {
-   'range': max,
-   'charging_speed': max,
-   'screen_size': max,
+   'default': max,

    'acceleration': min,
    'price': min,

    'drivetrain': custom_drivetrain_rule
}
```
!!! danger
    Be careful with _default_ as those **NOT_APPLICABLE** fields we removed
    (make, model, batter_capacity) will now use the default rule of `max`

!!! tip
    Now that your rules are reduced, maybe you can fit it all within the constructor!
```python
diff = ModelDiff(
    model_3, mach_e,
    default=max,
    acceleration=min,
    price=min,
    drivetrain=custom_drivetrain_rule
)
```

### Including Primary Key Values

Often the PK values are **NOT APPLICABLE**. Such is the case for our EV example.
For this reason, the PK is automatically excluded from the diff all together.
If we wish to include the PK, we simply set `include_pk=True`. Let's look at that in action.

Consider our EV data:

| Make      | Model          | Drivetrain | 0–60 mph (s) | Battery (kWh) | Range (mi) | Charging Speed (kW) | Screen Size (in) | Price ($) |
|-----------|----------------|------------|--------------|---------------|------------|---------------------|------------------|-----------|
| Tesla     | Model 3        | AWD        | 4.2          | 82            | 333        | 250                 | 15.0             | 42,990    |
| Ford      | Mustang Mach-E | AWD        | 4.8          | 91            | 310        | 150                 | 15.5             | 42,995    |
| Chevrolet | Bolt EUV       | FWD        | 7.0          | 65            | 247        | 55                  | 10.2             | 28,995    |
| Rivian    | R1T            | AWD        | 3.0          | 135           | 328        | 200                 | 16.0             | 73,900    |

Say we have a preference of Vehicle Make: Tesla > Ford > Everything else.
We can define a PreferenceRule for that.
```python
ev_rules = {
    'make': lambda values: (
        'Tesla' if 'Tesla' in values else
        'Ford' if 'Ford' in values else
        Preference.NOT_APPLICABLE
    ),
    ...
}

diff = ModelDiff(model_3, mach_e, **ev_rules)
```

However, since _make_ is a primary key, it is not included within the diff.
This means that `get_preferred` will raise a `KeyError` which is remedied with the include_pk flag.
```python
diff = ModelDiff(model_3, mach_e, include_pk=True, **ev_rules)
diff.get_preferred('make')  # returns Preference.LEFT since Tesla is preferred over Ford
```
> !!! warning
>     A KeyError could still be thrown if the make values are the same, thus not included within the diff.
>     You can avoid this error by first checking `if 'make' in diff:`.

Passing the pk_flag and rules each time we wish to make a comparison is too repetitive.
Python allows us to avoid duplicate code by overriding the ModelDiff class.

### Custom ModelDiff Class

**ModelDiff** is designed for ease of customization. Let's consider refactoring our code from above.
```python
# Override the ModelDiff class and support type hints by specifying the EV DAOModel
class EVDiff(ModelDiff[EV]):
    def __init__(self, left: EV, right: EV):
        # Inject the flag and rule arguments that will stay constant
        super().__init__(left, right, include_pk=True,
            default=max,

            make=lambda values: (
                'Tesla' if 'Tesla' in values else
                'Ford' if 'Ford' in values else
                Preference.NOT_APPLICABLE
            ),
            model=Preference.NOT_APPLICABLE,

            acceleration=min,
            price=min,
            drivetrain=custom_drivetrain_rule
        )

# We no longer need to pass the rules and pk flag each time
diff1 = EVDiff(model_3, mach_e)
diff2 = EVDiff(mach_e, bolt)
diff3 = EVDiff(model_3, r1t)
```

See how this extra class definition can clean up the logic elsewhere in your code?
More than that, a custom ModelDiff class can allow for functionality not possible otherwise,
such as determining a preference based on another field value.
This is essential in comparing our EVCharger models:

**Model**:
```python
class EVCharger(DAOModel, table=True):
    brand: Identifier[str]
    model: Identifier[str]
    connector_type: str
    cord_length: int
    max_amps: int
    voltage: int
    bidirectional: bool
    wifi: bool
    portable: bool
```

**Data**:

| Brand  | Model                    | Connector | Cord Length | Max Amps | Voltage | Bidirectional | WiFi | Portable |
|--------|--------------------------|-----------|-------------|----------|---------|---------------|------|----------|
| Tesla  | Mobile Connector         | NACS      | 20 ft       | 32       | 240     | No            | No   | Yes      |
| Tesla  | Wall Connector           | NACS      | 24 ft       | 48       | 240     | No            | Yes  | No       |
| Tesla  | Universal Wall Connector | J1772     | 24 ft       | 48       | 240     | Yes           | Yes  | No       |
| Ford   | Connected Charge Station | J1772     | 20 ft       | 48       | 240     | No            | Yes  | No       |
| Ford   | Charge Station Pro       | J1772     | 25 ft       | 80       | 240     | Yes           | Yes  | No       |
| GM     | Dual Level Charger       | J1772     | 22 ft       | 32       | 240     | No            | No   | Yes      |
| GM     | PowerUp 2                | J1772     | 25 ft       | 48       | 240     | No            | Yes  | No       |
| GM     | Energy PowerShift        | J1772     | 25 ft       | 80       | 240     | Yes           | Yes  | No       |
| Rivian | Portable Charger (NACS)  | NACS      | 18 ft       | 32       | 240     | No            | No   | Yes      |
| Rivian | Portable Charger (J1772) | J1772     | 18 ft       | 32       | 240     | No            | No   | Yes      |
| Rivian | Wall Charger (NACS)      | NACS      | 24 ft       | 48       | 240     | No            | No   | No       |
| Rivian | Wall Charger (J1772)     | J1772     | 24 ft       | 48       | 240     | No            | No   | No       |

**Rules**:
```python
def prefer_true(left, right):
    if left:
        return Preference.LEFT
    elif right:
        return Preference.RIGHT
    return Preference.NEITHER

rules = {
    'default': max,
    'connector_type': Preference.NOT_APPLICABLE,
    'bidirectional': prefer_true,
    'wifi': prefer_true,
    'portable': prefer_true,
}

class EVChargerDiff(ModelDiff[EVCharger]):
    def __init__(self, left: EVCharger, right: EVCharger):
        super().__init__(left, right, **rules)
```

When it comes to `cord_length`, longer is better.
But if the charger is portable then we do not care so much about its length.
In that case, the preference for `cord_length` should really be **NOT_APPLICABLE**.
To achieve this, we will override the `get_preferred` function.

```python
class EVChargerDiff(ModelDiff[EVCharger]):
    def __init__(self, left: EVCharger, right: EVCharger):
        super().__init__(left, right, **rules)

    def get_preferred(self, field: str):
        if field == 'cord_length':
            if self.left.portable or self.right.portable:
                return Preference.NOT_APPLICABLE

        # If not portable, or the field in question is not cord_length, then call the original code.
        return super().get_preferred(field)
```

See how overriding gives more flexibility than passing in rules?
We now have visibility of the full models, not just their value for a single field.
That is just one example of how powerful custom ModelDiff classes can be.

DAOModel actually has a couple of these custom ModelDiff classes packaged with it. For example, **ChangeSet**.

## ChangeSet

A ChangeSet is used to view a set of changes on a model entry (similar to a Pull Request for a code change).
When working with a ChangeSet, the goal is to apply the target changes to a baseline object.
During this process, we want some of the baseline properties to be overwritten, but others should be preserved.
Preference Rules dictate which values will be a part of the final result.

Since a ChangeSet is an extension of ModelDiff it has the functionality listed [above](#modeldiff) plus a couple modifications:

- `get_baseline(field)` and `get_target(field)` mimic `get_left` and `get_right` respectively, providing more meaningful naming
- `modified_in_baseline` and `modified_in_target` properties list the fields that are not their default value
- `get_preferred(field)` now also contains logic that prefers populated values, especially modified values

| Baseline | Target   | Preference       |
|----------|----------|------------------|
| No value | Default  | Preference.RIGHT |
| No value | Modified | Preference.RIGHT |
| Default  | No value | Preference.LEFT  |
| Default  | Modified | Preference.RIGHT |
| Modified | No value | Preference.LEFT  |
| Modified | Default  | Preference.LEFT  |
| Modified | Modified | Preference.Both  |

!!! note
    The table excludes scenarios where both values are `None`, or both values are the default property value.
    In each case, those values would match and therefore not be included as a _diff_

### Usage

Below, we have the model for a user-submitted Point-of-Interest app:
```python
class POI(DAOModel, table=True):
    name: Identifier[str]
    category: Optional[str]
    description: Optional[str]
    website: Optional[str]
    latitude: float
    longitude: float
    ada_compliant: Optional[bool]
    latest_condition: Optional[str]

poi_dao.create_with(
    name='Niagara Falls',
    description='A world-famous trio of waterfalls straddling the Canada-U.S. border.',
    latitude=43.0815,
    longitude=-79.0642
)
```

Users can add new POIs or update existing ones. Since a POI already exists for Niagara Falls,
a ChangeSet is used to allow someone to provide new information.

```python
# Retrieve the existing Niagara Falls entry
saved_poi = poi_dao.get('Niagara Falls')

# Create an entry from the user's input
user_entry = poi_dao.create_with(
    name='Niagara Falls',
    category='Nature',
    website='https://www.nps.gov/nifa',
    ada_compliant=True,
    latest_condition='Fireworks tonight!',
    insert=False
)

# The original baseline object is the first arg, the new target data is the last arg
change_set = ChangeSet(saved_poi, user_entry)
```
> !!! info
>     [What is insert=False?](../usage/dao.md#daomodel.dao.DAO.create_with)

ChangeSets typically have a fairly standard workflow:

1. Create a ChangeSet
2. Resolve all preferences
3. Apply the changes

i.e. `ChangeSet(baseline, target).resolve_preferences().apply()`

### Resolving Preferences

The `resolve_preferences()` function uses [get_preferred()](#daomodel.model_diff.ModelDiff.get_preferred)
to decide which values are worth keeping.

::: daomodel.model_diff.ChangeSet.resolve_preferences
```python
change_set.resolve_preferences()
```

Essentially, what this function does is evaluate the diff and eliminate each value that isn't _preferred_.
Again, the determined preference between values can be configured by providing preference rules.

The new Niagara Falls input contains a value for _category_ but the old input does not.
Therefore, the _target_ (aka _right_) value is preferred.
Here is the full result from changes being applied:

|          | Name          | Category | Description                                                          | Website                  | Latitude | Longitude | ADA  | Condition          |
|----------|---------------|----------|----------------------------------------------------------------------|--------------------------|----------|-----------|------|--------------------|
| baseline | Niagara Falls |          | A world-famous trio of waterfalls straddling the Canada-U.S. border. |                          | 43.0815  | -79.0642  |      |                    |
| target   | Niagara Falls | Nature   |                                                                      | https://www.nps.gov/nifa |          |           | True | Fireworks tonight! |
| result   | Niagara Falls | Nature   | A world-famous trio of waterfalls straddling the Canada-U.S. border. | https://www.nps.gov/nifa | 43.0815  | -79.0642  | True | Fireworks tonight! |

This first change contained no conflicts. Using the result as our new baseline, let's accept another user submission.
Each property has a value, so we can specify preference rules to avoid troublesome conflicts.

```python
class POIChangeSet(ChangeSet[POI]):
    def __init__(self, baseline: POI, target: POI):
        super().__init__(baseline, target,
            default=Preference.LEFT,  # Unless specified below, prefer the existing data
            ada_compliant=lambda b, t: False,  # Don't prefer a value of True unless confirmed by moderator
            latest_condition=Preference.RIGHT  # Always prefer the new condition value
        )

# Retrieve the existing Niagara Falls entry
saved_poi = poi_dao.get('Niagara Falls')

# Create an entry from the user's input
user_entry = poi_dao.create_with(
    name='Niagara Falls',
    category='Construction, avoid!',
    ada_compliant=False,
    latest_condition='Construction limits viewing platforms.',
    insert=False
)

ChangeSet(saved_poi, user_entry).resolve_preferences().apply()
```

With the defined preference rules, here are the results:

|          | Name          | Category               | Description                                                          | Website                  | Latitude | Longitude | ADA   | Condition                              |
|----------|---------------|------------------------|----------------------------------------------------------------------|--------------------------|----------|-----------|-------|----------------------------------------|
| baseline | Niagara Falls | Nature                 | A world-famous trio of waterfalls straddling the Canada-U.S. border. | https://www.nps.gov/nifa | 43.0815  | -79.0642  | True  | Fireworks tonight!                     |
| target   | Niagara Falls | 'Construction, avoid!' |                                                                      |                          |          |           | False | Construction limits viewing platforms. |
| result   | Niagara Falls | Nature                 | A world-famous trio of waterfalls straddling the Canada-U.S. border. | https://www.nps.gov/nifa | 43.0815  | -79.0642  | False | Construction limits viewing platforms. |

### Conflict Resolution

This next submission contains a value for _description_. We want that new description, but we don't want to overwrite the old one.
Conveniently, a ChangeSet will automatically give a Preference of **BOTH** since both values are not the default value of `None`.
This results in a conflict since we can only assign a single value to _description_.
Without any additional input, a `Conflict` error will be raised. That error can be avoided by specifying a conflict resolution rule.
!!! tip
    The `Conflict` error can also be avoided by overriding the `default_conflict` rule, setting it to `Preference.BOTH`.
    This will result in the field being labeled as [Unresolved](#unresolved).
Conflict resolution rules are defined just like preference rules but must be suffixed with `_conflict` as seen below.

```python
class POIChangeSet(ChangeSet[POI]):
    def __init__(self, baseline: POI, target: POI):
        super().__init__(baseline, target,
            default=Preference.LEFT,
            description_conflict='\n'.join,  # Join the descriptions into a single string
            ada_compliant=lambda b, t: False,
            latest_condition=Preference.RIGHT
        )

# Retrieve the existing Niagara Falls entry
saved_poi = poi_dao.get('Niagara Falls')

# Create an entry from the user's input
user_entry = poi_dao.create_with(
    name='Niagara Falls',
    description='Known for their immense power and breathtaking views!',
    insert=False
)

ChangeSet(saved_poi, user_entry).resolve_preferences().apply()
```

|          | Name          | Category | Description                                                                                                                    | Website                  | Latitude | Longitude | ADA   | Condition                              |
|----------|---------------|----------|--------------------------------------------------------------------------------------------------------------------------------|--------------------------|----------|-----------|-------|----------------------------------------|
| baseline | Niagara Falls | Nature   | A world-famous trio of waterfalls straddling the Canada-U.S. border.                                                           | https://www.nps.gov/nifa | 43.0815  | -79.0642  | False | Construction limits viewing platforms. |
| target   | Niagara Falls |          | Known for their immense power and breathtaking views!                                                                          |                          |          |           |       |                                        |
| result   | Niagara Falls | Nature   | A world-famous trio of waterfalls straddling the Canada-U.S. border.<br/>Known for their immense power and breathtaking views! | https://www.nps.gov/nifa | 43.0815  | -79.0642  | False | Construction limits viewing platforms. |

Most of the time, you can get away with defining a preference rule.
But for more complex situations, a conflict resolution rule is more powerful.
If rule definitions don't meet your needs, you can always override the `resolve_conflict` function for complete control.

Now that resolving preferences is understood, we can discuss the special cases when applying changes.

### Applying Changes

Changes are applied by calling the `apply()` method on the ChangeSet.
This is typically only done after calling `resolve_preferences()`.
The `apply()` function calls `get_resolution()` for each field and assigns the value to the baseline object.
!!! info
    The **baseline** object is the one that is modified when applying changes.
    This means that submitted said changes to the DB is as simple as calling `dao.commit()`

Most of the time, the determined _resolution_ is simply the **target** value.
However, it may also be labeled as `Resolved` or `Unresolved`.
!!! info
    If the preference is determined to be **LEFT**, The `resolve_preference` function will delete the entry
    from the dict and no changes will be applied. To understand why this is, think about resolving code changes,
    if one of the changes is unwanted, that change is removed leaving just the original code as it was.

Here is a sample of how a ChangeSet may look under the hood, after resolving preferences but before applying changes:
```python
changeset = {
    'category': (
        'Nature',
        Unresolved('State Park')
    ),
    'description': (
        'A world-famous trio of waterfalls straddling the Canada-U.S. border.',
        Resolved(
            'Known for their immense power and breathtaking views!',
            'A world-famous trio of waterfalls straddling the Canada-U.S. border.\nKnown for their immense power and breathtaking views!'
        )
    ),
    'website': (
        None,
        Unresolved('invalid-website.com')
    ),
    'latest_condition': (
        'Construction limits viewing platforms.',
        'Construction has completed'
    )
}
```

#### Resolved

In the previous sample, the description field is marked as `Resolved`. 
This means that the resolution is a different value from that of the _baseline_ or the _target_.

When applying changes, the resolved value will be used as the new value.

#### Unresolved

`category` and `website` give us examples of unresolved fields.
You will see `Unresolved` if the Preference was **NEITHER** or **NOT_APPLICABLE**.
A field could also be unresolved if the Preference is **BOTH** even after attempting to resolve the conflict.
In this case, we don't want an empty value or an invalid website, leaving that change Unresolved.
We can still _apply_ the changes if something is unresolved, but the object's value will then be set to an `Unresolved` object.
You will have to account for this and handle it before being able to `commit` the changes to the database.
!!! tip
    Resolving an _Unresolved_ change will likely need some sort of human feedback since a standard rule could not
    determine an adequate result. This feedback may be in the form of submitting the change to a moderator for approval.

Again, once a ChangeSet is applied, we can now submit the changes to the database through a `commit`.
!!! tip
    The `SingleModelService` is an extendable BaseService class for your DAOModel.
    It includes a `merge` function that uses a ChangeSet to merge data into a model entry.
    If you find this feature useful, that service may be a good starting point.

## MergeSet

A ChangeSet is great, but we process many user submissions each day.
A MergeSet will combine several model entries at once.
This way we have visibility into all the potential values to determine the final result.

A **MergeSet** is configured in the same manner as a ChangeSet.
The only difference is that the target is a list of model entries.

Here is an example of merging multiple user-submitted POIs into a baseline:

```python
# Retrieve the existing Washington Monument entry
saved_poi = poi_dao.get('Washington Monument')

# Create entries from multiple user inputs
user_entry1 = poi_dao.create_with(
    name='Washington Monument',
    category='Obelisk',
    description='A 555-foot marble obelisk built to commemorate George Washington.',
    website='https://www.nps.gov/wamo',
    ada_compliant=True,
    latest_condition='Clear skies, excellent visibility from observation deck.',
    insert=False
)

user_entry2 = poi_dao.create_with(
    name='Washington Monument',
    category='Structure',
    description='One of the most recognizable structures in Washington DC.',
    latitude=38.8895,
    longitude=-77.0352,
    latest_condition='Limited tickets available for today\'s tours.',
    insert=False
)

user_entry3 = poi_dao.create_with(
    name='Washington Monument',
    description='Completed in 1884, it was once the tallest building in the world.',
    website='https://washington.org/monument',
    ada_compliant=False,
    latest_condition='Special evening lighting display tonight.',
    insert=False
)

user_entry4 = poi_dao.create_with(
    name='Washington Monument',
    category='Monument',
    description='Located on the National Mall between the Capitol and Lincoln Memorial.',
    ada_compliant=True,
    latest_condition='Park rangers offering special history talks hourly.',
    insert=False
)

user_entry5 = poi_dao.create_with(
    name='Washington Monument',
    category='Monument',
    website='https://www.doi.gov/washington-monument',
    latest_condition='Surrounding grounds open for picnics and gatherings.',
    insert=False
)

# Define custom preference rules for the MergeSet
class POIMergeSet(MergeSet[POI]):
    def __init__(self, baseline: POI, *targets: POI):
        super().__init__(baseline, *targets,
            # For category, prefer the deepest category from our taxonomy
            # i.e. 'Obelisk' is most preferred within the following taxonomy
            #   Structure
            #     └── Built Structure
            #           └── Commemorative Structure
            #                 └── Monument
            #                       └── Obelisk
            category=most_specific_from_taxonomy,

            # For description, we want to combine all unique descriptions
            # This requires a conflict resolution rule (_conflict)
            description_conflict=lambda values: (
                    '\n'.join(dedupe(exclude_falsy(values)))  # dedupe & exclude_falsy are from daomodel.util
            ),

            # For website, we prefer official .gov domains
            website=lambda values: (
                    first_str_with('.gov', values) or  # these functions are also available in daomodel.util
                    first(values)  # selects the first non-empty str
            ),

            # For coordinates, we want precise values
            latitude=lambda values: next((v for v in values if v is not None), None),
            longitude=lambda values: next((v for v in values if v is not None), None),

            # For ADA, trust the majority by taking the most common value
            ada_compliant=mode,  # the mode function may be imported from daomodel.util

            # For latest condition, we want the most recent information
            latest_condition=last  # Take the last submitted value
        )

# Create the MergeSet with baseline and all user entries
merge_set = POIMergeSet(saved_poi, user_entry1, user_entry2, user_entry3, user_entry4, user_entry5)

# Resolve preferences and apply changes
merge_set.resolve_preferences().apply()
```
!!! tip
    The code example above contains several utility functions that can be imported and used in your own projects!

Let's examine how this MergeSet handles the different values from multiple submissions:

|          | Name                | Category  | Description                                                                                                                                                                                                                                                                   | Website                                 | Latitude | Longitude | ADA   | Condition                                                |
|----------|---------------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|----------|-----------|-------|----------------------------------------------------------|
| baseline | Washington Monument |           | A 555-foot marble obelisk honoring the first U.S. president.                                                                                                                                                                                                                  |                                         | 38.8895  | -77.0352  |       |                                                          |
| target 0 | Washington Monument | Obelisk   | A 555-foot marble obelisk built to commemorate George Washington.                                                                                                                                                                                                             | https://www.nps.gov/wamo                |          |           | True  | Clear skies, excellent visibility from observation deck. |
| target 1 | Washington Monument | Structure | One of the most recognizable structures in Washington DC.                                                                                                                                                                                                                     |                                         | 38.8895  | -77.0352  |       | Limited tickets available for today's tours.             |
| target 2 | Washington Monument |           | Completed in 1884, it was once the tallest building in the world.                                                                                                                                                                                                             | https://washington.org/monument         |          |           | False | Special evening lighting display tonight.                |
| target 3 | Washington Monument | Monument  | Located on the National Mall between the Capitol and Lincoln Memorial.                                                                                                                                                                                                        |                                         |          |           | True  | Park rangers offering special history talks hourly.      |
| target 4 | Washington Monument | Monument  |                                                                                                                                                                                                                                                                               | https://www.doi.gov/washington-monument |          |           |       | Surrounding grounds open for picnics and gatherings.     |
| result   | Washington Monument | Obelisk   | A 555-foot marble obelisk built to commemorate George Washington.<br>One of the most recognizable structures in Washington DC.<br>Completed in 1884, it was once the tallest building in the world.<br>Located on the National Mall between the Capitol and Lincoln Memorial. | https://www.nps.gov/wamo                | 38.8895  | -77.0352  | True  | Surrounding grounds open for picnics and gatherings.     |

This example shows how a MergeSet could handle complex merging scenarios with multiple user submissions,
applying different preference rules and conflict resolution strategies based on the specific requirements of each field.

If you have your own utility functions that you use often and would like added to the library,
[submit a ticket](https://github.com/BassMastaCod/DAOModel/issues/new) to let me know, I would be happy to add it!
