import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from catboost import CatBoostRegressor


def generate_sample_data(n=50000):
    """Генерирует синтетику."""
    np.random.seed(42)
    df = pd.DataFrame({
        'YEAR': 2025,
        'MONTH': np.random.choice(range(1, 13), n),
        'DAY': np.random.choice(range(1, 29), n),
        'DAY_OF_WEEK': np.random.choice(range(7), n),
        'AIRLINE': np.random.choice(['AA', 'UA', 'DL', 'SW', 'AS', 'B6', 'NK', 'F9'], n),
        'ORIGIN_AIRPORT': np.random.choice(
            ['ATL', 'LAX', 'ORD', 'DFW', 'DEN', 'JFK', 'SFO', 'SEA', 'MIA', 'BOS',
             'PHX', 'IAH', 'EWR', 'MCO', 'CLT', 'MSP', 'DTW', 'PHL', 'LGA', 'FLL'], n
        ),
        'DESTINATION_AIRPORT': np.random.choice(
            ['ATL', 'LAX', 'ORD', 'DFW', 'DEN', 'JFK', 'SFO', 'SEA', 'MIA', 'BOS',
             'PHX', 'IAH', 'EWR', 'MCO', 'CLT', 'MSP', 'DTW', 'PHL', 'LGA', 'FLL'], n
        ),
        'SCHEDULED_DEPARTURE': np.random.choice(range(0, 2400, 5), n),
        'DISTANCE': np.random.choice(range(150, 5000), n),
        'CANCELLED': 0,
    })

    df['DEP_HOUR'] = df['SCHEDULED_DEPARTURE'] // 100
    base_delay = 5
    hour_penalty = np.where((df['DEP_HOUR'] >= 16) & (df['DEP_HOUR'] <= 20), 12, 0)
    weekend_bonus = np.where(df['DAY_OF_WEEK'] >= 5, -3, 0)
    noise = np.random.exponential(12, n)

    df['DEPARTURE_DELAY'] = base_delay + hour_penalty + weekend_bonus + noise
    df['DEPARTURE_DELAY'] = df['DEPARTURE_DELAY'].clip(-30, 300).round(0)

    # Сохраняем в корень data/raw/
    save_path = Path('data/raw/flights.csv')
    save_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(save_path, index=False)
    print(f"Сгенерировано {n} записей → data/raw/flights.csv")
    return df


