from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    transcript = Column(Text, nullable=False)
    summary = Column(Text)
    validation = Column(Text)
    followups = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    discussions = relationship(
        "Discussion",
        back_populates="meeting",
        cascade="all, delete"
    )

    decisions = relationship(
        "Decision",
        back_populates="meeting",
        cascade="all, delete"
    )

    action_items = relationship(
        "ActionItemDB",
        back_populates="meeting",
        cascade="all, delete"
    )


class Discussion(Base):
    __tablename__ = "discussions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    discussion = Column(Text, nullable=False)

    meeting = relationship(
        "Meeting",
        back_populates="discussions"
    )


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    decision = Column(Text, nullable=False)

    meeting = relationship(
        "Meeting",
        back_populates="decisions"
    )


class ActionItemDB(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))

    task = Column(Text, nullable=False)
    assigned_to = Column(Text)
    deadline = Column(Text)

    meeting = relationship(
        "Meeting",
        back_populates="action_items"
    )