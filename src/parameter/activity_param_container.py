from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class ActivityParamContainer:
    feasible_start: float
    feasible_end: float
    constant: float = 0
    des_timing_mean: float = 0
    des_timing_std: float = 0
    pen_early: float = 0
    pen_late: float = 0
    des_duration_mean: float = 0
    des_duration_std: float = 0
    pen_short: float = 0
    pen_long: float = 0


@dataclass(frozen=True)
class ActivityParam:
    param: Dict[Tuple[str, str], ActivityParamContainer]