def load_and_preprocess():
    """Загружает данные (реальные или синтетику)."""
    data_path = Path('data/raw/flights.csv')
    
    if data_path.exists():
        print(f"Загрузка {data_path}...")
        df = pd.read_csv(data_path)
    else:
        print("Данные не найдены, генерирую синтетику...")
        df = generate_sample_data()

    if 'CANCELLED' in df.columns:
        df = df[df['CANCELLED'] == 0]

    df['DEP_HOUR'] = (df['SCHEDULED_DEPARTURE'] // 100).clip(0, 23)
    df['HOUR_SIN'] = np.sin(2 * np.pi * df['DEP_HOUR'] / 24)
    df['HOUR_COS'] = np.cos(2 * np.pi * df['DEP_HOUR'] / 24)

    if 'DAY_OF_WEEK' in df.columns:
        df['IS_WEEKEND'] = (df['DAY_OF_WEEK'] >= 5).astype(int)
    else:
        df['DAY_OF_WEEK'] = 3
        df['IS_WEEKEND'] = 0

    if 'MONTH' not in df.columns:
        df['MONTH'] = 6

    df['DEPARTURE_DELAY'] = df['DEPARTURE_DELAY'].fillna(0)

    print(f"Данные загружены: {df.shape[0]} строк")
    return df



def build_features(df):
    """Создаёт дополнительные признаки."""
    df = df.copy()
    df = df.sort_values(['ORIGIN_AIRPORT', 'DEP_HOUR'])

    df['AIRPORT_LAG_DELAY'] = (
        df.groupby('ORIGIN_AIRPORT')['DEPARTURE_DELAY']
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
    )

    if 'YEAR' in df.columns and 'DATE' not in df.columns:
        df['DATE'] = pd.to_datetime(df[['YEAR', 'MONTH', 'DAY']])

    if 'DATE' in df.columns:
        df['AIRPORT_LOAD'] = df.groupby(['ORIGIN_AIRPORT', 'DATE'])['DEPARTURE_DELAY'].transform('count')
    else:
        df['AIRPORT_LOAD'] = df.groupby('ORIGIN_AIRPORT')['DEPARTURE_DELAY'].transform('count')

    df['AIRLINE_AVG'] = df.groupby('AIRLINE')['DEPARTURE_DELAY'].transform('mean')

    return df



def quick_eda(df):
    """Графики."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    df['DEPARTURE_DELAY'].clip(-30, 150).hist(bins=80, ax=axes[0, 0], color='steelblue')
    axes[0, 0].set_title('Распределение задержек')

    hourly = df.groupby('DEP_HOUR')['DEPARTURE_DELAY'].mean()
    axes[0, 1].bar(hourly.index, hourly.values, color='coral')
    axes[0, 1].set_title('Задержки по часам')

    if 'DAY_OF_WEEK' in df.columns:
        dow = df.groupby('DAY_OF_WEEK')['DEPARTURE_DELAY'].mean()
        axes[1, 0].bar(['Пн','Вт','Ср','Чт','Пт','Сб','Вс'], dow.values, color='green')
        axes[1, 0].set_title('По дням недели')

    airline = df.groupby('AIRLINE')['DEPARTURE_DELAY'].mean().sort_values()
    axes[1, 1].barh(airline.index, airline.values, color='purple')
    axes[1, 1].set_title('По авиакомпаниям')

    plt.tight_layout()
    plt.savefig('notebooks/eda_plots.png', dpi=100)
    plt.show()
    print("Графики сохранены в notebooks/eda_plots.png")



def prepare_xy(df):
    """Готовит X и y."""
    feature_cols = [
        'HOUR_SIN', 'HOUR_COS',
        'DAY_OF_WEEK', 'IS_WEEKEND', 'MONTH',
        'DISTANCE',
        'AIRPORT_LAG_DELAY', 'AIRPORT_LOAD', 'AIRLINE_AVG',
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].copy()
    y = df['DEPARTURE_DELAY'].clip(-60, 180)

    mask = ~(X.isna().any(axis=1) | y.isna())
    X, y = X[mask], y[mask]

    print(f"Признаки: {available}")
    print(f"Записей: {len(X)}")
    return X, y, available



def train():
    """Обучение Baseline + CatBoost, сравнение, сохранение лучшей."""
    
    # Загрузка
    df = load_and_preprocess()

    # EDA
    quick_eda(df)

    # Фичи
    df = build_features(df)

    # X, y
    X, y, feature_names = prepare_xy(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    results = {}

    # ---- BASELINE: LinearRegression ----
    print("\n" + "=" * 50)
    print("BASELINE: LinearRegression")
    print("=" * 50)
    baseline = LinearRegression()
    baseline.fit(X_train, y_train)
    y_pred_base = baseline.predict(X_test)

    mae_base = mean_absolute_error(y_test, y_pred_base)
    r2_base = r2_score(y_test, y_pred_base)
    within_base = (np.abs(y_test - y_pred_base) <= 15).mean()

    results['Baseline'] = {
        'model': baseline,
        'MAE': mae_base,
        'R2': r2_base,
        'within_15min': within_base,
    }
    print(f"  MAE:              {mae_base:.1f} мин")
    print(f"  R²:               {r2_base:.3f}")
    print(f"  Точно (±15 мин):  {within_base:.1%}")

    # ---- CatBoost ----
    print("\n" + "=" * 50)
    print("CATBOOST")
    print("=" * 50)
    catboost = CatBoostRegressor(
        iterations=500,
        learning_rate=0.05,
        depth=6,
        random_seed=42,
        verbose=100,
        early_stopping_rounds=50,
    )
    catboost.fit(X_train, y_train, eval_set=(X_test, y_test), verbose=False)
    y_pred_cat = catboost.predict(X_test)

    mae_cat = mean_absolute_error(y_test, y_pred_cat)
    r2_cat = r2_score(y_test, y_pred_cat)
    within_cat = (np.abs(y_test - y_pred_cat) <= 15).mean()

    results['CatBoost'] = {
        'model': catboost,
        'MAE': mae_cat,
        'R2': r2_cat,
        'within_15min': within_cat,
    }
    print(f"  MAE:              {mae_cat:.1f} мин")
    print(f"  R²:               {r2_cat:.3f}")
    print(f"  Точно (±15 мин):  {within_cat:.1%}")

    # ---- СРАВНЕНИЕ ----
    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ МОДЕЛЕЙ")
    print("=" * 60)
    print(f"{'Модель':<20} {'MAE':<10} {'R²':<10} {'±15 мин':<10}")
    print("-" * 60)
    for name, res in results.items():
        print(f"{name:<20} {res['MAE']:<10.1f} {res['R2']:<10.3f} {res['within_15min']:<10.1%}")

    # Выбираем лучшую по MAE
    best_name = min(results, key=lambda k: results[k]['MAE'])
    best_model = results[best_name]['model']
    print(f"\nЛучшая модель: {best_name} (MAE = {results[best_name]['MAE']:.1f} мин)")

    # Сохраняем лучшую
    Path('../models').mkdir(exist_ok=True)
    joblib.dump(best_model, '../models/model.pkl')
    joblib.dump(feature_names, '../models/feature_names.pkl')
    joblib.dump({
        'Baseline_MAE': mae_base,
        'Baseline_R2': r2_base,
        'CatBoost_MAE': mae_cat,
        'CatBoost_R2': r2_cat,
        'best_model': best_name,
    }, '../models/metrics.pkl')

    print(f"\nСохранено: models/model.pkl ({best_name})")
    print(f"Сохранено: models/feature_names.pkl")
    print(f"Сохранено: models/metrics.pkl")

    return best_model, results


if __name__ == "__main__":
    train()