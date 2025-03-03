from abc import abstractmethod
from typing import Any, Optional, Iterable, Literal

from daomodel import DAOModel


class ModelDiff(dict[str, tuple[Any, Any]]):
    """A dictionary wrapper to provided extended functionality for model comparisons."""
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
        """Returns the left value for the specified field."""
        return self.get(field)[0]

    def get_right(self, field: str) -> Any:
        """Returns the right value for the specified field."""
        return self.get(field)[1]

    @abstractmethod
    def get_preferred(self, field: str) -> Literal['left', 'right', 'neither', 'both']:
        """Defines which of the different values is preferred.

        'neither' and 'both' may be redundant depending on the application.
        They are differentiated in the case of specifying "these are both bad" and "these are both acceptable".

        :param field: The name of the field
        :return: 'left', 'right', 'neither', or 'both'
        :raises: ValueError if the field is invalid or otherwise not included in this diff
        """
        raise NotImplementedError(f'Cannot determine which value is preferred for {field}: '
                                  f'{self.get_left(field)} -> {self.get_right(field)}')
