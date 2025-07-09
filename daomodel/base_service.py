from typing import Any, Callable, List

from daomodel import DAOModel, all_models
from daomodel.db import DAOFactory
from daomodel.model_diff import ChangeSet, Preference


SOURCE_VALUE = Preference.RIGHT
DESTINATION_VALUE = Preference.LEFT


class BaseService:
    """An extendable base for creating a service layer for your DAOModel project.

    This service provides access to DAOs for model classes through the `daos` property.
    It also provides methods for operations involving your models.
    """
    def __init__(self, daos: DAOFactory):
        self.daos = daos

    def bulk_update(self, models: List[DAOModel], **common_values: Any) -> None:
        """Assigns values to multiple models in a single transaction.

        This is particularly useful for applying batch changes to a filtered set of records.
        ```python
        service.bulk_update(overdue_accounts, status='suspended')
        ```

        The method supports updating models of different types in a single operation,
        as long as the fields being updated are present in all model types.
        ```python
        no_longer_at_school = (school_service.daos[Student].find(graduated=True) +
                               school_service.daos[Staff].find(retired=True))
        service.bulk_update(no_longer_at_school, status='inactive', door_code=None)
        ```

        :param models: List of models to update (can be of different types)
        :param common_values: Values to set on all models
        """
        if not models:
            return

        # Group models by type
        models_by_type = {}
        for model in models:
            model_type = type(model)
            if model_type not in models_by_type:
                models_by_type[model_type] = []
            models_by_type[model_type].append(model)

        # Start a transaction on the first model type's DAO
        # This will be used for all model types
        if not models_by_type:
            return

        first_model_type = next(iter(models_by_type.keys()))
        transaction_dao = self.daos[first_model_type]
        transaction_dao.start_transaction()

        try:
            # Process each model type
            for model_type, model_list in models_by_type.items():
                model_dao = self.daos[model_type]
                for model in model_list:
                    model.set_values(**common_values)
                    model_dao.db.add(model)

            # Commit the transaction
            transaction_dao.commit()
        except Exception as e:
            transaction_dao.rollback()
            raise e


class SingleModelService(BaseService):
    """A service layer specifically designed around a single DAOModel.

    This service extends BaseService and provides access to the DAO for the primary model 
    through the `dao` property, allowing direct access to all DAO methods without creating 
    pass-through methods. It also provides additional methods that add value beyond simple 
    DAO operations.
    """
    def __init__(self, daos: DAOFactory, model_class: type[DAOModel]):
        super().__init__(daos)
        self.dao = daos[model_class]

    def merge(self, source: DAOModel, *destination_pk_values, **conflict_resolution: Preference|Callable|Any) -> None:
        """Merges the given source model into the specified destination.

        In some cases, specify conflict_resolution to successfully merge values.
        See the `ChangeSet` documentation for more details on conflict resolution.

        :param source: The source DAOModel to be merged into the destination
        :param destination_pk_values: The primary key values indicating where to merge the model
        :raises NotFound: if the destination model does not exist in the database
        :raises Conflict: if the source model fails to merge into the destination
        :raises TypeError: if source is not of the primary model type
        """
        model_dao = self.dao
        model_dao.start_transaction()
        destination = model_dao.get(*destination_pk_values)
        if type(source) is not self.dao.model_class:
            raise TypeError(f'{source} is not of type {self.dao.model_class}')

        ChangeSet(destination, source, **conflict_resolution).resolve_preferences().apply()
        self._redirect_fks(source, destination)
        model_dao.remove(source)
        model_dao.commit(destination)

    def _redirect_fks(self, source: DAOModel, destination: DAOModel) -> None:
        for model in all_models(self.daos.db.get_bind()):
            model_dao = self.daos[model]
            for column in model.get_references_of(source):
                old_value = source.get_value_of(column)
                new_value = destination.get_value_of(column)
                model_dao.query.where(column == old_value).update({column: new_value})
