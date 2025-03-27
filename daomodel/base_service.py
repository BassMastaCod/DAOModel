from daomodel import DAOModel, all_models
from daomodel.db import DAOFactory
from daomodel.model_diff import ChangeSet, Preference


SOURCE_VALUE = Preference.RIGHT
DESTINATION_VALUE = Preference.LEFT


class BaseService:
    """A base for service layers specifically designed around DAOModels."""
    def __init__(self, daos: DAOFactory):
        self.daos = daos

    def merge(self, source: DAOModel, *destination_pk_values, **conflict_resolution) -> None:
        """Merges the given source model into the specified destination.

        In some cases, specify conflict_resolution to successfully merge values.

        :param source: The source DAOModel to be merged into the destination
        :param destination_pk_values: The primary key values indicating where to merge the model
        :raises: NotFound: if the destination model does not exist in the database
        :raises: Conflict: if the source model fails to merge into the destination
        """
        model_dao = self.daos[type(source)]
        destination = model_dao.get(*destination_pk_values)
        if type(destination) is not type(source):
            raise TypeError(f'{destination} is not of type {type(source)}')

        ChangeSet(destination, source, **conflict_resolution).resolve_preferences().apply()
        self._redirect_fks(source, destination)
        model_dao.update(destination)
        model_dao.remove(source)

    def _redirect_fks(self, source: DAOModel, destination: DAOModel) -> None:
        for model in all_models(self.daos.db.get_bind()):
            model_dao = self.daos[model]
            for column in model.get_references_of(source):
                old_value = source.get_value_of(column)
                new_value = destination.get_value_of(column)
                model_dao.query.where(column == old_value).update({column: new_value})
