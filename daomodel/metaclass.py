from typing import Dict, Any, Tuple, Type, get_origin, get_args
from sqlmodel.main import SQLModelMetaclass, Field, Undefined
from daomodel.fields import Identifier


class DAOModelMetaclass(SQLModelMetaclass):
    """
    A metaclass for DAOModel that adds support for Identifier typing.
    """
    def __new__(
        cls,
        name: str,
        bases: Tuple[Type[Any], ...],
        class_dict: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        annotations = class_dict.get('__annotations__', {})
        new_annotations = {}

        for field_name, field_type in annotations.items():
            if get_origin(field_type) is Identifier:
                field_type = get_args(field_type)[0]
                if field_name not in class_dict:
                    class_dict[field_name] = Field(primary_key=True)
                elif hasattr(class_dict[field_name], '__class__') and class_dict[field_name].__class__.__name__ == 'Field':
                   field_info = class_dict[field_name]
                   # Create a new Field with primary_key=True and all other attributes preserved
                   sa_kwargs = getattr(field_info, 'sa_column_kwargs', {}) or {}
                   sa_kwargs['primary_key'] = True
                   class_dict[field_name] = Field(
                       default=getattr(field_info, 'default', Undefined),
                       default_factory=getattr(field_info, 'default_factory', Undefined),
                       sa_column=getattr(field_info, 'sa_column', Undefined),
                       sa_column_args=getattr(field_info, 'sa_column_args', Undefined),
                       sa_column_kwargs=sa_kwargs,
                       primary_key=True,
                   )
            new_annotations[field_name] = field_type

        class_dict['__annotations__'] = new_annotations

        return super().__new__(cls, name, bases, class_dict, **kwargs)
