from typing import Dict, Any, Tuple, Type, get_origin, get_args, Union
import inspect
import uuid
from sqlmodel.main import SQLModelMetaclass, Field, FieldInfo
from sqlalchemy import ForeignKey, JSON

from daomodel.util import reference_of, UnsupportedFeatureError
from daomodel.fields import Identifier, Unsearchable, Protected


def is_dao_model(cls: Type[Any]) -> bool:
    return inspect.isclass(cls) and 'DAOModel' in (base.__name__ for base in inspect.getmro(cls))


class DAOModelMetaclass(SQLModelMetaclass):
    """A metaclass for DAOModel that adds support for Identifier and DAOModel typing."""

    def __new__(
            cls,
            name: str,
            bases: Tuple[Type[Any], ...],
            class_dict: Dict[str, Any],
            **kwargs: Any,
    ) -> Any:
        annotations = class_dict.get('__annotations__', {})

        for field_name, field_type in annotations.items():
            if get_origin(field_type) is Unsearchable:
                class_dict.setdefault('_unsearchable', set()).add(field_name)
                field_type = get_args(field_type)[0]

            field_args: dict[str, Any] = {'nullable': False}
            if get_origin(field_type) is Identifier:
                field_type = get_args(field_type)[0]
                field_args['primary_key'] = True

            is_protected = get_origin(field_type) is Protected
            if is_protected:
                field_type = get_args(field_type)[0]

            if get_origin(field_type) is Union:
                args = get_args(field_type)
                if len(args) == 2 and args[1] is type(None):
                    field_args['nullable'] = True
                    field_type = args[0]

            if field_type is uuid.UUID:
                field_args['default_factory'] = uuid.uuid4
            elif field_type is dict:
                field_args['sa_type'] = JSON
            elif is_dao_model(field_type):
                if len(field_type.get_pk()) == 1:
                    single_pk = next(iter(field_type.get_pk()))
                    field_type = field_type.__annotations__[single_pk.name]
                    field_args['foreign_key'] = reference_of(single_pk)
                    # Check if field already exists with custom parameters
                    custom_ondelete = None
                    if field_name in class_dict:
                        existing_field = class_dict.get(field_name)
                        # Check for both ondelete and on_delete parameters
                        if hasattr(existing_field, 'ondelete'):
                            custom_ondelete = existing_field.ondelete
                        elif hasattr(existing_field, 'on_delete'):
                            custom_ondelete = existing_field.on_delete

                    # Set default ondelete behavior if not customized
                    if custom_ondelete is None:
                        if field_args['nullable']:
                            field_args['ondelete'] = 'SET NULL'
                        else:
                            field_args['ondelete'] = 'CASCADE'
                        if is_protected:
                            field_args['ondelete'] = 'RESTRICT'
                    else:
                        field_args['ondelete'] = custom_ondelete

                    # Pass ondelete to ForeignKey constructor
                    field_args['sa_column_args'] = [
                        ForeignKey(
                            reference_of(single_pk),
                            onupdate='CASCADE',
                            ondelete=field_args['ondelete']
                        )
                    ]
                else:
                    raise UnsupportedFeatureError(f'Cannot map to composite key of {field_type.__name__}.')
            annotations[field_name] = Union[field_type|None] if field_args['nullable'] else field_type

            if field_name in class_dict:
                existing_field = class_dict.get(field_name)
                if isinstance(existing_field, FieldInfo):
                    for key, value in field_args.items():
                        setattr(existing_field, key, value)
                    continue
                else:
                    field_args['default'] = existing_field
            class_dict[field_name] = Field(**field_args)

        return super().__new__(cls, name, bases, class_dict, **kwargs)
