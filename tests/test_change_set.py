from datetime import date
from typing import Optional, Any

import pytest

from daomodel import DAOModel, PrimaryKey
from daomodel.dao import Conflict
from daomodel.model_diff import ChangeSet
from tests.labeled_tests import labeled_tests


class CalendarEvent(DAOModel, table=True):
    title: str = PrimaryKey
    day: date
    time: Optional[str] = 'All Day'
    location: Optional[str]
    description: Optional[str]


dads_entry = CalendarEvent(
    title='Family Picnic',
    day=date(2025, 6, 20),
    time='11:00 AM',
    location='Central Park',
    description='Annual family picnic with games and BBQ.'
)
moms_entry = CalendarEvent(
    title='Family Picnic',
    day=date(2025, 6, 20),
    time='12:00 PM',
    location='Central Park',
    description='Picnic with family and friends, do not forget the salads!'
)
sons_entry = CalendarEvent(
    title='Family Picnic',
    day=date(2025, 6, 19),
    time='12:00 PM',
    description='Bring your football and frisbee!'
)
daughters_entry = CalendarEvent(
    title='Family Picnic',
    day=date(2025, 6, 20),
    time='All Day',
    location='Central Park'
)
unrelated_entry = CalendarEvent(
    title='Dentist Appointment',
    day=date(2025, 7, 1)
)


class EventChangeSet(ChangeSet):
    def resolve_conflict(self, field: str) -> Any:
        match field:
            case 'title':
                raise Conflict(msg='Unexpected conflict for title field')
            case 'day':
                return max(self.get_baseline(field), self.get_target(field))
            case 'time':
                return min(self.get_baseline(field), self.get_target(field))
            case 'location':
                return self.get_target(field)
            case 'description':
                return '\n\n'.join([self.get_target(field), self.get_baseline(field)])
            case _:
                raise NotImplementedError(f'The field {field} is not supported')


def test_change_set():
    assert 'title' not in ChangeSet(dads_entry, unrelated_entry)


def test_change_set__include_pk():
    assert 'title' in ChangeSet(dads_entry, unrelated_entry, include_pk=True)


def test_get_baseline_get_target():
    change_set = ChangeSet(dads_entry, moms_entry)
    assert change_set.get_baseline('time') == change_set.get_left('time') == '11:00 AM'
    assert change_set.get_target('time') == change_set.get_right('time') == '12:00 PM'


def test_get_resolution():
    assert ChangeSet(dads_entry, moms_entry).get_resolution('time') == '12:00 PM'
    assert ChangeSet(moms_entry, dads_entry).get_resolution('time') == '11:00 AM'


@labeled_tests({
    'left': [
        (dads_entry, sons_entry, 'location', 'left'),
        (dads_entry, daughters_entry, 'time', 'left'),
        (dads_entry, daughters_entry, 'description', 'left'),
        (sons_entry, daughters_entry, 'time', 'left'),
        (sons_entry, daughters_entry, 'description', 'left')
    ],
    'right': [
        (sons_entry, moms_entry, 'location', 'right'),
        (daughters_entry, moms_entry, 'time', 'right'),
        (daughters_entry, moms_entry, 'description', 'right'),
        (sons_entry, daughters_entry, 'location', 'right')
    ],
    'both': [
        (dads_entry, moms_entry, 'time', 'both'),
        (dads_entry, moms_entry, 'description', 'both'),
        (moms_entry, sons_entry, 'day', 'both')
    ]
})
def test_get_preferred(baseline: CalendarEvent, target: CalendarEvent, field: str, expected: str):
    assert ChangeSet(baseline, target).get_preferred(field) == expected


@labeled_tests({
    'dad => mom':
        (dads_entry, moms_entry, {
            'description': ('Annual family picnic with games and BBQ.', 'Picnic with family and friends, do not forget the salads!',
                            'Picnic with family and friends, do not forget the salads!\n\nAnnual family picnic with games and BBQ.')
        }),
    'dad => son':
        (dads_entry, sons_entry, {
            'description': ('Annual family picnic with games and BBQ.', 'Bring your football and frisbee!',
                            'Bring your football and frisbee!\n\nAnnual family picnic with games and BBQ.')
        }),
    'dad => daughter':
        (dads_entry, daughters_entry, {}),
    'mom => dad':
        (moms_entry, dads_entry, {
            'time': ('12:00 PM', '11:00 AM'),
            'description': ('Picnic with family and friends, do not forget the salads!', 'Annual family picnic with games and BBQ.',
                            'Annual family picnic with games and BBQ.\n\nPicnic with family and friends, do not forget the salads!')
        }),
    'mom => son':
        (moms_entry, sons_entry, {
            'description': ('Picnic with family and friends, do not forget the salads!', 'Bring your football and frisbee!',
                            'Bring your football and frisbee!\n\nPicnic with family and friends, do not forget the salads!')
        }),
    'mom => daughter':
        (moms_entry, daughters_entry, {}),
    'son => dad':
        (sons_entry, dads_entry, {
            'day': (date(2025, 6, 19), date(2025, 6, 20)),
            'time': ('12:00 PM', '11:00 AM'),
            'location': (None, 'Central Park'),
            'description': ('Bring your football and frisbee!', 'Annual family picnic with games and BBQ.',
                            'Annual family picnic with games and BBQ.\n\nBring your football and frisbee!')
        }),
    'son => mom':
        (sons_entry, moms_entry, {
            'day': (date(2025, 6, 19), date(2025, 6, 20)),
            'location': (None, 'Central Park'),
            'description': ('Bring your football and frisbee!', 'Picnic with family and friends, do not forget the salads!',
                            'Picnic with family and friends, do not forget the salads!\n\nBring your football and frisbee!')
        }),
    'son => daughter':
        (sons_entry, daughters_entry, {
            'day': (date(2025, 6, 19), date(2025, 6, 20)),
            'location': (None, 'Central Park')
        }),
    'daughter => dad':
        (daughters_entry, dads_entry, {
            'time': ('All Day', '11:00 AM'),
            'description': (None, 'Annual family picnic with games and BBQ.')
        }),
    'daughter => mom':
        (daughters_entry, moms_entry, {
            'time': ('All Day', '12:00 PM'),
            'description': (None, 'Picnic with family and friends, do not forget the salads!')
        }),
    'daughter => son':
        (daughters_entry, sons_entry, {
            'time': ('All Day', '12:00 PM'),
            'description': (None, 'Bring your football and frisbee!')
        }),
})
def test_resolve_preferences(baseline: CalendarEvent, target: CalendarEvent, expected: dict[str, tuple[Any, Any]|tuple[Any, Any, Any]]):
    change_set = EventChangeSet(baseline, target)
    change_set.resolve_preferences()
    assert change_set == expected


def test_resolve_preferences__conflict():
    with pytest.raises(Conflict):
        assert ChangeSet(dads_entry, moms_entry).resolve_preferences()
