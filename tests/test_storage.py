"""Saving twice must never duplicate data (temporary database, synthetic rows)."""
import storage

TRADE = {
    "exec_id": "TEST.1", "time": "2026-01-02T15:30:00+00:00", "con_id": 1, "symbol": "AAA",
    "sec_type": "STK", "currency": "USD", "side": "BOT", "shares": 10.0, "price": 100.0,
    "commission": 1.0, "realized_pnl": None,
}


def nav_row(value: float) -> dict:
    return {"date": "2026-01-02", "net_liquidation": value, "total_cash": None,
            "gross_position_value": None, "unrealized_pnl": None, "realized_pnl": None,
            "currency": "USD"}


def test_same_trade_saved_once(tmp_path):
    conn = storage.connect(tmp_path / "sub" / "test.db")  # also creates the folder
    assert storage.save_executions(conn, [TRADE]) == 1
    assert storage.save_executions(conn, [TRADE]) == 0
    assert len(storage.load_executions(conn)) == 1


def test_nav_last_sync_of_day_wins(tmp_path):
    conn = storage.connect(tmp_path / "test.db")
    storage.save_nav(conn, nav_row(1000.0))
    storage.save_nav(conn, nav_row(1010.0))
    assert storage.load_nav(conn).tolist() == [1010.0]


def test_positions_ignore_extra_keys(tmp_path):
    # sync.py passes a sec_type key that is not a column; it must be ignored.
    conn = storage.connect(tmp_path / "test.db")
    storage.save_positions(conn, [{
        "date": "2026-01-02", "con_id": 1, "symbol": "AAA", "quantity": 10.0, "avg_cost": 100.0,
        "market_price": 101.0, "market_value": 1010.0, "currency": "USD", "sec_type": "STK",
    }])
    assert storage.load_positions(conn)["symbol"].tolist() == ["AAA"]


def test_prices_pivot_by_symbol(tmp_path):
    conn = storage.connect(tmp_path / "test.db")
    storage.save_prices(conn, [
        {"con_id": 1, "symbol": "AAA", "date": "2026-01-01", "close": 10.0},
        {"con_id": 1, "symbol": "AAA", "date": "2026-01-02", "close": 11.0},
        {"con_id": 2, "symbol": "BBB", "date": "2026-01-01", "close": 20.0},
    ])
    prices = storage.load_prices(conn, [1, 2])
    assert list(prices.columns) == ["AAA", "BBB"]
    assert prices["AAA"].tolist() == [10.0, 11.0]
