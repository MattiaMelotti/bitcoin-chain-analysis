from fastapi.testclient import TestClient
from main import app
import pytest
import respx
import httpx

client = TestClient(app)


def test_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


MOCK_ADDRESS = {
    "address": "bc1qtest",
    "chain_stats": {
        "funded_txo_sum": 120000000,
        "spent_txo_sum": 78000000,
        "tx_count": 47
    },
    "mempool_stats": {"funded_txo_sum": 0, "spent_txo_sum": 0, "tx_count": 0}
}

MOCK_TXS = [
    {
        "txid": "abc123def456",
        "status": {"confirmed": True, "block_time": 1716739200},
        "vin": [{"prevout": {"scriptpubkey_address": "1SenderAddr"}}],
        "vout": [
            {"scriptpubkey_address": "bc1qtest", "value": 10000000},
            {"scriptpubkey_address": "1ChangeAddr", "value": 5000000}
        ]
    }
]


@respx.mock
def test_address_stats_success():
    respx.get("https://mempool.space/api/address/bc1qtest").mock(
        return_value=httpx.Response(200, json=MOCK_ADDRESS)
    )
    respx.get("https://mempool.space/api/address/bc1qtest/txs").mock(
        return_value=httpx.Response(200, json=MOCK_TXS)
    )
    response = client.get("/api/address/bc1qtest")
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "bc1qtest"
    assert data["balance_btc"] == pytest.approx(0.42, rel=1e-3)
    assert data["total_received_btc"] == pytest.approx(1.20, rel=1e-3)
    assert data["total_sent_btc"] == pytest.approx(0.78, rel=1e-3)
    assert data["tx_count"] == 47
    assert len(data["transactions"]) == 1
    assert data["transactions"][0]["txid"] == "abc123def456"
    assert data["transactions"][0]["type"] == "received"
    assert data["transactions"][0]["amount_btc"] == pytest.approx(0.1, rel=1e-3)


@respx.mock
def test_address_stats_not_found():
    respx.get("https://mempool.space/api/address/bc1qnotfound").mock(
        return_value=httpx.Response(404)
    )
    response = client.get("/api/address/bc1qnotfound")
    assert response.status_code == 404


@respx.mock
def test_address_stats_mempool_unreachable():
    respx.get("https://mempool.space/api/address/bc1qtest2").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    response = client.get("/api/address/bc1qtest2")
    assert response.status_code == 502


@respx.mock
def test_graph_success():
    respx.get("https://mempool.space/api/address/bc1qtest/txs").mock(
        return_value=httpx.Response(200, json=MOCK_TXS)
    )
    response = client.get("/api/address/bc1qtest/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    central_nodes = [n for n in data["nodes"] if n["role"] == "central"]
    assert len(central_nodes) == 1
    assert central_nodes[0]["id"] == "bc1qtest"
    assert len(data["edges"]) >= 1
    assert data["edges"][0]["source"] == "1SenderAddr"
    assert data["edges"][0]["target"] == "bc1qtest"
