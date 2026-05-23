from daomodel.dao import SearchStream
from tests.school_models import *


def test_stream__iter(student_dao: DAO):
    count = 0
    for student in student_dao.stream():
        count += 1
        if count >= 3:  # Just test first few
            break
    assert count == 3


def test_stream__iter__multiple_times(student_dao: DAO):
    stream = student_dao.stream()
    first_iteration = list(stream)
    second_iteration = list(stream)
    assert first_iteration == all_students
    assert second_iteration == all_students
    assert first_iteration == second_iteration


def test_stream_first__multiple_results(student_dao: DAO):
    stream = student_dao.stream()
    assert stream.first() == all_students[0]


def test_stream_first__single_result(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(100)
    stream = dao.stream()
    assert stream.first() == Student(id=100)


def test_stream_first__no_results(daos: TestDAOFactory):
    stream = daos[Student].stream()
    assert stream.first() is None


def test_stream_only__single_result(daos: TestDAOFactory):
    dao = daos[Student]
    dao.create(100)
    stream = dao.stream(id=100)
    assert stream.only() == Student(id=100)


def test_stream_only__multiple_results(student_dao: DAO):
    stream = student_dao.stream()
    with pytest.raises(ValueError, match='Expected exactly one result, got more than 1'):
        stream.only()


def test_stream_only__no_results(daos: TestDAOFactory):
    stream = daos[Student].stream(id=9999)
    with pytest.raises(ValueError, match='Expected exactly one result, got 0'):
        stream.only()


# TODO: this doesn't actually test what it claims
def test_search_stream__lazy_evaluation(student_dao: DAO):
    stream = student_dao.stream()

    # Getting the stream object shouldn't execute the query yet
    assert isinstance(stream, SearchStream)

    # Only when we iterate should we get results
    first_result = next(iter(stream))
    assert first_result is not None
    assert isinstance(first_result, Student)


def test_stream__consistency_with_find(student_dao: DAO):
    find_results = student_dao.find()
    stream_results = list(student_dao.stream())
    assert stream_results == list(find_results)


def test_stream__consistency_with_find__filtered(student_dao: DAO):
    find_results = student_dao.find(active=True)
    stream_results = list(student_dao.stream(active=True))
    assert stream_results == list(find_results)


def test_stream__consistency_with_find__ordered(student_dao: DAO):
    find_results = student_dao.find(_order='!id')
    stream_results = list(student_dao.stream(_order='!id'))
    assert stream_results == list(find_results)
