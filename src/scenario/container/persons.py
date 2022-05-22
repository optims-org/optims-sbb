from dataclasses import dataclass


@dataclass(frozen=True)
class Person:
    name: str
    activity_scoring_group: str = None
