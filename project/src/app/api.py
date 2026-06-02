import joblib
import numpy as np
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import time

# ---------- ЛОГИРОВАНИЕ ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------- МОДЕЛИ ДАННЫХ ----------
class FlightRequest(BaseModel):
    dep_hour: int = Field(..., ge=0, le=23, example=17)
    day_of_week: int = Field(..., ge=0, le=6, example=3)
    month: int = Field(..., ge=1, le=12, example=6)
    is_weekend: int = Field(..., ge=0, le=1, example=0)
    distance: float = Field(..., gt=0, example=1500.0)
    airport_lag_delay: float = Field(default=0.0, example=12.5)
    airport_load: float = Field(default=50.0, example=45.0)
    airline_avg: float = Field(default=5.0, example=8.2)

class FlightResponse(BaseModel):
    predicted_delay_minutes: float
    is_delayed: bool
    delay_category: str
    timestamp: str

# ---------- ЗАГРУЗКА МОДЕЛИ ----------
MODEL_PATH = Path(__file__).parent.parent.parent / 'models' / 'model.pkl'
FEATURES_PATH = Path(__file__).parent.parent.parent / 'models' / 'feature_names.pkl'

model = None
feature_names = None

if MODEL_PATH.exists():
    model = joblib.load(MODEL_PATH)
    feature_names = joblib.load(FEATURES_PATH)
    logger.info(f"Модель загружена: {type(model).__name__}")
    logger.info(f"Признаки: {feature_names}")
else:
    logger.warning("Модель не найдена!")

# ---------- FASTAPI ----------
app = FastAPI(title="Flight Delay Predictor", version="1.0")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware: логирует все запросы и время ответа."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}с)")
    return response

@app.get("/health")
def health():
    """Проверка здоровья сервиса."""
    status = "healthy" if model is not None else "no_model"
    logger.info(f"Health check: {status}")
    return {
        "status": status,
        "model_loaded": model is not None,
        "model_type": type(model).__name__ if model else None,
    }

@app.post("/predict", response_model=FlightResponse)
def predict(req: FlightRequest):
    """Предсказание задержки рейса."""
    if model is None:
        logger.error("Запрос отклонён: модель не загружена")
        raise HTTPException(503, "Модель не загружена")

    logger.info(
        f"Predict: hour={req.dep_hour}, day={req.day_of_week}, "
        f"month={req.month}, weekend={req.is_weekend}, dist={req.distance}"
    )

    # Циклическое кодирование
    hour_sin = np.sin(2 * np.pi * req.dep_hour / 24)
    hour_cos = np.cos(2 * np.pi * req.dep_hour / 24)

    features = np.array([[
        hour_sin, hour_cos,
        req.day_of_week, req.is_weekend, req.month,
        req.distance,
        req.airport_lag_delay, req.airport_load, req.airline_avg,
    ]])

    pred = model.predict(features)[0]

    # Категория
    if pred < 0:
        cat = "Ранний вылет"
    elif pred <= 15:
        cat = "Без задержки"
    elif pred <= 60:
        cat = "Умеренная задержка"
    else:
        cat = "Серьёзная задержка"

    logger.info(f"Результат: {pred:.1f} мин → {cat}")

    return FlightResponse(
        predicted_delay_minutes=round(float(pred), 1),
        is_delayed=pred > 15,
        delay_category=cat,
        timestamp=datetime.now().isoformat(),
    )