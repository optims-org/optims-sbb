from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    name: str
    x_coord: float = None
    y_coord: float = None

    def __str__(self):
        return str(self.name)
