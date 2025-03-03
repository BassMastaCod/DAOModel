from decimal import Decimal
from enum import Enum, auto
from typing import Optional, Any

from daomodel import DAOModel, PrimaryKey, OptionalPrimaryKey
from daomodel.model_diff import ModelDiff
from tests.labeled_tests import labeled_tests


class LaundryStatus(Enum):
    Private = auto()
    Shared = auto()
    Public = auto()


class Rental(DAOModel, table=True):
    address: str = PrimaryKey
    apt: Optional[str] = OptionalPrimaryKey
    dwelling_type: str
    sqft: int
    bedrooms: int
    bathrooms: Decimal
    garage_parking: int = 0
    laundry: Optional[LaundryStatus] = None
    cost: int


one_full = Decimal('1')
one_full_one_half = Decimal('1.1')
two_full = Decimal('2')
two_full_two_half = Decimal('2.2')


dorm = Rental(
    address='123 College Ave',
    apt='12',
    dwelling_type='Dormitory',
    sqft=200,
    bedrooms=1,
    bathrooms=one_full,
    laundry=LaundryStatus.Public,
    cost=0
)
apartment = Rental(
    address='456 City Plaza',
    apt='101',
    dwelling_type='Apartment',
    sqft=850,
    bedrooms=2,
    bathrooms=one_full,
    garage_parking=1,
    laundry=LaundryStatus.Shared,
    cost=1200
)
apartment_two = Rental(
    address='456 City Plaza',
    apt='102',
    dwelling_type='Apartment',
    sqft=850,
    bedrooms=2,
    bathrooms=one_full,
    garage_parking=1,
    laundry=LaundryStatus.Shared,
    cost=1200
)
multi_family = Rental(
    address='789 Suburb St',
    apt='B',
    dwelling_type='Multi-family House',
    sqft=950,
    bedrooms=1,
    bathrooms=one_full_one_half,
    cost=1800
)
town_home = Rental(
    address='321 Maple Dr',
    dwelling_type='Town home',
    sqft=1400,
    bedrooms=3,
    bathrooms=two_full,
    garage_parking=1,
    laundry=LaundryStatus.Private,
    cost=2200
)
single_family = Rental(
    address='987 Country Rd',
    dwelling_type='House',
    sqft=1800,
    bedrooms=4,
    bathrooms=two_full_two_half,
    garage_parking=2,
    laundry=LaundryStatus.Private,
    cost=3000
)


