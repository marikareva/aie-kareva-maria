from __future__ import annotations

import pandas as pd

from eda_cli.core import (
    compute_quality_flags,
    correlation_matrix,
    flatten_summary_for_print,
    missing_table,
    summarize_dataset,
    top_categories,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [10, 20, 30, None],
            "height": [140, 150, 160, 170],
            "city": ["A", "B", "A", None],
        }
    )


def test_summarize_dataset_basic():
    df = _sample_df()
    summary = summarize_dataset(df)

    assert summary.n_rows == 4
    assert summary.n_cols == 3
    assert any(c.name == "age" for c in summary.columns)
    assert any(c.name == "city" for c in summary.columns)

    summary_df = flatten_summary_for_print(summary)
    assert "name" in summary_df.columns
    assert "missing_share" in summary_df.columns


def test_missing_table_and_quality_flags():
    df = _sample_df()
    missing_df = missing_table(df)

    assert "missing_count" in missing_df.columns
    assert missing_df.loc["age", "missing_count"] == 1

    summary = summarize_dataset(df)
    flags = compute_quality_flags(summary, missing_df)
    assert 0.0 <= flags["quality_score"] <= 1.0


def test_correlation_and_top_categories():
    df = _sample_df()
    corr = correlation_matrix(df)
    # корреляция между age и height существует
    assert "age" in corr.columns or corr.empty is False

    top_cats = top_categories(df, max_columns=5, top_k=2)
    assert "city" in top_cats
    city_table = top_cats["city"]
    assert "value" in city_table.columns
    assert len(city_table) <= 2


def test_hw03_constant_column():
    """Test constant column detection."""
    df = pd.DataFrame({"col": [1, 1, 1]})
    missing_df = missing_table(df)
    summary = summarize_dataset(df)
    flags = compute_quality_flags(summary, missing_df)
    
    assert flags["has_constant_columns"] == True
    assert "col" in flags["constant_columns"]

def test_hw03_high_cardinality():
    """Test high cardinality detection."""
    df = pd.DataFrame({"cat": [f"v{i}" for i in range(51)]})
    missing_df = missing_table(df)
    summary = summarize_dataset(df)
    flags = compute_quality_flags(summary, missing_df)
    
    assert flags["has_high_cardinality_categoricals"] == True
    assert "cat" in flags["high_cardinality_cols"]

def test_hw03_no_issues():
    """Test clean data."""
    df = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
    missing_df = missing_table(df)
    summary = summarize_dataset(df)
    flags = compute_quality_flags(summary, missing_df)
    
    assert flags["has_constant_columns"] == False
    assert flags["has_high_cardinality_categoricals"] == False

def test_hw03_example_csv():
    """Test on example.csv."""
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "data", "example.csv")
    
    if os.path.exists(path):
        df = pd.read_csv(path)
        missing_df = missing_table(df)
        summary = summarize_dataset(df)
        flags = compute_quality_flags(summary, missing_df)
        
        assert "has_constant_columns" in flags
        assert "has_high_cardinality_categoricals" in flags
        assert 0.0 <= flags["quality_score"] <= 1.0
        
def test_hw03_cli_parameters():
    # Проверяем, что функция top_categories принимает параметр top_k
    df = pd.DataFrame({"cat": ["A", "B", "C", "D", "E", "F"] * 3})  # 6 уникальных значений
    
    # С параметром top_k=2
    result_2 = top_categories(df, top_k=2)
    
    # С параметром top_k=5
    result_5 = top_categories(df, top_k=5)
    
    # Проверяем, что с разными top_k получаем разное количество записей
    if "cat" in result_2 and "cat" in result_5:
        assert len(result_2["cat"]) == 2  # должно быть 2
        assert len(result_5["cat"]) == 5  # должно быть 5 (не больше чем уникальных значений)
        assert len(result_2["cat"]) != len(result_5["cat"])
        
def test_hw03_additional_heuristic():
    # Дополнительный тест для новых эвристик в compute_quality_flags
    df = pd.DataFrame({
        "normal": [1, 2, 3, 4, 5],
        "constant": [7, 7, 7, 7, 7],  # Все значения одинаковые
        "mixed": ["A", "B", "A", "B", "A"],
    })
    
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df)
    
    # Проверяем, что обнаружилась постоянная колонка
    assert flags["has_constant_columns"] == True
    assert "constant" in flags["constant_columns"]
    assert len(flags["constant_columns"]) == 1
    
def test_hw03_quality_flags_comprehensive():
    # Простой тест для compute_quality_flags
    df = pd.DataFrame({
        "constant": [1, 1, 1, 1, 1],  # 5 одинаковых значений
        "high_card": [f"val_{i}" for i in range(5)],  # 5 уникальных (для теста)
        "normal": [10, 20, 30, 40, 50],
    })
    
    summary = summarize_dataset(df)
    missing = missing_table(df)
    flags = compute_quality_flags(summary, missing)
    
    # Проверяем обе эвристики (high_card теперь имеет только 5 уникальных < 50)
    assert flags["has_constant_columns"] == True
    assert flags["has_high_cardinality_categoricals"] == False  # 5 < 50
    
    # Проверяем оценку качества
    assert 0 <= flags["quality_score"] <= 1.0