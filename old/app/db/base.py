from sqlalchemy.orm import DeclarativeBase, declared_attr

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Automatically generate table names from class names if not given
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
