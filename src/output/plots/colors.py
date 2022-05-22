from typing import List

_colors = {"work": "#C60018",
           "education": "#2d327d",
           "leisure": '#00973B',
           "shopping": '#FCBB00',
           "accompany": '#E84E10',
           "business": '#FFDE15',
           "other": '#6F2282',
           "travel": '#444444',
           "home": '#D2D2D2',
           "dawn": '#D2D2D2',
           "dusk": '#D2D2D2',
           'all': "#C60018"}
_default_color = '#0079C7'


def get_activity_hierarchy() -> List[str]:
    return [*_colors.keys()]


def get_color_for_act_type(act_type: str) -> str:
    return _colors.get(act_type, _default_color)
