# app/models/mnist.py
from sqlalchemy import LargeBinary, Column, Integer
from app.db.base import Base


class Mnist(Base):
    """
    Database model for MNIST dataset samples.

    Attributes:
        id (int): Primary key.
        digit (int): Digit label (0–9).
        sample_index (int): Index of the sample within the dataset.
        image_data (bytes): Raw binary image data of the handwritten digit.
    """
    __tablename__ = "mnist"
    id = Column(Integer, primary_key=True, index=True)
    digit = Column(Integer, nullable=False, index=True)
    sample_index = Column(Integer, nullable=False)
    image_data = Column(LargeBinary, nullable=False)
