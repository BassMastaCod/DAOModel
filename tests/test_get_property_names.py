from typing import Optional, Any

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


all_property_values = {
    'set_pk': 1,
    'unset_pk': None,
    'default_pk': 0,
    'set_default_pk': 0,
    'default_none_pk': None,
    'set_none_pk': None,
    'set_default_none_pk': None,
    'set_fk': 1,
    'unset_fk': None,
    'default_fk': 0,
    'set_default_fk': 0,
    'default_none_fk': None,
    'set_none_fk': None,
    'set_default_none_fk': None,
    'set': 1,
    'unset': None,
    'default': 0,
    'set_default': 0,
    'default_none': None,
    'set_none': None,
    'set_default_none': None
}
pk_property_values = {
    'set_pk': 1,
    'unset_pk': None,
    'default_pk': 0,
    'set_default_pk': 0,
    'default_none_pk': None,
    'set_none_pk': None,
    'set_default_none_pk': None
}
fk_property_values = {
    'set_fk': 1,
    'unset_fk': None,
    'default_fk': 0,
    'set_default_fk': 0,
    'default_none_fk': None,
    'set_none_fk': None,
    'set_default_none_fk': None
}
standard_property_values = {
    'set': 1,
    'unset': None,
    'default': 0,
    'set_default': 0,
    'default_none': None,
    'set_none': None,
    'set_default_none': None
}
assigned_property_values = {
    'set_pk': 1,
    'set_fk': 1,
    'set': 1
}
unset_property_values = {
    'unset_pk': None,
    'default_pk': 0,
    'default_none_pk': None,
    'unset_fk': None,
    'default_fk': 0,
    'default_none_fk': None,
    'unset': None,
    'default': 0,
    'default_none': None
}
default_value_property_values = {
    'unset_pk': None,
    'default_pk': 0,
    'set_default_pk': 0,
    'default_none_pk': None,
    'set_default_none_pk': None,
    'unset_fk': None,
    'default_fk': 0,
    'set_default_fk': 0,
    'default_none_fk': None,
    'set_default_none_fk': None,
    'unset': None,
    'default': 0,
    'set_default': 0,
    'default_none': None,
    'set_default_none': None
}
none_value_property_values = {
    'unset_pk': None,
    'default_none_pk': None,
    'set_none_pk': None,
    'set_default_none_pk': None,
    'unset_fk': None,
    'default_none_fk': None,
    'set_none_fk': None,
    'set_default_none_fk': None,
    'unset': None,
    'default_none': None,
    'set_none': None,
    'set_default_none': None
}
set_none_value_property_values = {
    'set_none_pk': None,
    'set_default_none_pk': None,
    'set_none_fk': None,
    'set_default_none_fk': None,
    'set_none': None,
    'set_default_none': None
}
set_to_non_none_default_property_values = {
    'set_default_pk': 0,
    'set_default_fk': 0,
    'set_default': 0
}
standard_non_none_property_values = {
    'set': 1,
    'default': 0,
    'set_default': 0
}
primary_key_and_unset_foreign_key_property_values = {
    'set_pk': 1,
    'unset_pk': None,
    'default_pk': 0,
    'set_default_pk': 0,
    'default_none_pk': None,
    'set_none_pk': None,
    'set_default_none_pk': None,
    'unset_fk': None,
    'default_fk': 0,
    'default_none_fk': None
}


@labeled_tests({
    'no properties': [
        ({}, [], {}),
        ({'all': False}, [], {}),
        ({'pk': False}, [], {}),
        ({'unset': False}, [], {}),
        ({'defaults': False}, [], {}),
        ({'none': False}, [], {}),
        ({'pk': False, 'unset': False, 'defaults': False, 'none': False}, [], {})
    ],
    'all properties': [
        ({'all': True}, all_properties, all_property_values),
        ({'pk': True, 'fk': True, 'standard': True}, all_properties, all_property_values)
    ],
    'primary key properties': [
        ({'pk': True}, pk_properties, pk_property_values),
        ({'all': True, 'fk': False, 'standard': False}, pk_properties, pk_property_values)
    ],
    'foreign key properties': [
        ({'fk': True}, fk_properties, fk_property_values),
        ({'all': True, 'pk': False, 'standard': False}, fk_properties, fk_property_values)
    ],
    'standard properties': [
        ({'standard': True}, standard_properties, standard_property_values),
        ({'all': True, 'pk': False, 'fk': False}, standard_properties, standard_property_values)
    ],
    'assigned properties': [
        ({'assigned': True}, assigned_properties, assigned_property_values),
        ({'all': True, 'unset': False, 'defaults': False, 'none': False}, assigned_properties, assigned_property_values)
    ],
    'unset properties': [
        ({'unset': True}, unset_properties, unset_property_values)
    ],
    'default value properties': [
        ({'defaults': True}, default_value_properties, default_value_property_values)
    ],
    'none value properties': [
        ({'none': True}, none_value_properties, none_value_property_values)
    ],
    'mixed property categories': [
        ({'none': True, 'unset': False}, set_none_value_properties, set_none_value_property_values),
        ({'defaults': True, 'unset': False, 'none': False}, set_to_non_none_default_properties, set_to_non_none_default_property_values),
        ({'standard': True, 'none': False}, standard_non_none_properties, standard_non_none_property_values),
        ({'unset': True, 'standard': False, 'pk': True}, primary_key_and_unset_foreign_key_properties, primary_key_and_unset_foreign_key_property_values)
    ]
})
def test_get_property_names_get_property_values(
        property_modifications: dict[str, bool],
        expected_property_names: list[str],
        expected_property_values: dict[str, Any]):
    assert property_model.get_property_names(**property_modifications) == expected_property_names
    assert property_model.get_property_values(**property_modifications) == expected_property_values
