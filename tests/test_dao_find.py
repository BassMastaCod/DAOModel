import pytest
from sqlmodel import desc

from daomodel import Unsearchable
from daomodel.dao import DAO, SearchResults
from daomodel.util import MissingInput
from tests.conftest import all_students, TestDAOFactory, Student, Person, page_one, page_two, page_three, age_ordered, \
    pk_ordered, duplicated_names, active, inactive, active_females, having_gender, not_having_name, unique_names, Book, \
    Hall


def test_find__all(student_dao: DAO):
    assert student_dao.find() == SearchResults(all_students, total=len(all_students))


def test_find__single_result(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(100)
    assert dao.find() == SearchResults([Student(id=100)], total=1)


def test_find__no_results(daos: TestDAOFactory):
    assert daos[Student].find() == SearchResults([], total=0)


def test_find__limit(student_dao: DAO):
    assert student_dao.find(per_page=5) == SearchResults(page_one, total=len(all_students), page=1, per_page=5)


def test_find__fewer_results_than_limit(student_dao: DAO):
    assert student_dao.find(per_page=15) == SearchResults(all_students, total=len(all_students), page=1, per_page=15)


def test_find__subsequent_page(student_dao: DAO):
    assert student_dao.find(per_page=5, page=2) == SearchResults(page_two, total=len(all_students), page=2, per_page=5)


def test_find__last_page(student_dao: DAO):
    assert student_dao.find(per_page=5, page=3) == SearchResults(page_three, total=len(all_students), page=3, per_page=5)


def test_find__undefined_page_size(daos: TestDAOFactory):
    with pytest.raises(MissingInput):
        daos[Student].find(page=1)


def test_find__filter_by_single_property(student_dao: DAO):
    expected = [Student(id=106)]
    assert student_dao.find(id=106) == SearchResults(expected, total=len(expected))


def test_find__filter_by_bool_property(student_dao: DAO):
    assert student_dao.find(active=True) == SearchResults(active, total=len(active))
    assert student_dao.find(active=False) == SearchResults(inactive, total=len(inactive))


def test_find__unsearchable_property(daos: TestDAOFactory):
    with pytest.raises(Unsearchable):
        daos[Person].find(ssn=32)


def test_find__invalid_property(daos: TestDAOFactory):
    with pytest.raises(Unsearchable):
        daos[Student].find(sex="m")


def test_find__filter_by_multiple_properties(student_dao: DAO):
    assert student_dao.find(gender="f", active=True) == SearchResults(active_females, total=len(active_females))


def test_find__filter_by_property_is_set(student_dao: DAO):
    assert student_dao.find(gender=True) == SearchResults(having_gender, total=len(having_gender))
    assert student_dao.find(gender="true") == SearchResults(having_gender, total=len(having_gender))
    assert student_dao.find(gender="yes") == SearchResults(having_gender, total=len(having_gender))


def test_find__filter_by_property_not_set(student_dao: DAO):
    assert student_dao.find(name=False) == SearchResults(not_having_name, total=len(not_having_name))
    assert student_dao.find(name="false") == SearchResults(not_having_name, total=len(not_having_name))
    assert student_dao.find(name="no") == SearchResults(not_having_name, total=len(not_having_name))


def test_find__filter_by_0_value(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(0)
    expected = [Student(id=0)]
    assert dao.find(id=0) == SearchResults(expected, total=len(expected))


def test_find__filter_by_foreign_property(school_dao: DAO):
    expected = [Student(id=102), Student(id=103)]
    assert school_dao.find(**{"book.subject": "Math"}) == SearchResults(expected, total=len(expected))


def test_find__filter_by_multiple_foreign_property(school_dao: DAO):
    expected = [Student(id=103)]
    filters = {"book.name": "Calculus", "book.subject": "Math"}
    assert school_dao.find(**filters) == SearchResults(expected, total=len(expected))


def test_find__filter_by_different_foreign_tables(school_dao: DAO):
    expected = [Student(id=100)]
    filters = {"book.name": "Biology 101", "locker.number": 1101}
    assert school_dao.find(**filters) == SearchResults(expected, total=len(expected))


def test_find__filter_by_nested_foreign_property(school_dao: DAO):
    expected = [Student(id=102), Student(id=107), Student(id=110)]
    assert school_dao.find(**{"hall.color": "blue"}) == SearchResults(expected, total=len(expected))


def test_find__default_order(person_dao: DAO):
    assert person_dao.find() == SearchResults(pk_ordered, total=len(pk_ordered))


def test_find__specified_order(person_dao: DAO):
    assert person_dao.find(order=Person.age) == SearchResults(age_ordered, total=len(age_ordered))


def test_find__reverse_order(student_dao: DAO):
    assert student_dao.find(order=desc(Student.id)) == SearchResults(list(reversed(all_students)), total=len(all_students))


def test_find__order_without_table(person_dao: DAO):
    assert person_dao.find(order="age") == SearchResults(age_ordered, total=len(age_ordered))


def test_find__order_by_multiple_properties(student_dao: DAO):
    ordered = [
        Student(id=111),
        Student(id=106),
        Student(id=107),
        Student(id=102),
        Student(id=110),
        Student(id=112),
        Student(id=109),
        Student(id=108),
        Student(id=105),
        Student(id=101),
        Student(id=103),
        Student(id=104),
        Student(id=100)
    ]
    order = (Student.active, Student.gender, desc(Student.name))
    assert student_dao.find(order=order) == SearchResults(ordered, total=len(ordered))


def test_find__order_by_foreign_property(school_dao: DAO):
    ordered = [Student(id=101), Student(id=100), Student(id=103), Student(id=102)]
    assert school_dao.find(order=Book.name) == SearchResults(ordered, total=len(ordered))


def test_find__order_by_nested_foreign_property(school_dao: DAO):
    ordered = [
        Student(id=107),
        Student(id=110),
        Student(id=102),
        Student(id=100),
        Student(id=108),
        Student(id=103),
        Student(id=104),
        Student(id=109),
        Student(id=101),
        Student(id=106),
        Student(id=111),
        Student(id=105)
    ]
    assert school_dao.find(order=Hall.color) == SearchResults(ordered, total=len(ordered))


def test_find__order_by_unsearchable(daos: TestDAOFactory):
    with pytest.raises(Unsearchable):
        daos[Person].find(order=Person.ssn)


def test_find__duplicate(person_dao: DAO):
    assert person_dao.find(duplicate=Person.name) == SearchResults(duplicated_names, total=len(duplicated_names))


def test_find__duplicate_foreign_property(school_dao: DAO):
    expected = [Student(id=102), Student(id=103)]
    assert school_dao.find(duplicate=Book.subject) == SearchResults(expected, total=len(expected))


def test_find__duplicate_unsearchable(daos: TestDAOFactory):
    with pytest.raises(Unsearchable):
        daos[Person].find(duplicate=Person.ssn)


def test_find__unique(person_dao: DAO):
    assert person_dao.find(unique=Person.name) == SearchResults(unique_names, total=len(unique_names))


def test_find__unique_foreign_property(school_dao: DAO):
    expected = [Student(id=100), Student(id=101)]
    assert school_dao.find(unique=Book.subject) == SearchResults(expected, total=len(expected))


def test_find__unique_unsearchable(daos: TestDAOFactory):
    with pytest.raises(Unsearchable):
        daos[Person].find(unique=Person.ssn)


def test_find__duplicate_and_unique(person_dao: DAO):
    expected = [
        Person(name="John", age=23),
        Person(name="John", age=45),
        Person(name="Mike", age=18)
    ]
    assert person_dao.find(duplicate=Person.name, unique=Person.age) == SearchResults(expected, total=len(expected))


def test_search_results__iter(student_dao: DAO):
    student_id = 100
    for student in student_dao.find():
        assert student.id == student_id
        student_id += 1


def test_search_results__eq_hash(student_dao: DAO):
    first = student_dao.find()
    second = student_dao.find()
    assert first == second
    assert hash(first) == hash(second)


def test_search_results__eq_hash__different_order(student_dao: DAO):
    first = student_dao.find(order=Student.name)
    second = student_dao.find(order=desc(Student.name))
    assert first != second
    assert hash(first) != hash(second)


def test_search_results__str(student_dao: DAO):
    results = student_dao.find()
    assert str(results) == str(list(results))


def test_search_results__str__page(student_dao: DAO):
    result = str(student_dao.find(page=2, per_page=5))
    assert result.split("[")[0] == "Page 2; 5 of 13 results "
