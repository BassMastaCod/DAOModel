from decimal import Decimal
from enum import Enum, auto
from typing import Optional, Any, Literal

import pytest

from daomodel import DAOModel, PrimaryKey, OptionalPrimaryKey
from daomodel.model_diff import ModelDiff
from tests.labeled_tests import labeled_tests


class LaundryStatus(Enum):
    Public = auto()
    Shared = auto()
    Private = auto()


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


class RentalDiff(ModelDiff):
    def get_preferred(self, field: str) -> Literal['left', 'right', 'neither', 'both', 'n/a']:
        match field:
            case 'address'|'apt':
                return 'n/a'
            case 'sqft'|'bedrooms'|'bathrooms'|'garage_parking':
                return 'left' if self.get_left(field) > self.get_right(field) else 'right'
            case 'cost':
                return 'left' if self.get_left(field) < self.get_right(field) else 'right'
            case 'dwelling_type':
                bad = ['Apartment', 'Multi-family House']
                good = ['Town home', 'House']
                def get_value(dwelling_type: str):
                    if dwelling_type in bad:
                        return -1
                    elif dwelling_type in good:
                        return 1
                    else:
                        return 0
                left_value = get_value(self.get_left(field))
                right_value = get_value(self.get_right(field))
                return(
                    'left' if left_value > right_value else
                    'right' if right_value > left_value else
                    'both' if left_value > 0 else
                    'neither'
                )
            case 'laundry':
                left_value = 0 if self.get_left(field) is None else self.get_left(field).value
                right_value = 0 if self.get_right(field) is None else self.get_right(field).value
                return 'left' if left_value > right_value else 'right'
            case _:
                raise NotImplementedError(f'The field {field} is not supported')


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
def test_model_diff(left: Rental, right: Rental, expected: dict[str, tuple[Any, Any]]):
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
def test_model_diff__pk(left: Rental, right: Rental, expected: dict[str, tuple[Any, Any]]):
    diff = ModelDiff(left, right)
    pk_diff = {key: diff[key] for key in ['address', 'apt'] if key in diff}
    assert pk_diff == expected


def test_get_left_get_right():
    diff = ModelDiff(apartment, apartment_two)
    assert diff.get_left('apt') == '101'
    assert diff.get_right('apt') == '102'


def test_get_left_get_right__missing():
    diff = ModelDiff(apartment, apartment_two)
    with pytest.raises(KeyError):
        diff.get_left('address')
    with pytest.raises(KeyError):
        diff.get_right('cost')


def test_get_left_get_right__invalid():
    diff = ModelDiff(apartment, apartment_two)
    with pytest.raises(KeyError):
        diff.get_left('APT')
    with pytest.raises(KeyError):
        diff.get_right('invalid')


@labeled_tests({
    'dorm vs apartment': [
        (dorm, apartment, 'dwelling_type', 'left'),
        (dorm, apartment, 'sqft', 'right'),
        (dorm, apartment, 'bedrooms', 'right'),
        (dorm, apartment, 'garage_parking', 'right'),
        (dorm, apartment, 'laundry', 'right'),
        (dorm, apartment, 'cost', 'left')
    ],
    'dorm vs multi family': [
        (dorm, multi_family, 'dwelling_type', 'left'),
        (dorm, multi_family, 'sqft', 'right'),
        (dorm, multi_family, 'bathrooms', 'right'),
        (dorm, multi_family, 'laundry', 'left'),
        (dorm, multi_family, 'cost', 'left')
    ],
    'dorm vs town home': [
        (dorm, town_home, 'dwelling_type', 'right'),
        (dorm, town_home, 'sqft', 'right'),
        (dorm, town_home, 'bedrooms', 'right'),
        (dorm, town_home, 'bathrooms', 'right'),
        (dorm, town_home, 'garage_parking', 'right'),
        (dorm, town_home, 'laundry', 'right'),
        (dorm, town_home, 'cost', 'left')
    ],
    'dorm vs single family': [
        (dorm, single_family, 'dwelling_type', 'right'),
        (dorm, single_family, 'sqft', 'right'),
        (dorm, single_family, 'bedrooms', 'right'),
        (dorm, single_family, 'bathrooms', 'right'),
        (dorm, single_family, 'garage_parking', 'right'),
        (dorm, single_family, 'laundry', 'right'),
        (dorm, single_family, 'cost', 'left')
    ],
    'apartment vs multi family': [
        (apartment, multi_family, 'dwelling_type', 'neither'),
        (apartment, multi_family, 'sqft', 'right'),
        (apartment, multi_family, 'bedrooms', 'left'),
        (apartment, multi_family, 'bathrooms', 'right'),
        (apartment, multi_family, 'garage_parking', 'left'),
        (apartment, multi_family, 'laundry', 'left'),
        (apartment, multi_family, 'cost', 'left')
    ],
    'apartment vs town home': [
        (apartment, town_home, 'dwelling_type', 'right'),
        (apartment, town_home, 'sqft', 'right'),
        (apartment, town_home, 'bedrooms', 'right'),
        (apartment, town_home, 'bathrooms', 'right'),
        (apartment, town_home, 'laundry', 'right'),
        (apartment, town_home, 'cost', 'left')
    ],
    'apartment vs single family': [
        (apartment, single_family, 'dwelling_type', 'right'),
        (apartment, single_family, 'sqft', 'right'),
        (apartment, single_family, 'bedrooms', 'right'),
        (apartment, single_family, 'bathrooms', 'right'),
        (apartment, single_family, 'garage_parking', 'right'),
        (apartment, single_family, 'laundry', 'right'),
        (apartment, single_family, 'cost', 'left')
    ],
    'multi family vs town home': [
        (multi_family, town_home, 'dwelling_type', 'right'),
        (multi_family, town_home, 'sqft', 'right'),
        (multi_family, town_home, 'bedrooms', 'right'),
        (multi_family, town_home, 'bathrooms', 'right'),
        (multi_family, town_home, 'garage_parking', 'right'),
        (multi_family, town_home, 'laundry', 'right'),
        (multi_family, town_home, 'cost', 'left')
    ],
    'multi family vs single family': [
        (multi_family, single_family, 'dwelling_type', 'right'),
        (multi_family, single_family, 'sqft', 'right'),
        (multi_family, single_family, 'bedrooms', 'right'),
        (multi_family, single_family, 'bathrooms', 'right'),
        (multi_family, single_family, 'garage_parking', 'right'),
        (multi_family, single_family, 'laundry', 'right'),
        (multi_family, single_family, 'cost', 'left')
    ],
    'town home vs single family': [
        (town_home, single_family, 'dwelling_type', 'both'),
        (town_home, single_family, 'sqft', 'right'),
        (town_home, single_family, 'bedrooms', 'right'),
        (town_home, single_family, 'bathrooms', 'right'),
        (town_home, single_family, 'garage_parking', 'right'),
        (town_home, single_family, 'cost', 'left')
    ],
    'n/a': [
        (multi_family, single_family, 'address', 'n/a'),
        (multi_family, single_family, 'apt', 'n/a'),
    ],
})
def test_get_preferred(left: Rental, right: Rental, field: str,
                       expected: Literal['left', 'right', 'neither', 'both', 'n/a']):
    assert RentalDiff(left, right).get_preferred(field) == expected


def test_get_preferred__not_implemented():
    with pytest.raises(NotImplementedError):
        ModelDiff(apartment, multi_family).get_preferred('cost')


def test_get_preferred__missing():
    with pytest.raises(KeyError):
        RentalDiff(single_family, town_home).get_preferred('laundry')
