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

## 4. Quality flags from CSV (для HW04)

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
