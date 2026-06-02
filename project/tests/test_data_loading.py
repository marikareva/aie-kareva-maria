import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'src'))
from eda_and_train import load_and_preprocess, build_features, prepare_xy

def test_load_returns_dataframe():
    df = load_and_preprocess()
    assert df is not None
    assert len(df) > 0

def test_build_features_adds_columns():
    df = load_and_preprocess()
    df = build_features(df)
    assert 'AIRPORT_LAG_DELAY' in df.columns

def test_prepare_xy_shapes_match():
    df = load_and_preprocess()
    df = build_features(df)
    X, y, _ = prepare_xy(df)
    assert len(X) == len(y)