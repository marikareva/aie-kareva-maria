# S03 – eda_cli: мини-EDA для CSV

Небольшое CLI-приложение для базового анализа CSV-файлов.
Используется в рамках Семинара 03 курса «Инженерия ИИ».

## Требования

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) установлен в систему

## Инициализация проекта

В корне проекта (S03):

```bash
uv sync
```

Эта команда:

- создаст виртуальное окружение `.venv`;
- установит зависимости из `pyproject.toml`;
- установит сам проект `eda-cli` в окружение.

## Запуск CLI

### Краткий обзор

```bash
uv run eda-cli overview data/example.csv
```

Параметры:

- `--sep` – разделитель (по умолчанию `,`);
- `--encoding` – кодировка (по умолчанию `utf-8`).

### Полный EDA-отчёт

```bash
uv run eda-cli report data/example.csv --out-dir reports
```

В результате в каталоге `reports/` появятся:

- `report.md` – основной отчёт в Markdown;
- `summary.csv` – таблица по колонкам;
- `missing.csv` – пропуски по колонкам;
- `correlation.csv` – корреляционная матрица (если есть числовые признаки);
- `top_categories/*.csv` – top-k категорий по строковым признакам;
- `hist_*.png` – гистограммы числовых колонок;
- `missing_matrix.png` – визуализация пропусков;
- `correlation_heatmap.png` – тепловая карта корреляций.

## Тесты

```bash
uv run pytest -q
```
## Расширенные параметры команды `report`

Команда `report` поддерживает дополнительные параметры для настройки отчёта:

```bash
uv run eda-cli report data.csv --title "Мой анализ" --top-k-categories 15 --min-missing-share 0.2 --max-hist-columns 10 --out-dir my_report
```

## EDA CLI и HTTP сервис для анализа качества данных(HW04)

Этот проект включает два компонента:

Командный интерфейс (CLI) для анализа данных - был реализован в домашнем задании HW03

HTTP сервис на FastAPI для оценки качества датасетов - реализован в текущем задании HW04

## Требования для запуска

Python версии 3.11 или выше

Утилита uv для управления зависимостями

## Для HTTP сервиса (HW04)

- `fastapi>=0.125.0` – фреймворк для создания веб-API
- `uvicorn[standard]>=0.38.0` – ASGI-сервер для запуска FastAPI приложений
- `python-multipart>=0.0.21` – библиотека для обработки загрузки файлов

## Для тестирования

- `pytest>=9.0.1` – фреймворк для написания и запуска тестов

### 1. Установка зависимостей

Перейдите в папку проекта:

```bash
cd homeworks/HW04/eda-cli
```
### Установите зависимости(для HW04):
```
uv sync
```
## Проверка CLI (из HW03)

Краткий обзор датасета

```bash
uv run eda-cli overview data/example.csv
```
## Полный EDA-отчёт

```bash
uv run eda-cli report data/example.csv --out-dir reports
```

## Запуск HTTP-сервиса 

Для запуска HTTP сервиса используйте команду uvicorn:

```bash
uv run uvicorn eda_cli.api:app --reload --port 8000
```
Эта команда запускает FastAPI приложение из модуля eda_cli.api на порту 8000.

Разбор команды по пунктам:

- `uv run` – запускает команду в виртуальном окружении проекта

- `uvicorn` – ASGI-сервер для запуска FastAPI приложений

- `eda_cli.api:app` – указывает на приложение app в файле api.py пакета eda_cli

- `--reload` – автоматически перезапускает сервер при изменении кода

- `--port 8000` – сервер будет работать на порту 8000

После запуска сервер будет доступен по адресу: http://127.0.0.1:8000

## Доступные HTTP эндпоинты

1. Проверка работоспособности сервиса

Метод: GET
- URL: /health
Описание: Проверяет, что сервис запущен и работает корректно.

2. Оценка качества данных по параметрам

Метод: POST
- URL: /quality
Описание: Оценивает качество датасета на основе переданных параметров.

3. Полный анализ CSV файла

Метод: POST
- URL: /quality-from-csv
Описание: Загружает CSV файл и проводит полный анализ качества данных.

## Результаты должны быть 

Результат: `INFO:     127.0.0.1:14600 - "GET /docs HTTP/1.1" 200 OK`
Результат: `INFO:     127.0.0.1:13079 - "GET /health HTTP/1.1" 200 OK`
Результат: `INFO:     127.0.0.1:14600 - "GET /openapi.json HTTP/1.1" 200 OK`
Результат: `INFO:     127.0.0.1:4748 - "POST /quality-flags-from-csv HTTP/1.1" 200 OK `
Результат: `INFO:     127.0.0.1:3067 - "POST /quality-from-csv HTTP/1.1" 200 OK `

## Тестирование эндпоинтов в Swagger UI:

- Найдите нужный эндпоинт (например, `/quality-flags-from-csv`)
- Нажмите "Try it out"
- Загрузите файл или заполните параметры
- Нажмите "Execute"

Увидите реальный ответ от сервера

## Quality flags from CSV (для HW04)

`POST /quality-flags-from-csv`
Полный набор флагов качества, включая эвристики из HW03:

- `has_constant_columns` - обнаружение колонок с одним значением
- `has_high_cardinality_categoricals` - обнаружение категориальных колонок с >50 уникальных значений

Параметры:
- `file` (multipart/form-data): CSV файл для анализа

Ответ:

```json
{
  "flags": {
    "too_few_rows": bool,
    "too_many_columns": bool,
    "too_many_missing": bool,
    "has_constant_columns": bool,
    "has_high_cardinality_categoricals": bool
  }
}
```
