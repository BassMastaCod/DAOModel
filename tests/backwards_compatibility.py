from typing import Optional

from sqlmodel import Field, Relationship

from daomodel import DAOModel


class SQLModel(DAOModel, table=True):
    id: int = Field(primary_key=True)
    parent: Optional['SQLModel'] = Relationship(back_populates='children')
    children: list['SQLModel'] = Relationship(back_populates='parent')
    _private: list[str]

def test_sqlmodel_backwards_compatibility() -> None:
    pass
