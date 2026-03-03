from datetime import date, timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db, init_db
from . import crud, schemas

app = FastAPI(
    title="Habit Tracker API",
    description="Habit takip uygulaması için REST API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Uygulama başlarken veritabanı tablolarını oluşturur."""
    init_db()


@app.get("/")
def root():
    """API'nin çalışıp çalışmadığını kontrol etmek için."""
    return {"message": "Habit Tracker API çalışıyor!", "status": "ok"}


@app.get("/health")
def health_check():
    """Sağlık kontrolü endpoint'i."""
    return {"status": "healthy"}


# --- Habit endpoints ---

@app.post("/habits", response_model=schemas.HabitResponse)
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(get_db)):
    """Yeni alışkanlık oluşturur."""
    return crud.create_habit(db, habit)


@app.get("/habits", response_model=list[schemas.HabitResponse])
def list_habits(db: Session = Depends(get_db)):
    """Tüm alışkanlıkları listeler."""
    return crud.get_habits(db)


@app.get("/habits/{habit_id}", response_model=schemas.HabitResponse)
def get_habit(habit_id: int, db: Session = Depends(get_db)):
    """ID ile tek alışkanlık getirir."""
    habit = crud.get_habit(db, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Alışkanlık bulunamadı")
    return habit


@app.delete("/habits/{habit_id}", status_code=204)
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    """Alışkanlığı ve ilişkili günlük kayıtlarını siler."""
    if not crud.delete_habit(db, habit_id):
        raise HTTPException(status_code=404, detail="Alışkanlık bulunamadı")
    return None


# --- DailyLog endpoints ---

@app.post("/daily-logs", response_model=schemas.DailyLogResponse)
def create_daily_log(log: schemas.DailyLogCreate, db: Session = Depends(get_db)):
    """Yeni günlük kayıt oluşturur."""
    habit = crud.get_habit(db, log.habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Alışkanlık bulunamadı")
    # Only today actions allowed
    today = date.today()
    if log.date != today:
        raise HTTPException(status_code=403, detail="Sadece bugün için kayıt girişi yapılabilir.")
    return crud.create_daily_log(db, log)


@app.get("/daily-logs", response_model=list[schemas.DailyLogResponse])
def list_daily_logs(
    habit_id: int | None = None,
    log_date: date | None = None,
    log_date_from: date | None = None,
    log_date_to: date | None = None,
    db: Session = Depends(get_db),
):
    """Günlük kayıtları listeler. habit_id, log_date veya log_date_from/to ile filtrelenebilir."""
    return crud.get_daily_logs(
        db,
        habit_id=habit_id,
        log_date=log_date,
        log_date_from=log_date_from,
        log_date_to=log_date_to,
    )


@app.get("/daily-logs/{log_id}", response_model=schemas.DailyLogResponse)
def get_daily_log(log_id: int, db: Session = Depends(get_db)):
    """ID ile tek günlük kayıt getirir."""
    log = crud.get_daily_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Günlük kayıt bulunamadı")
    return log


@app.patch("/daily-logs/{log_id}", response_model=schemas.DailyLogResponse)
def update_daily_log(
    log_id: int,
    payload: schemas.DailyLogUpdate,
    db: Session = Depends(get_db),
):
    """Günlük kaydın durumunu (is_completed) günceller."""
    if payload.is_completed is None:
        raise HTTPException(status_code=400, detail="is_completed gerekli")
    # Only today entries can be edited
    exist = crud.get_daily_log(db, log_id)
    if not exist:
        raise HTTPException(status_code=404, detail="Günlük kayıt bulunamadı")
    today = date.today()
    if exist.date != today:
        raise HTTPException(status_code=403, detail="Sadece bugünkü kayıtlarda değişiklik yapılır")
    log = crud.update_daily_log(db, log_id, payload.is_completed)
    if not log:
        raise HTTPException(status_code=404, detail="Günlük kayıt bulunamadı")
    return log


# --- Smart metrics endpoints ---
@app.get("/metrics/today", response_model=schemas.MetricResponse)
def get_today_metric(db: Session = Depends(get_db)):
    today = date.today()
    m = crud.get_or_create_metric(db, today)
    return schemas.MetricResponse(date=today, water_ml=m.water_ml, steps=m.steps)


@app.post("/metrics/water", response_model=schemas.MetricResponse)
def add_water(req: schemas.WaterAddRequest, db: Session = Depends(get_db)):
    if req.amount_ml <= 0:
        raise HTTPException(status_code=400, detail="amount_ml > 0 olmalı")
    return crud.add_water(db, req.amount_ml)


@app.post("/metrics/steps", response_model=schemas.MetricResponse)
def set_steps(req: schemas.StepsSetRequest, db: Session = Depends(get_db)):
    if req.steps < 0:
        raise HTTPException(status_code=400, detail="steps >= 0 olmalı")
    return crud.set_steps(db, req.steps)


# --- Events ---
@app.post("/events", response_model=schemas.EventResponse)
def create_event(evt: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, evt)


@app.get("/events", response_model=list[schemas.EventResponse])
def get_events(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_events(db, date_from=date_from, date_to=date_to)
