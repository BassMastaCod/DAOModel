from typing import Dict, Any, Tuple, Type, get_origin, get_args, Union, TypeVar, Generic, Optional
import inspect
import uuid
from sqlmodel.main import SQLModelMetaclass, Field, FieldInfo
from sqlalchemy import ForeignKey, JSON

from daomodel.util import reference_of, UnsupportedFeatureError
from daomodel.fields import Identifier, Unsearchable, Protected


class Annotation:
    """A utility class to help manage a single annotation type."""
    def __init__(self, field_name: str, field_type: type[Any]):
        self.name = field_name

        self.modifiers = set()
        for modifier in [Unsearchable, Identifier, Protected]:
            if get_origin(field_type) is modifier:
                self.modifiers.add(modifier)
                field_type = get_args(field_type)[0]
        if get_origin(field_type) is Union:
            args = get_args(field_type)
            if len(args) == 2 and args[1] is type(None):
                self.modifiers.add(Optional)
                field_type = args[0]

        self.type = field_type
        self.args = {}

    def has_modifier(self, modifier: Any) -> bool:
        """Check whether the annotation has a specified modifier.

        :param modifier: The modifier to check for, valid modifiers are Unsearchable, Identifier, Protected, Optional
        :return: True if the annotation has the modifier
        """
        return modifier in self.modifiers

    def is_dao_model(self) -> bool:
        """Check whether the annotation is a DAOModel."""
        return inspect.isclass(self.type) and 'DAOModel' in (base.__name__ for base in inspect.getmro(self.type))

    def __getitem__(self, key: str) -> Any:
        return self.args.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.args[key] = value


class ClassDictHelper:
    """A utility class to help manage class dictionary and annotations in metaclasses."""
    def __init__(self, class_dict: dict[str, Any]):
        self.class_dict = class_dict

    @property
    def annotations(self) -> dict[str, Any]:
        return self.class_dict.get('__annotations__', {})

    def set_annotation(self, field: Annotation) -> None:
        """Set an annotation for a field, automatically handling optional types if nullable is True."""
        self.annotations[field.name] = Union[field.type, None] if field['nullable'] else field.type

    @property
    def fields(self) -> list[Annotation]:
        return [Annotation(field_name, field_type) for field_name, field_type in self.annotations.items() if
                not field_name.startswith('_')]

    def add_unsearchable(self, field: Annotation) -> None:
        """Mark a field as unsearchable within in the class dictionary."""
        self.class_dict.setdefault('_unsearchable', set()).add(field.name)

    def __getitem__(self, key: str) -> Any:
        return self.class_dict.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.class_dict[key] = value

    def __contains__(self, field: Annotation) -> bool:
        return field.name in self.class_dict


class DAOModelMetaclass(SQLModelMetaclass):
    """A metaclass for DAOModel that adds support for modifiers and special typing within annotations."""
    def __new__(
            cls,
            name: str,
            bases: Tuple[Type[Any], ...],
            class_dict: Dict[str, Any],
            **kwargs: Any,
    ) -> Any:
        model = ClassDictHelper(class_dict)

        for field in model.fields:
            if field.has_modifier(Unsearchable):
                model.add_unsearchable(field)
            if field.has_modifier(Identifier):
                field['primary_key'] = True
            field['nullable'] = field.has_modifier(Optional)

            if field.type is uuid.UUID:
                field['default_factory'] = uuid.uuid4
            elif field.type is dict:
                field['sa_type'] = JSON
            elif field.is_dao_model():
                if len(field.type.get_pk()) != 1:
                    raise UnsupportedFeatureError(f'Cannot map to composite key of {field.type.__name__}.')

                single_pk = next(iter(field.type.get_pk()))
                field.type = field.type.__annotations__[single_pk.name]
                field['foreign_key'] = reference_of(single_pk)

                ondelete = None
                if field in model:
                    existing_field = model[field.name]
                    ondelete = getattr(existing_field, 'ondelete', None) or getattr(existing_field, 'on_delete', None)
                field['ondelete'] = (
                    ondelete if ondelete is not None else
                    'RESTRICT' if field.has_modifier(Protected) else
                    'SET NULL' if field['nullable'] else
                    'CASCADE'
                )

                field['sa_column_args'] = [
                    ForeignKey(
                        field['foreign_key'],
                        onupdate='CASCADE',
                        ondelete=field['ondelete']
                    )
                ]

            model.set_annotation(field)

            if field in model:
                existing_field = model[field.name]
                if isinstance(existing_field, FieldInfo):
                    for key, value in field.args.items():
                        setattr(existing_field, key, value)
                    continue
                else:
                    field['default'] = existing_field
            model[field.name] = Field(**field.args)

        return super().__new__(cls, name, bases, class_dict, **kwargs)
