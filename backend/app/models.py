from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Habit(Base):
    """Alışkanlık modeli. recurrence_type: daily, weekly, monthly."""

    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Tekrarlama: daily | weekly | monthly
    recurrence_type = Column(String(20), default="daily", nullable=False)
    # Haftalık: virgülle ayrılmış haftanın günleri (0=Pzt .. 6=Paz)
    weekly_days = Column(String(50), nullable=True)
    # Aylık: ayın günü (1-31)
    monthly_day = Column(Integer, nullable=True)
    # Hex renk (ör. #FF00FF). Varsayılan neon renk aralığından atanır.
    color = Column(String(7), nullable=True)

    daily_logs = relationship("DailyLog", back_populates="habit", cascade="all, delete-orphan")


class DailyLog(Base):
    """Hangi alışkanlığın hangi gün yapıldığını tutar."""

    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(Date, nullable=False)
    is_completed = Column(Boolean, default=False)

    habit = relationship("Habit", back_populates="daily_logs")


class DailyMetric(Base):
    """Akıllı alışkanlıklar için günlük metrikler (su, adım)."""

    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    water_ml = Column(Integer, default=0, nullable=False)
    steps = Column(Integer, default=0, nullable=False)


class Event(Base):
    """Takvim etkinlikleri."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    title = Column(String(255), nullable=False)
    color = Column(String(7), nullable=True)
