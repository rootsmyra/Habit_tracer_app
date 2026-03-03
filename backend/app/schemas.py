from datetime import date, datetime
from pydantic import BaseModel, model_validator


class HabitBase(BaseModel):
    name: str
    color: str | None = None  # hex


class HabitCreate(HabitBase):
    recurrence_type: str = "daily"  # daily | weekly | monthly
    weekly_days: list[int] | None = None  # 0-6 (Pzt=0, Paz=6)
    monthly_day: int | None = None  # 1-31


class HabitResponse(HabitBase):
    id: int
    created_at: datetime
    recurrence_type: str = "daily"
    weekly_days: list[int] | None = None
    monthly_day: int | None = None

    class Config:
        from_attributes = True

    @model_validator(mode="wrap")
    @classmethod
    def parse_weekly_days(cls, data, handler):
        def to_list(s):
            if not s:
                return None
            if isinstance(s, list):
                return s
            return [int(x) for x in str(s).split(",") if x.strip()]

        if hasattr(data, "weekly_days"):
            wd = getattr(data, "weekly_days", None)
            data = {
                "id": data.id,
                "name": data.name,
                "color": getattr(data, "color", None),
                "created_at": data.created_at,
                "recurrence_type": getattr(data, "recurrence_type", None) or "daily",
                "weekly_days": to_list(wd),
                "monthly_day": getattr(data, "monthly_day", None),
            }
        elif isinstance(data, dict) and "weekly_days" in data:
            data = {**data, "weekly_days": to_list(data.get("weekly_days"))}
        return handler(data)


# --- DailyLog ---

class DailyLogBase(BaseModel):
    habit_id: int
    date: date
    is_completed: bool = False


class DailyLogCreate(DailyLogBase):
    pass


class DailyLogUpdate(BaseModel):
    is_completed: bool | None = None


class DailyLogResponse(DailyLogBase):
    id: int

    class Config:
        from_attributes = True


# --- Daily Metrics (water/steps) ---
class MetricResponse(BaseModel):
    date: date
    water_ml: int
    steps: int


class WaterAddRequest(BaseModel):
    amount_ml: int


class StepsSetRequest(BaseModel):
    steps: int


# --- Events ---
class EventCreate(BaseModel):
    date: date
    title: str
    color: str | None = None


class EventResponse(EventCreate):
    id: int

    class Config:
        from_attributes = True

