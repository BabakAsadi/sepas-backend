from sqlalchemy import Column, Integer, String

from app.database.base import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(String, nullable=False)
    name = Column(String, nullable=False)
    field = Column(String, nullable=False)