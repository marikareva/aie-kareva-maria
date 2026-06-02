from fastapi.testclient import TestClient
from src.app.api import app, model
import pytest

client = TestClient(app)


# ========== Тесты health-check ==========

def test_health_returns_200():
    """Health-check должен возвращать 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_has_status_field():
    """Ответ health-check должен содержать поле status."""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data


def test_health_model_is_loaded():
    """Модель должна быть загружена."""
    response = client.get("/health")
    data = response.json()
    assert data["model_loaded"] == True


# ========== Тесты predict ==========

def test_predict_returns_200():
    """Успешное предсказание — 200 OK."""
    payload = {
        "dep_hour": 14,
        "day_of_week": 2,
        "month": 7,
        "is_weekend": 0,
        "distance": 2500.0,
        "airport_lag_delay": 10.0,
        "airport_load": 60.0,
        "airline_avg": 5.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200


def test_predict_returns_correct_fields():
    """Ответ должен содержать все нужные поля."""
    payload = {
        "dep_hour": 10,
        "day_of_week": 1,
        "month": 3,
        "is_weekend": 0,
        "distance": 1000.0,
        "airport_lag_delay": 5.0,
        "airport_load": 30.0,
        "airline_avg": 3.0,
    }
    response = client.post("/predict", json=payload)
    data = response.json()
    assert "predicted_delay_minutes" in data
    assert "is_delayed" in data
    assert "delay_category" in data
    assert "timestamp" in data


def test_predict_delay_is_number():
    """Задержка должна быть числом."""
    payload = {
        "dep_hour": 8,
        "day_of_week": 0,
        "month": 1,
        "is_weekend": 0,
        "distance": 500.0,
        "airport_lag_delay": 0.0,
        "airport_load": 20.0,
        "airline_avg": 2.0,
    }
    response = client.post("/predict", json=payload)
    data = response.json()
    assert isinstance(data["predicted_delay_minutes"], (int, float))


def test_predict_delay_category_is_string():
    """Категория задержки должна быть строкой."""
    payload = {
        "dep_hour": 20,
        "day_of_week": 5,
        "month": 12,
        "is_weekend": 1,
        "distance": 3000.0,
        "airport_lag_delay": 25.0,
        "airport_load": 80.0,
        "airline_avg": 10.0,
    }
    response = client.post("/predict", json=payload)
    data = response.json()
    assert isinstance(data["delay_category"], str)
    assert data["delay_category"] in [
        "Ранний вылет",
        "Без задержки",
        "Умеренная задержка",
        "Серьёзная задержка",
    ]


# ========== Тесты валидации ==========

def test_predict_invalid_hour_returns_422():
    """Час > 23 должен вернуть 422 Validation Error."""
    payload = {
        "dep_hour": 25,
        "day_of_week": 3,
        "month": 6,
        "is_weekend": 0,
        "distance": 1500.0,
        "airport_lag_delay": 0.0,
        "airport_load": 50.0,
        "airline_avg": 5.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_missing_field_returns_422():
    """Отсутствие обязательного поля — 422."""
    payload = {
        "day_of_week": 3,
        "month": 6,
        "is_weekend": 0,
        "distance": 1500.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_negative_distance_returns_422():
    """Отрицательное расстояние — 422."""
    payload = {
        "dep_hour": 10,
        "day_of_week": 3,
        "month": 6,
        "is_weekend": 0,
        "distance": -500.0,
        "airport_lag_delay": 0.0,
        "airport_load": 50.0,
        "airline_avg": 5.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422