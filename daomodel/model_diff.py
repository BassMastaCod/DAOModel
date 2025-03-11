from abc import abstractmethod
from typing import Any, Optional, Iterable, Literal, Self

from daomodel import DAOModel
from daomodel.dao import Conflict


class ModelDiff(dict[str, tuple[Any, Any]|tuple[Any, Any, Any]]):
    """A dictionary wrapper to provide extended functionality for model comparisons."""
    def __init__(self, left: DAOModel, right: DAOModel, include_pk: Optional[bool] = True):
        super().__init__()
        self.left = left
        self.right = right
        self.update(left.compare(right, include_pk=include_pk))

    @property
    def fields(self) -> Iterable[str]:
        """The fields that have different values between the two models."""
        return self.keys()

    def get_left(self, field: str) -> Any:
        """Fetches the value of the left model.

        :param field: The name of the field to fetch
        :return: The left value for the specified field
        :raises: KeyError if the field is invalid or otherwise not included in this diff
        """
        if field not in self:
            raise KeyError(f'{field} not found in diff.')
        return self.get(field)[0]

    def get_right(self, field: str) -> Any:
        """Fetches the value of the right model.

        :param field: The name of the field to fetch
        :return: The right value for the specified field
        :raises: KeyError if the field is invalid or otherwise not included in this diff
        """
        if field not in self:
            raise KeyError(f'{field} not found in diff.')
        return self.get(field)[1]

    @abstractmethod
    def get_preferred(self, field: str) -> Literal['left', 'right', 'neither', 'both', 'n/a']:
        """Defines which of the varying values is preferred.

        'neither' and 'both' may be redundant depending on the application.
        They are differentiated in the case of specifying "these are both bad" and "these are both acceptable".
        'n/a' is used when it does not make sense to have a preference i.e. the name field of two customers.

        :param field: The name of the field
        :return: 'left', 'right', 'neither', 'both', or 'n/a'
        :raises: KeyError if the field is invalid or otherwise not included in this diff
        """
        raise NotImplementedError(f'Cannot determine which value is preferred for {field}: '
                                  f'{self.get_left(field)} -> {self.get_right(field)}')


class ChangeSet(ModelDiff):
    """A directional model diff with the left being the baseline and the right being the target.

    Unlike the standard ModelDiff, PK is excluded by default.
    """
    def __init__(self, baseline: DAOModel, target: DAOModel, include_pk: Optional[bool] = False):
        super().__init__(baseline, target, include_pk)
        self.baseline = self.left
        self.target = self.right
        self.assigned_in_baseline = self.baseline.get_property_names(assigned=True)
        self.assigned_in_target = self.target.get_property_names(assigned=True)

    def get_baseline(self, field: str) -> Any:
        """Fetches the value of the baseline model.

        :param field: The name of the field to fetch
        :return: The baseline value for the specified field
        :raises: KeyError if the field is invalid or otherwise not included in this diff
        """
        return self.get(field)[0]

    def get_target(self, field: str) -> Any:
        """Fetches the value of the target model.

        :param field: The name of the field to fetch
        :return: The target value for the specified field
        :raises: KeyError if the field is invalid or otherwise not included in this diff
        """
        return self.get(field)[1]

    def get_resolution(self, field: str) -> Any:
        """Returns the resolved value for the specified field.

        This will be the new value for the specified field if the change set were to be applied.

        :param field: The name of the field to fetch
        :return: The resolved value, which is the target value unless resolve_preferences() was called
        """
        return self.get(field)[1]

    def get_preferred(self, field: str) -> Literal['left', 'right', 'neither', 'both', 'n/a']:
        return (
            'left' if self.get_target(field) is None else
            'both' if field in self.assigned_in_baseline and field in self.assigned_in_target else
            'left' if field in self.assigned_in_baseline else
            'right' if field in self.assigned_in_target else
            'neither'
        )

    def resolve_conflict(self, field: str) -> Any:
        """Designed to be overridden, this function defines how to handle conflicts.

        A conflict occurs when both the baseline and target have unique meaningful values for a field.

        :param field: The field having a conflict
        :return: The result of the resolution which may be the baseline value, target value, or something new entirely
        :raises: Conflict if a resolution cannot be determined
        """
        raise Conflict(msg=f'Unable to determine preferred result for {field}: '
                           f'{self.get_baseline(field)} -> {self.get_target(field)}')

    def resolve_preferences(self) -> Self:
        """Removes unwanted changes, preserving the meaningful values, regardless of them being from baseline or target

        :return: This ChangeSet to allow for chaining function calls
        :raises: Conflict if both baseline and target have meaningful values (unless resolve_conflict is overridden)
        """
        for field in list(self.fields):
            match self.get_preferred(field):
                case 'left' | 'neither':
                    del self[field]
                case 'both':
                    resolution = self.resolve_conflict(field)
                    if resolution == self.get_baseline(field):
                        del self[field]
                    elif resolution == self.get_target(field):
                        pass
                    else:
                        self[field] = (self.get_baseline(field), self.get_target(field), resolution)
                case 'right':
                    pass
        return self

    def apply(self) -> DAOModel:
        """Enacts these changes upon the baseline.

        You will typically want to call resolve_preferences prior to this.
        """
        self.baseline.set_values(**{field: self.get_resolution(field) for field in self.fields})
        return self.baseline
