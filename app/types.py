from enum import Enum


class PostFilter(Enum):
    ALL = 'all'
    FOLLOWED = 'followed'
    MYSELF = 'myself'

    @classmethod
    def by_value(cls, value, default=None):
        for member in cls:
            if member.value == value:
                return member
        return default
