import pytest

from daomodel.dao import DAO, NotFound, Conflict
from daomodel.util import MissingInput
from tests.conftest import TestDAOFactory, Student, Person, Book


def test_create__single_column(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create(100)
    assert model == Student(id=100)
    daos.assert_in_db(Student, 100)


def test_create__multi_column(daos: TestDAOFactory):
    model = daos[Person].create('John', 23)
    assert model == Person(name='John', age=23)
    daos.assert_in_db(Person, 'John', 23)


def test_create__default_fields(daos: TestDAOFactory):
    model = daos[Student].create(100)
    assert model.active
    daos.assert_in_db(Student, 100, active=True)


def test_create__required_fields(daos: TestDAOFactory):
    with pytest.raises(KeyError):
        daos[Person].create('John')


def test_create_with(daos: TestDAOFactory):
    model = daos[Student].create_with(id=100, name='Bob', active=False)
    assert model == Student(id=100, name='Bob', active=False)
    daos.assert_in_db(Student, 100, name='Bob', active=False)


def test_create_with__no_commit(daos: TestDAOFactory):
    model = daos[Student].create_with(False, id=100)
    assert model == Student(id=100)
    daos.assert_not_in_db(Student, 100)


def test_insert(daos: TestDAOFactory):
    daos[Student].insert(Student(id=100))
    daos.assert_in_db(Student, 100)


def test_insert__default_fields(daos: TestDAOFactory):
    model = Student(id=100)
    daos[Student].insert(model)
    assert model.active
    daos.assert_in_db(Student, 100, active=True)


def test_insert__conflict(daos: TestDAOFactory):
    dao = daos[Student]
    dao.insert(Student(id=100))
    daos.assert_in_db(Student, 100)
    with pytest.raises(Conflict):
        dao.insert(Student(id=100))


def test_update(daos: TestDAOFactory):
    dao = daos[Student]
    model = Student(id=100)
    dao.insert(model)
    assert model.name is None
    model.name = 'Bob'
    daos.assert_in_db(Student, 100, name=None)
    dao.update(model)
    daos.assert_in_db(Student, 100, name='Bob')


def test_update_missing(daos: TestDAOFactory):
    with pytest.raises(NotFound):
        daos[Student].update(Student(id=100, name='Bob'))


def test_upsert__new(daos: TestDAOFactory):
    daos[Student].upsert(Student(id=100, name='Bob'))
    daos.assert_in_db(Student, 100, name='Bob')


def test_upsert__existing(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create(100)
    model.name = 'Bob'
    daos.assert_in_db(Student, 100, name=None)
    dao.upsert(model)
    daos.assert_in_db(Student, 100, name='Bob')


def test_rename(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create(100)
    daos.assert_in_db(Student, 100)
    daos.assert_not_in_db(Student, 200)
    dao.rename(model, 200)
    daos.assert_not_in_db(Student, 100)
    daos.assert_in_db(Student, 200)


def test_rename__multiple_columns(daos: TestDAOFactory):
    dao = daos[Person]
    model = dao.create('Alfred', 51)
    daos.assert_in_db(Person, 'Alfred', 51)
    daos.assert_not_in_db(Person, 'Al', 51)

    dao.rename(model, 'Al', 51)
    daos.assert_not_in_db(Person, 'Alfred', 51)
    daos.assert_in_db(Person, 'Al', 51)

    dao.rename(model, 'Fred', 52)
    daos.assert_not_in_db(Person, 'Al', 51)
    daos.assert_in_db(Person, 'Fred', 52)

    dao.rename(model, 'Fred', 53)
    daos.assert_not_in_db(Person, 'Fred', 52)
    daos.assert_in_db(Person, 'Fred', 53)


def test_rename__keep_property_values(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create_with(id=100, name='Bob', gender='m', active=False)
    daos.assert_in_db(Student, 100, name='Bob', gender='m', active=False)
    daos.assert_not_in_db(Student, 200)
    dao.rename(model, 200)
    daos.assert_not_in_db(Student, 100)
    daos.assert_in_db(Student, 200, name='Bob', gender='m', active=False)


def test_rename__cascade_foreign_reference(daos: TestDAOFactory):
    student_dao = daos[Student]
    model = student_dao.create(100)
    daos[Book].create_with(name='Algebra I', subject='Math', owner=100)
    daos.assert_in_db(Book, 'Algebra I', subject='Math', owner=100)
    student_dao.rename(model, 200)
    daos.assert_in_db(Book, 'Algebra I', subject='Math', owner=200)


def test_rename__keep_foreign_key(daos: TestDAOFactory):
    daos[Student].create(100)
    book_dao = daos[Book]
    book = book_dao.create_with(name='Algebra I', subject='Math', owner=100)
    daos.assert_in_db(Book, 'Algebra I', subject='Math', owner=100)
    daos.assert_not_in_db(Book, 'Algebra II')
    book_dao.rename(book, 'Algebra II')
    daos.assert_not_in_db(Book, 'Algebra I')
    daos.assert_in_db(Book, 'Algebra II', subject='Math', owner=100)


def test_rename__already_exists(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create(100)
    dao.create(200)
    daos.assert_in_db(Student, 100)
    daos.assert_in_db(Student, 200)
    with pytest.raises(Conflict):
        dao.rename(model, 200)


def test_exists_true(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create(100)
    assert dao.exists(model)


def test_exists_false(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create_with(id=100, commit=False)
    assert not dao.exists(model)


def test_get__single_column(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create_with(id=100, name='Bob')
    model = DAO(Student, daos.assert_session).get(100)
    assert model.id == 100
    assert model.name == 'Bob'


def test_get__multiple_column(daos: TestDAOFactory):
    dao = daos[Person]
    dao.create_with(name='John', age=23)
    model = DAO(Person, daos.assert_session).get('John', 23)
    assert model.name == 'John'
    assert model.age == 23


def test_get__missing_column(daos: TestDAOFactory):
    with pytest.raises(MissingInput):
        daos[Person].get('John')


def test_get__not_found(daos: TestDAOFactory):
    with pytest.raises(NotFound):
        daos[Student].get(100)


def test_get_with(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create_with(id=100, name='Bob')
    model = DAO(Student, daos.assert_session).get_with(id=100, name='Mike')
    assert model.id == 100
    assert model.name == 'Mike'


def test_get_with__no_additional_data(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create_with(id=100, name='Bob')
    model = DAO(Student, daos.assert_session).get_with(id=100)
    assert model.id == 100
    assert model.name == 'Bob'


def test_get_with__blank_data(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create_with(id=100, name='Bob')
    model = DAO(Student, daos.assert_session).get_with(id=100, name=None)
    assert model.id == 100
    assert model.name is None


def test_get__missing_data(daos: TestDAOFactory):
    with pytest.raises(MissingInput):
        daos[Person].get_with(name='John')


def test_get_with__not_found(daos: TestDAOFactory):
    with pytest.raises(NotFound):
        daos[Student].get_with(id=100, name='Mike')


def test_remove(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create(100)
    daos.assert_in_db(Student, 100)
    dao.remove(model)
    daos.assert_not_in_db(Student, 100)


def test_remove__not_found(daos: TestDAOFactory):
    with pytest.raises(NotFound):
        daos[Student].remove(Student(id=100))


def test_commit(daos: TestDAOFactory):
    dao = daos[Student]
    model = dao.create(100)
    dao.remove(model, commit=False)
    daos.assert_in_db(Student, 100)
    dao.commit()
    daos.assert_not_in_db(Student, 100)
