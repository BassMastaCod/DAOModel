from typing import Optional

from sqlmodel import Field

from daomodel import DAOModel, PrimaryKey, ForeignKey
from tests.labeled_tests import labeled_tests


class ForeignModel(DAOModel, table=True):
    pk: int = PrimaryKey


class PropertyModel(DAOModel, table=True):
    set_pk: int = PrimaryKey
    unset_pk: Optional[int] = PrimaryKey
    default_pk: Optional[int] = Field(primary_key=True, default=0)
    set_default_pk: Optional[int] = Field(primary_key=True, default=0)
    default_none_pk: Optional[int] = Field(primary_key=True, default=None)
    set_none_pk: Optional[int] = PrimaryKey
    set_default_none_pk: Optional[int] = Field(primary_key=True, default=None)
    set_fk: int = ForeignKey('foreign_model.pk')
    unset_fk: Optional[int] = ForeignKey('foreign_model.pk')
    default_fk: Optional[int] = ForeignKey('foreign_model.pk', default=0)
    set_default_fk: Optional[int] = ForeignKey('foreign_model.pk', default=0)
    default_none_fk: Optional[int] = ForeignKey('foreign_model.pk', default=None)
    set_none_fk: Optional[int] = ForeignKey('foreign_model.pk')
    set_default_none_fk: Optional[int] = ForeignKey('foreign_model.pk', default=None)
    set: int
    unset: Optional[int]
    default: Optional[int] = 0
    set_default: Optional[int] = 0
    default_none: Optional[int] = None
    set_none: Optional[int]
    set_default_none: Optional[int] = None
property_model = PropertyModel(set_pk=1, set_default_pk=0, set_none_pk=None, set_default_none_pk=None,
                       set_fk=1, set_default_fk=0, set_none_fk=None, set_default_none_fk=None,
                       set=1, set_default=0, set_none=None, set_default_none=None)

all_properties = [
    'set_pk',
    'unset_pk',
    'default_pk',
    'set_default_pk',
    'default_none_pk',
    'set_none_pk',
    'set_default_none_pk',
    'set_fk',
    'unset_fk',
    'default_fk',
    'set_default_fk',
    'default_none_fk',
    'set_none_fk',
    'set_default_none_fk',
    'set',
    'unset',
    'default',
    'set_default',
    'default_none',
    'set_none',
    'set_default_none'
]
pk_properties = [
    'set_pk',
    'unset_pk',
    'default_pk',
    'set_default_pk',
    'default_none_pk',
    'set_none_pk',
    'set_default_none_pk'
]
fk_properties = [
    'set_fk',
    'unset_fk',
    'default_fk',
    'set_default_fk',
    'default_none_fk',
    'set_none_fk',
    'set_default_none_fk'
]
standard_properties = [
    'set',
    'unset',
    'default',
    'set_default',
    'default_none',
    'set_none',
    'set_default_none'
]
assigned_properties = [
    'set_pk',
    'set_fk',
    'set',
]
unset_properties = [
    'unset_pk',
    'default_pk',
    'default_none_pk',
    'unset_fk',
    'default_fk',
    'default_none_fk',
    'unset',
    'default',
    'default_none'
]
default_value_properties = [
    'unset_pk',
    'default_pk',
    'set_default_pk',
    'default_none_pk',
    'set_default_none_pk',
    'unset_fk',
    'default_fk',
    'set_default_fk',
    'default_none_fk',
    'set_default_none_fk',
    'unset',
    'default',
    'set_default',
    'default_none',
    'set_default_none'
]
none_value_properties = [
    'unset_pk',
    'default_none_pk',
    'set_none_pk',
    'set_default_none_pk',
    'unset_fk',
    'default_none_fk',
    'set_none_fk',
    'set_default_none_fk',
    'unset',
    'default_none',
    'set_none',
    'set_default_none'
]
set_none_value_properties = [
    'set_none_pk',
    'set_default_none_pk',
    'set_none_fk',
    'set_default_none_fk',
    'set_none',
    'set_default_none'
]
set_to_non_none_default_properties = [
    'set_default_pk',
    'set_default_fk',
    'set_default'
]
standard_non_none_properties = [
    'set',
    'default',
    'set_default'
]
primary_key_and_unset_foreign_key_properties = [
    'set_pk',
    'unset_pk',
    'default_pk',
    'set_default_pk',
    'default_none_pk',
    'set_none_pk',
    'set_default_none_pk',
    'unset_fk',
    'default_fk',
    'default_none_fk'
]


@labeled_tests({
    'no properties': [
        ({}, []),
        ({'all': False}, []),
        ({'pk': False}, []),
        ({'unset': False}, []),
        ({'defaults': False}, []),
        ({'none': False}, []),
        ({'pk': False, 'unset': False, 'defaults': False, 'none': False}, [])
    ],
    'all properties': [
        ({'all': True}, all_properties),
        ({'pk': True, 'fk': True, 'standard': True}, all_properties)
    ],
    'primary key properties': [
        ({'pk': True}, pk_properties),
        ({'all': True, 'fk': False, 'standard': False}, pk_properties)
    ],
    'foreign key properties': [
        ({'fk': True}, fk_properties),
        ({'all': True, 'pk': False, 'standard': False}, fk_properties)
    ],
    'standard properties': [
        ({'standard': True}, standard_properties),
        ({'all': True, 'pk': False, 'fk': False}, standard_properties)
    ],
    'assigned properties': [
        ({'assigned': True}, assigned_properties),
        ({'all': True, 'unset': False, 'defaults': False, 'none': False}, assigned_properties)
    ],
    'unset properties':
        ({'unset': True}, unset_properties),
    'default value properties':
        ({'defaults': True}, default_value_properties),
    'none value properties':
        ({'none': True}, none_value_properties),
    'mixed property categories': [
        ({'none': True, 'unset': False}, set_none_value_properties),
        ({'defaults': True, 'unset': False, 'none': False}, set_to_non_none_default_properties),
        ({'standard': True, 'none': False}, standard_non_none_properties),
        ({'unset': True, 'standard': False, 'pk': True}, primary_key_and_unset_foreign_key_properties),
    ]
})
def test_get_property_names(property_modifications: dict[str, bool], expected: list[str]):
    assert property_model.get_property_names(**property_modifications) == expected
