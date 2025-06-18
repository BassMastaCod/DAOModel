from sqlmodel import desc

from daomodel import UnsearchableError
from daomodel.dao import SearchResults
from daomodel.util import MissingInput, LessThan, GreaterThan, GreaterThanEqualTo, LessThanEqualTo, Between, \
    AnyOf, NoneOf, IsSet, is_set, NotSet, not_set
from tests.school_models import *


def test_find__all(student_dao: DAO):
    assert student_dao.find() == SearchResults(all_students)


def test_first__multiple_results(student_dao: DAO):
    assert student_dao.find().first() == all_students[0]


def test_only__multiple_results(student_dao: DAO):
    with pytest.raises(ValueError):
        student_dao.find().only()


def test_find__single_result(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(100)
    assert dao.find() == SearchResults([Student(id=100)])


def test_first__single_result(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(100)
    assert dao.find().first() == Student(id=100)


def test_only__single_result(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(100)
    assert dao.find().only() == Student(id=100)


def test_find__no_results(daos: TestDAOFactory):
    assert daos[Student].find() == SearchResults([])


def test_first__no_results(daos: TestDAOFactory):
    assert daos[Student].find().first() is None


def test_only__no_results(daos: TestDAOFactory):
    with pytest.raises(ValueError):
        daos[Student].find().only()


def test_find__limit(student_dao: DAO):
    assert student_dao.find(per_page=5) == SearchResults(page_one, total=len(all_students), page=1, per_page=5)


def test_find__fewer_results_than_limit(student_dao: DAO):
    assert student_dao.find(per_page=15) == SearchResults(all_students, page=1, per_page=15)


def test_find__subsequent_page(student_dao: DAO):
    assert student_dao.find(per_page=5, page=2) == SearchResults(page_two, total=len(all_students), page=2, per_page=5)


def test_find__last_page(student_dao: DAO):
    assert student_dao.find(per_page=5, page=3) == SearchResults(page_three, total=len(all_students), page=3, per_page=5)


def test_find__undefined_page_size(daos: TestDAOFactory):
    with pytest.raises(MissingInput):
        daos[Student].find(page=1)


def test_find__filter_by_single_property(student_dao: DAO):
    assert student_dao.find(id=106) == SearchResults([Student(id=106)])


def test_find__filter_by_bool_property(student_dao: DAO):
    assert student_dao.find(active=True) == SearchResults(active)
    assert student_dao.find(active=False) == SearchResults(inactive)


def test_find__unsearchable_property(daos: TestDAOFactory):
    with pytest.raises(UnsearchableError):
        daos[Person].find(ssn=32)


def test_find__invalid_property(daos: TestDAOFactory):
    with pytest.raises(UnsearchableError):
        daos[Student].find(sex='m')


def test_find__filter_by_multiple_properties(student_dao: DAO):
    assert student_dao.find(gender='f', active=True) == SearchResults(active_females)


def test_find__is_set(student_dao: DAO):
    #assert student_dao.find(is_set_=Student.gender) == SearchResults(having_gender)
    assert student_dao.find(gender=IsSet()) == SearchResults(having_gender)
    assert student_dao.find(gender=is_set) == SearchResults(having_gender)


@pytest.mark.skip(reason='Not yet implemented')
def test_find__is_set_foreign_property(student_dao: DAO):
    assert student_dao.find(is_set_=Book.name) == SearchResults(having_book)


def test_find__is_set_unsearchable(student_dao: DAO):
    with pytest.raises(UnsearchableError):
        student_dao.find(is_set_=Hall.floor)


def test_find__not_set(student_dao: DAO):
    #assert student_dao.find(not_set_=Student.name) == SearchResults(not_having_name)
    assert student_dao.find(name=NotSet()) == SearchResults(not_having_name)
    assert student_dao.find(name=not_set) == SearchResults(not_having_name)


@pytest.mark.skip(reason='Not yet implemented')
def test_find__not_set_foreign_property(student_dao: DAO):
    assert student_dao.find(not_set_=Locker.number) == SearchResults(not_having_locker)


def test_find__condition_operator_unsearchable(person_dao: DAO):
    with pytest.raises(UnsearchableError):
        person_dao.find(ssn=is_set)


def test_find__filter_by_0_value(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(0)
    assert dao.find(id=0) == SearchResults([Student(id=0)])


def test_find__filter_by_foreign_property(school_dao: DAO):
    assert school_dao.find(**{'book.subject': 'Math'}) == SearchResults(having_math_book)


def test_find__filter_by_multiple_foreign_property(school_dao: DAO):
    filters = {'book.name': 'Calculus', 'book.subject': 'Math'}
    assert school_dao.find(**filters) == SearchResults([Student(id=103)])


def test_find__filter_by_different_foreign_tables(school_dao: DAO):
    filters = {'book.name': 'Biology 101', 'locker.number': 1101}
    assert school_dao.find(**filters) == SearchResults([Student(id=100)])


def test_find__filter_by_nested_foreign_property(school_dao: DAO):
    assert school_dao.find(**{'hall.color': 'blue'}) == SearchResults(in_blue_hall)


def test_find__filter_by_gt(school_dao: DAO):
    expected = [Student(id=109), Student(id=110), Student(id=111), Student(id=112)]
    assert school_dao.find(id=GreaterThan(108)) == SearchResults(expected)


def test_find__filter_by_gteq(school_dao: DAO):
    expected = [Student(id=108), Student(id=109), Student(id=110), Student(id=111), Student(id=112)]
    assert school_dao.find(id=GreaterThanEqualTo(108)) == SearchResults(expected)


def test_find__filter_by_lt(school_dao: DAO):
    expected = [Student(id=100), Student(id=101), Student(id=102), Student(id=103)]
    assert school_dao.find(id=LessThan(104)) == SearchResults(expected)


def test_find__filter_by_lteq(school_dao: DAO):
    expected = [Student(id=100), Student(id=101), Student(id=102), Student(id=103), Student(id=104)]
    assert school_dao.find(id=LessThanEqualTo(104)) == SearchResults(expected)


def test_find__filter_by_between(school_dao: DAO):
    expected = [Student(id=104), Student(id=105), Student(id=106), Student(id=107), Student(id=108)]
    assert school_dao.find(id=Between(104, 108)) == SearchResults(expected)


def test_find__filter_by_any_of(person_dao: DAO):
    expected = [
        Person(name='Greg', age=31),
        Person(name='John', age=23),
        Person(name='John', age=45)
    ]
    assert person_dao.find(name=AnyOf('John', 'Greg')) == SearchResults(expected)


def test_find__filter_by_none_of(person_dao: DAO):
    expected = [
        Person(name='Mike', age=18),
        Person(name='Mike', age=25),
        Person(name='Paul', age=25)
    ]
    assert person_dao.find(name=NoneOf('John', 'Joe', 'Greg')) == SearchResults(expected)


def test_find__default_order(person_dao: DAO):
    assert person_dao.find() == SearchResults(pk_ordered)


def test_find__specified_order(person_dao: DAO):
    assert person_dao.find(order=Person.age) == SearchResults(age_ordered)


def test_find__reverse_order(student_dao: DAO):
    assert student_dao.find(order=desc(Student.id)) == SearchResults(list(reversed(all_students)))


def test_find__order_without_table(person_dao: DAO):
    assert person_dao.find(order='age') == SearchResults(age_ordered)


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
    assert student_dao.find(order=order) == SearchResults(ordered)


def test_find__order_by_foreign_property(school_dao: DAO):
    ordered = [Student(id=101), Student(id=100), Student(id=103), Student(id=102)]
    assert school_dao.find(order=Book.name) == SearchResults(ordered)


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
    assert school_dao.find(order=Hall.color) == SearchResults(ordered)


def test_find__order_by_unsearchable(daos: TestDAOFactory):
    with pytest.raises(UnsearchableError):
        daos[Person].find(order=Person.ssn)


def test_find__duplicate(person_dao: DAO):
    assert person_dao.find(duplicate=Person.name) == SearchResults(duplicated_names)


def test_find__duplicate_foreign_property(school_dao: DAO):
    assert school_dao.find(duplicate=Book.subject) == SearchResults([Student(id=102), Student(id=103)])


def test_find__duplicate_unsearchable(daos: TestDAOFactory):
    with pytest.raises(UnsearchableError):
        daos[Person].find(duplicate=Person.ssn)


def test_find__unique(person_dao: DAO):
    assert person_dao.find(unique=Person.name) == SearchResults(unique_names)


def test_find__unique_foreign_property(school_dao: DAO):
    assert school_dao.find(unique=Book.subject) == SearchResults([Student(id=100), Student(id=101)])


def test_find__unique_unsearchable(daos: TestDAOFactory):
    with pytest.raises(UnsearchableError):
        daos[Person].find(unique=Person.ssn)


def test_find__duplicate_and_unique(person_dao: DAO):
    expected = [
        Person(name='John', age=23),
        Person(name='John', age=45),
        Person(name='Mike', age=18)
    ]
    assert person_dao.find(duplicate=Person.name, unique=Person.age) == SearchResults(expected)


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
    assert result.split('[')[0] == 'Page 2; 5 of 13 results '
