import math

import pandas as pd
import pytest

from logic import (
    STATUS_MISMATCH,
    STATUS_ONLY_ACT,
    STATUS_ONLY_REGISTRY,
    DataError,
    ExcelProcessor,
    match_columns,
    normalize_id,
    parse_amount,
)


@pytest.fixture
def processor():
    return ExcelProcessor()


@pytest.mark.parametrize(
    "value, expected",
    [
        (1234.56, 1234.56),
        (100, 100.0),
        ("1 234,56", 1234.56),
        ("1 234,56", 1234.56),
        ("1,234.56", 1234.56),
        ("1.234,56", 1234.56),
        ("1,234,567", 1234567.0),
        ("1.234.567", 1234567.0),
        ("(100,00)", -100.0),
        ("-5 ₽", -5.0),
        ("−250", -250.0),
        ("", 0.0),
        (None, 0.0),
        (float("nan"), 0.0),
        ("n/a", None),
        ("-", None),
    ],
)
def test_parse_amount(value, expected):
    assert parse_amount(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (12345, "12345"),
        (12345.0, "12345"),
        ("12345.0", "12345"),
        (" 12345 ", "12345"),
        ("00123", "00123"),
        ("A-17", "A-17"),
        (None, None),
        (float("nan"), None),
        ("  ", None),
    ],
)
def test_normalize_id(value, expected):
    assert normalize_id(value) == expected


def test_match_columns_prefers_exact_match():
    columns = ["Сумма НДС", "Сумма", "Сумма к оплате"]
    assert match_columns(columns, ["сумма"])[0] == "Сумма"


def test_match_columns_prefers_shorter_partial_match():
    columns = ["Итоговая сумма заказа с НДС", "Сумма заказа"]
    assert match_columns(columns, ["сумма"])[0] == "Сумма заказа"


def write_excel(path, df, title_rows=0):
    with pd.ExcelWriter(path) as writer:
        if title_rows:
            pd.DataFrame([["Реестр за май"]] + [[None]] * (title_rows - 1)).to_excel(
                writer, header=False, index=False
            )
        df.to_excel(writer, startrow=title_rows, index=False)
    return path


def test_load_file_detects_header_and_columns(tmp_path, processor):
    df = pd.DataFrame(
        {
            "ID заказа": [101, 102, "Итого"],
            "Сумма НДС": [1, 2, 3],
            "Сумма": ["1 234,56", "500,00", "1 734,56"],
        }
    )
    loaded = processor.load_file(write_excel(tmp_path / "reg.xlsx", df, title_rows=3))

    assert loaded.id_col == "ID заказа"
    assert loaded.amount_col == "Сумма"
    assert loaded.data.to_dict("records") == [
        {"ID": "101", "Amount": 1234.56},
        {"ID": "102", "Amount": 500.0},
    ]
    assert math.isclose(loaded.total, 1734.56)


def test_duplicate_ids_are_summed(processor):
    df = pd.DataFrame({"Order ID": ["1", "1", "2"], "Amount": [100, 50, 10]})
    data, _, _ = processor.prepare(df, "Order ID", "Amount")
    assert data.set_index("ID")["Amount"].to_dict() == {"1": 150.0, "2": 10.0}


def test_duplicate_ids_first_mode():
    processor = ExcelProcessor()
    processor.config["duplicate_ids"] = "first"
    df = pd.DataFrame({"Order ID": ["1", "1"], "Amount": [100, 50]})
    data, _, _ = processor.prepare(df, "Order ID", "Amount")
    assert data["Amount"].tolist() == [100.0]


def test_float_ids_match_int_ids(tmp_path, processor):
    # An empty ID cell makes pandas read the whole column as float
    reg = pd.DataFrame({"Order ID": [101, None, 102], "Amount": [10, 0, 20]})
    act = pd.DataFrame({"Order ID": ["101", "102"], "Amount": [10, 20]})
    r = processor.load_file(write_excel(tmp_path / "reg.xlsx", reg))
    a = processor.load_file(write_excel(tmp_path / "act.xlsx", act))
    assert processor.find_discrepancies(r.data, a.data).empty


def test_unparsed_amounts_are_counted(processor):
    df = pd.DataFrame({"Order ID": ["1", "2"], "Amount": ["abc", "5"]})
    data, rows, unparsed = processor.prepare(df, "Order ID", "Amount")
    assert (rows, unparsed) == (2, 1)
    assert data["Amount"].tolist() == [0.0, 5.0]


def test_find_discrepancies(processor):
    registry = pd.DataFrame(
        {"ID": ["1", "2", "3", "4"], "Amount": [100.0, 50.0, 7.0, 1.0]}
    )
    act = pd.DataFrame({"ID": ["1", "2", "5"], "Amount": [100.005, 40.0, 3.0]})

    diffs = processor.find_discrepancies(registry, act)

    # ID 1 differs by less than epsilon; the rest is sorted by |Diff|
    assert list(diffs.itertuples(index=False, name=None)) == [
        ("2", 50.0, 40.0, 10.0, STATUS_MISMATCH),
        ("3", 7.0, 0.0, 7.0, STATUS_ONLY_REGISTRY),
        ("5", 0.0, 3.0, -3.0, STATUS_ONLY_ACT),
        ("4", 1.0, 0.0, 1.0, STATUS_ONLY_REGISTRY),
    ]


def test_missing_amount_column_raises_data_error(tmp_path, processor):
    df = pd.DataFrame({"Order ID": [1], "Comment": ["x"]})
    with pytest.raises(DataError) as info:
        processor.load_file(write_excel(tmp_path / "bad.xlsx", df))
    assert info.value.key == "err_amount"
