from typing import Dict, Any, Tuple, Type, get_origin, get_args, Union
import inspect
import uuid
from sqlmodel.main import SQLModelMetaclass, Field
from sqlalchemy import ForeignKey

from daomodel.util import reference_of, UnsupportedFeatureError
from daomodel.fields import Identifier, Unsearchable


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
        if '_unsearchable' not in class_dict:
            class_dict['_unsearchable'] = set()

        annotations = class_dict.get('__annotations__', {})

        for field_name, field_type in annotations.items():
            field_args = {}
            if get_origin(field_type) is Unsearchable:
                class_dict['_unsearchable'].add(field_name)
                field_type = get_args(field_type)[0]

            if get_origin(field_type) is Identifier:
                field_type = get_args(field_type)[0]
                field_args['primary_key'] = True
                if field_type is uuid.UUID:
                    field_args['default_factory'] = uuid.uuid4

            is_optional = False
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                if len(args) == 2 and args[1] is type(None) and is_dao_model(args[0]):
                    is_optional = True
                    field_type = args[0]

            if is_dao_model(field_type):
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
                        if is_optional:
                            field_args['nullable'] = True
                            field_args['ondelete'] = 'SET NULL'
                        else:
                            field_args['ondelete'] = 'CASCADE'
                    else:
                        field_args['ondelete'] = custom_ondelete
                        if is_optional:
                            field_args['nullable'] = True

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
            annotations[field_name] = field_type

            if field_args:
                if field_name in class_dict:
                    existing_field = class_dict.get(field_name)
                    if hasattr(existing_field, '__dict__'):
                        existing_args = vars(existing_field)
                        field_args = {**field_args, **existing_args}
                    else:
                        field_args['default'] = existing_field
                class_dict[field_name] = Field(**field_args)

        return super().__new__(cls, name, bases, class_dict, **kwargs)