@labeled_tests({
    'dorm vs apartment':
        (dorm, apartment, {
            'dwelling_type': ('Dormitory', 'Apartment'),
            'sqft': (200, 850),
            'bedrooms': (1, 2),
            'garage_parking': (0, 1),
            'laundry': (LaundryStatus.Public, LaundryStatus.Shared),
            'cost': (0, 1200)
        }),
    'dorm vs multi family':
        (dorm, multi_family, {
            'dwelling_type': ('Dormitory', 'Multi-family House'),
            'sqft': (200, 950),
            'bathrooms': (Decimal('1'), Decimal('1.1')),
            'laundry': (LaundryStatus.Public, None),
            'cost': (0, 1800)
        }),
    'dorm vs town home':
        (dorm, town_home, {
            'dwelling_type': ('Dormitory', 'Town home'),
            'sqft': (200, 1400),
            'bedrooms': (1, 3),
            'bathrooms': (Decimal('1'), Decimal('2')),
            'garage_parking': (0, 1),
            'laundry': (LaundryStatus.Public, LaundryStatus.Private),
            'cost': (0, 2200)
        }),
    'dorm vs single family':
        (dorm, single_family, {
            'dwelling_type': ('Dormitory', 'House'),
            'sqft': (200, 1800),
            'bedrooms': (1, 4),
            'bathrooms': (Decimal('1'), Decimal('2.2')),
            'garage_parking': (0, 2),
            'laundry': (LaundryStatus.Public, LaundryStatus.Private),
            'cost': (0, 3000)
        }),
    'apartment vs multi family':
        (apartment, multi_family, {
            'dwelling_type': ('Apartment', 'Multi-family House'),
            'sqft': (850, 950),
            'bedrooms': (2, 1),
            'bathrooms': (Decimal('1'), Decimal('1.1')),
            'garage_parking': (1, 0),
            'laundry': (LaundryStatus.Shared, None),
            'cost': (1200, 1800)
        }),
    'apartment vs town home':
        (apartment, town_home, {
            'dwelling_type': ('Apartment', 'Town home'),
            'sqft': (850, 1400),
            'bedrooms': (2, 3),
            'bathrooms': (Decimal('1'), Decimal('2')),
            'laundry': (LaundryStatus.Shared, LaundryStatus.Private),
            'cost': (1200, 2200)
        }),
    'apartment vs single family':
        (apartment, single_family, {
            'dwelling_type': ('Apartment', 'House'),
            'sqft': (850, 1800),
            'bedrooms': (2, 4),
            'bathrooms': (Decimal('1'), Decimal('2.2')),
            'garage_parking': (1, 2),
            'laundry': (LaundryStatus.Shared, LaundryStatus.Private),
            'cost': (1200, 3000)
        }),
    'multi family vs town home':
        (multi_family, town_home, {
            'dwelling_type': ('Multi-family House', 'Town home'),
            'sqft': (950, 1400),
            'bedrooms': (1, 3),
            'bathrooms': (Decimal('1.1'), Decimal('2')),
            'garage_parking': (0, 1),
            'laundry': (None, LaundryStatus.Private),
            'cost': (1800, 2200)
        }),
    'multi family vs single family':
        (multi_family, single_family, {
            'dwelling_type': ('Multi-family House', 'House'),
            'sqft': (950, 1800),
            'bedrooms': (1, 4),
            'bathrooms': (Decimal('1.1'), Decimal('2.2')),
            'garage_parking': (0, 2),
            'laundry': (None, LaundryStatus.Private),
            'cost': (1800, 3000)
        }),
    'town home vs single family':
        (town_home, single_family, {
            'dwelling_type': ('Town home', 'House'),
            'sqft': (1400, 1800),
            'bedrooms': (3, 4),
            'bathrooms': (Decimal('2'), Decimal('2.2')),
            'garage_parking': (1, 2),
            'cost': (2200, 3000)
        }),
    'empty diff':
        (apartment, apartment_two, {})
})
def test_get_property_names(left: Rental, right: Rental, expected: dict[str, tuple[Any, Any]]):
    assert ModelDiff(left, right, include_pk=False) == expected


@labeled_tests({
    'same address':
        (apartment, apartment_two, {
            'apt': ('101', '102')
        }),
    'right None':
        (multi_family, town_home, {
            'address': ('789 Suburb St', '321 Maple Dr'),
            'apt': ('B', None)
        }),
    'left None':
        (single_family, multi_family, {
            'address': ('987 Country Rd', '789 Suburb St'),
            'apt': (None, 'B')
        }),
    'both None':
        (town_home, single_family, {
            'address': ('321 Maple Dr', '987 Country Rd')
        })
})
def test_get_property_names__pk(left: Rental, right: Rental, expected: dict[str, tuple[Any, Any]]):
    diff = ModelDiff(left, right)
    pk_diff = {key: diff[key] for key in ['address', 'apt'] if key in diff}
    assert pk_diff == expected


@labeled_tests({
    'all fields':
        (multi_family, single_family, {
            'address',
            'apt',
            'dwelling_type',
            'sqft',
            'bedrooms',
            'bathrooms',
            'garage_parking',
            'laundry',
            'cost'
        }),
    'partial fields':
        (dorm, multi_family, {
            'address',
            'apt',
            'dwelling_type',
            'sqft',
            'bathrooms',
            'laundry',
            'cost'
        }),
    'single field':
        (apartment, apartment_two, {'apt'}),
    'no fields': [
        (dorm, dorm, set()),
        (apartment, apartment, set()),
        (multi_family, multi_family, set()),
        (town_home, town_home, set()),
        (single_family, single_family, set())
    ]
})
def test_fields(left: Rental, right: Rental, expected: set[str]):
    assert ModelDiff(left, right).fields == expected


def test_fields__exclude_pk():
    assert ModelDiff(single_family, dorm, include_pk=False).fields == {
        'dwelling_type', 'sqft', 'bedrooms', 'bathrooms', 'garage_parking', 'laundry', 'cost'
    }
