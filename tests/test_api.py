"""API tests against a temporary database filled with synthetic data."""
import json

import pytest
from fastapi.testclient import TestClient

import storage
from main import app
from routers.portfolio import get_conn

ENDPOINTS = ["/positions", "/trades", "/nav", "/returns", "/risk", "/correlation"]


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    storage.connect(path).close()

    def override():
        conn = storage.connect(path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_conn] = override
    yield path
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    return TestClient(app)


def fill(path):
    """Three NAV days (100 -> 110 -> 99) and two holdings with five days of prices."""
    conn = storage.connect(path)
    for d, v in [("2026-01-01", 100.0), ("2026-01-02", 110.0), ("2026-01-03", 99.0)]:
        storage.save_nav(conn, {"date": d, "net_liquidation": v, "total_cash": None,
                                "gross_position_value": None, "unrealized_pnl": None,
                                "realized_pnl": None, "currency": "USD"})
    storage.save_positions(conn, [
        {"date": "2026-01-03", "con_id": 1, "symbol": "AAA", "quantity": 1.0, "avg_cost": 30.0,
         "market_price": 33.0, "market_value": 33.0, "currency": "USD"},
        {"date": "2026-01-03", "con_id": 2, "symbol": "BBB", "quantity": -1.0, "avg_cost": 20.0,
         "market_price": 19.8, "market_value": -19.8, "currency": "USD"},
    ])
    a = [10.0, 11.0, 10.5, 11.5, 12.0]
    b = [20.0, 19.0, 19.5, 18.0, 17.5]
    storage.save_prices(conn, [
        {"con_id": cid, "symbol": sym, "date": f"2026-01-0{i + 1}", "close": px}
        for cid, sym, series in [(1, "AAA", a), (2, "BBB", b)]
        for i, px in enumerate(series)
    ])
    conn.close()


def test_empty_database_does_not_crash(client):
    for path in ENDPOINTS:
        r = client.get(path)
        assert r.status_code == 200, path
    assert client.get("/returns").json()["twr_total"] is None
    assert client.get("/correlation").json() == {"symbols": [], "matrix": []}


def test_nav_pnl_and_returns(client, db):
    fill(db)
    rows = client.get("/nav").json()
    assert [r["date"] for r in rows] == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert [r["daily_pnl"] for r in rows] == [None, pytest.approx(10.0), pytest.approx(-11.0)]
    ret = client.get("/returns").json()
    assert ret["twr_total"] == pytest.approx(-0.01)
    assert ret["mwr"] == pytest.approx(-0.01)
    assert ret["days"] == 3


def test_positions_risk_and_correlation(client, db):
    fill(db)
    pos = {p["symbol"]: p for p in client.get("/positions").json()}
    assert pos["AAA"]["weight"] == pytest.approx(33.0 / 99.0)
    assert pos["BBB"]["weight"] == pytest.approx(-19.8 / 99.0)

    rk = client.get("/risk").json()
    assert rk["price_days"] == 4
    assert rk["ex_ante_daily"] > 0
    assert rk["realised_daily"] is None  # only 3 NAV days

    corr = client.get("/correlation").json()
    assert corr["symbols"] == ["AAA", "BBB"]
    m = corr["matrix"]
    assert m[0][0] == pytest.approx(1.0) and m[1][1] == pytest.approx(1.0)
    assert m[0][1] == pytest.approx(m[1][0])


def test_json_has_no_nan(client, db):
    fill(db)
    for path in ENDPOINTS:
        # strict parse: NaN or Infinity in the body would raise here
        json.loads(client.get(path).text, parse_constant=lambda c: pytest.fail(f"{path}: {c}"))


def test_cors_only_allows_local_frontend(client):
    ok = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.get("/", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in bad.headers
