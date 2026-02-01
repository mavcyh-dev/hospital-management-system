from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect


class Base(DeclarativeBase):
    def __repr__(self):
        mapper = inspect(self.__class__)
        attrs = []
        for col in mapper.columns:
            value = getattr(self, col.name)
            attrs.append(f"{col.name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"