from daomodel.search_util import *


def test_from_str__equals():
    op = ConditionOperator.from_str('value')
    assert isinstance(op, Equals)
    assert op.values == ('value',)

    op = ConditionOperator.from_str('is:value')
    assert isinstance(op, Equals)
    assert op.values == ('value',)


def test_from_str__lt():
    op = ConditionOperator.from_str('lt:5')
    assert isinstance(op, LessThan)
    assert op.values == ('5',)


def test_from_str__le():
    op = ConditionOperator.from_str('le:5')
    assert isinstance(op, LessThanEqualTo)
    assert op.values == ('5',)


def test_from_str__gt():
    op = ConditionOperator.from_str('gt:5')
    assert isinstance(op, GreaterThan)
    assert op.values == ('5',)


def test_from_str__ge():
    op = ConditionOperator.from_str('ge:5')
    assert isinstance(op, GreaterThanEqualTo)
    assert op.values == ('5',)


def test_from_str__between():
    op = ConditionOperator.from_str('between:1|5')
    assert isinstance(op, Between)
    assert op.values == ('1', '5')


def test_from_str__anyof():
    op = ConditionOperator.from_str('anyof:1|2|3')
    assert isinstance(op, AnyOf)
    assert op.values == ('1', '2', '3')


def test_from_str__noneof():
    op = ConditionOperator.from_str('noneof:1|2|3')
    assert isinstance(op, NoneOf)
    assert op.values == ('1', '2', '3')


def test_from_str__isset():
    assert isinstance(ConditionOperator.from_str('is:set'), IsSet)


def test_from_str__notset():
    assert isinstance(ConditionOperator.from_str('is:notset'), NotSet)


def test_from_str__part():
    op = ConditionOperator.from_str('part_is:5')
    assert isinstance(op, Equals)
    assert op.values == (5,)
    assert op.part == 'part'
