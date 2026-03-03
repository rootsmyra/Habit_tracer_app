from datetime import date
from sqlalchemy.orm import Session

from . import models, schemas


# --- Habit CRUD ---

def create_habit(db: Session, habit: schemas.HabitCreate) -> models.Habit:
    """Yeni alışkanlık oluşturur."""
    weekly_str = None
    if habit.weekly_days is not None:
        weekly_str = ",".join(str(d) for d in habit.weekly_days)
    # Neon renk ataması
    color = habit.color or _pick_neon_color()
    db_habit = models.Habit(
        name=habit.name,
        recurrence_type=habit.recurrence_type or "daily",
        weekly_days=weekly_str,
        monthly_day=habit.monthly_day,
        color=color,
    )
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit


def delete_habit(db: Session, habit_id: int) -> bool:
    """Alışkanlığı ve ilişkili daily_log kayıtlarını siler."""
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if not habit:
        return False
    db.delete(habit)
    db.commit()
    return True


def get_habit(db: Session, habit_id: int):
    """ID ile tek alışkanlık getirir."""
    return db.query(models.Habit).filter(models.Habit.id == habit_id).first()


def get_habits(db: Session):
    """Tüm alışkanlıkları listeler."""
    return db.query(models.Habit).all()


# --- DailyLog CRUD ---

def create_daily_log(db: Session, log: schemas.DailyLogCreate) -> models.DailyLog:
    """Yeni günlük kayıt oluşturur."""
    db_log = models.DailyLog(
        habit_id=log.habit_id,
        date=log.date,
        is_completed=log.is_completed,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


# --- Helpers ---
def _pick_neon_color() -> str:
    palette = [
        "#FF00FF",  # magenta
        "#00FFFF",  # cyan
        "#FF6B00",  # neon orange
        "#B0FF00",  # neon lime
        "#9D00FF",  # electric purple
        "#00FFA6",  # aqua green
        "#FFC400",  # neon yellow
    ]
    # basit bir seçim: tarih tabanlı deterministic index
    idx = date.today().toordinal() % len(palette)
    return palette[idx]


# --- Smart Metrics (water/steps) ---
def get_or_create_metric(db: Session, d: date) -> models.DailyMetric:
    metric = db.query(models.DailyMetric).filter(models.DailyMetric.date == d).first()
    if metric:
        return metric
    metric = models.DailyMetric(date=d, water_ml=0, steps=0)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def ensure_special_habit(db: Session, name: str, color: str | None = None) -> models.Habit:
    habit = db.query(models.Habit).filter(models.Habit.name == name).first()
    if habit:
        return habit
    habit = models.Habit(name=name, recurrence_type="daily", color=color or _pick_neon_color())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def upsert_daily_log(db: Session, habit_id: int, d: date, is_completed: bool) -> models.DailyLog:
    log = db.query(models.DailyLog).filter(models.DailyLog.habit_id == habit_id, models.DailyLog.date == d).first()
    if log:
        log.is_completed = is_completed
        db.commit()
        db.refresh(log)
        return log
    log = models.DailyLog(habit_id=habit_id, date=d, is_completed=is_completed)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def add_water(db: Session, amount_ml: int, target_ml: int = 2000) -> schemas.MetricResponse:
    today = date.today()
    metric = get_or_create_metric(db, today)
    metric.water_ml = max(0, metric.water_ml + amount_ml)
    db.commit()
    # auto complete "Daily Water"
    water_habit = ensure_special_habit(db, "Daily Water", "#00FFFF")
    done = metric.water_ml >= target_ml
    upsert_daily_log(db, water_habit.id, today, done)
    return schemas.MetricResponse(date=today, water_ml=metric.water_ml, steps=metric.steps)


def set_steps(db: Session, steps: int, target: int = 8000) -> schemas.MetricResponse:
    today = date.today()
    metric = get_or_create_metric(db, today)
    metric.steps = max(0, steps)
    db.commit()
    # auto complete "Daily Steps" (fallback to legacy '8000 Steps' if exists)
    step_habit = db.query(models.Habit).filter(models.Habit.name == "Daily Steps").first()
    if not step_habit:
        step_habit = db.query(models.Habit).filter(models.Habit.name == "8000 Steps").first()
    if not step_habit:
        step_habit = ensure_special_habit(db, "Daily Steps", "#B0FF00")
    done = metric.steps >= target
    upsert_daily_log(db, step_habit.id, today, done)
    return schemas.MetricResponse(date=today, water_ml=metric.water_ml, steps=metric.steps)


# --- Events ---
def create_event(db: Session, evt: schemas.EventCreate) -> models.Event:
    e = models.Event(date=evt.date, title=evt.title, color=evt.color)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def list_events(db: Session, date_from: date | None = None, date_to: date | None = None):
    q = db.query(models.Event)
    if date_from:
        q = q.filter(models.Event.date >= date_from)
    if date_to:
        q = q.filter(models.Event.date <= date_to)
    return q.all()


def get_daily_log(db: Session, log_id: int):
    """ID ile tek günlük kayıt getirir."""
    return db.query(models.DailyLog).filter(models.DailyLog.id == log_id).first()


def get_daily_logs(
    db: Session,
    habit_id: int | None = None,
    log_date: date | None = None,
    log_date_from: date | None = None,
    log_date_to: date | None = None,
):
    """Günlük kayıtları listeler. habit_id, log_date veya log_date_from/to ile filtrelenebilir."""
    query = db.query(models.DailyLog)
    if habit_id is not None:
        query = query.filter(models.DailyLog.habit_id == habit_id)
    if log_date is not None:
        query = query.filter(models.DailyLog.date == log_date)
    if log_date_from is not None:
        query = query.filter(models.DailyLog.date >= log_date_from)
    if log_date_to is not None:
        query = query.filter(models.DailyLog.date <= log_date_to)
    return query.all()


def update_daily_log(
    db: Session, log_id: int, is_completed: bool
) -> models.DailyLog | None:
    """Günlük kaydın is_completed alanını günceller."""
    db_log = get_daily_log(db, log_id)
    if not db_log:
        return None
    db_log.is_completed = is_completed
    db.commit()
    db.refresh(db_log)
    return db_log
