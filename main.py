from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

MEMPOOL_BASE = "https://mempool.space/api"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("static/index.html")


def satoshi_to_btc(sats: int) -> float:
    return round(sats / 100_000_000, 8)


@app.get("/api/address/{addr}")
def get_address(addr: str):
    try:
        with httpx.Client(timeout=10.0) as http:
            addr_resp = http.get(f"{MEMPOOL_BASE}/address/{addr}")
            if addr_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Address not found")
            addr_resp.raise_for_status()
            addr_data = addr_resp.json()

            txs_resp = http.get(f"{MEMPOOL_BASE}/address/{addr}/txs")
            txs_resp.raise_for_status()
            txs_data = txs_resp.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Cannot reach mempool.space")
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream error")

    chain = addr_data["chain_stats"]
    received = chain["funded_txo_sum"]
    sent = chain["spent_txo_sum"]

    transactions = []
    for tx in txs_data[:25]:
        input_addrs = [
            vin["prevout"]["scriptpubkey_address"]
            for vin in tx.get("vin", [])
            if "prevout" in vin and "scriptpubkey_address" in vin["prevout"]
        ]
        is_incoming = addr not in input_addrs
        if is_incoming:
            amount = sum(
                vout["value"]
                for vout in tx.get("vout", [])
                if vout.get("scriptpubkey_address") == addr
            )
            counterparties = list(set(input_addrs))
            tx_type = "received"
        else:
            amount = sum(
                vout["value"]
                for vout in tx.get("vout", [])
                if vout.get("scriptpubkey_address") != addr
            )
            counterparties = list({
                vout["scriptpubkey_address"]
                for vout in tx.get("vout", [])
                if vout.get("scriptpubkey_address") and vout["scriptpubkey_address"] != addr
            })
            tx_type = "sent"

        transactions.append({
            "txid": tx["txid"],
            "date": tx.get("status", {}).get("block_time"),
            "amount_btc": satoshi_to_btc(amount),
            "type": tx_type,
            "counterparties": counterparties
        })

    return {
        "address": addr,
        "balance_btc": satoshi_to_btc(received - sent),
        "total_received_btc": satoshi_to_btc(received),
        "total_sent_btc": satoshi_to_btc(sent),
        "tx_count": chain["tx_count"],
        "transactions": transactions
    }


@app.get("/api/address/{addr}/graph")
def get_graph(addr: str):
    try:
        with httpx.Client(timeout=10.0) as http:
            txs_resp = http.get(f"{MEMPOOL_BASE}/address/{addr}/txs")
            txs_resp.raise_for_status()
            txs_data = txs_resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Cannot reach mempool.space")
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream error")

    def short_label(a: str) -> str:
        return a[:8] + "..." + a[-4:] if len(a) > 12 else a

    nodes: dict = {addr: {"id": addr, "role": "central", "label": short_label(addr)}}
    edges = []

    for tx in txs_data[:10]:
        input_addrs = [
            vin["prevout"]["scriptpubkey_address"]
            for vin in tx.get("vin", [])
            if "prevout" in vin and "scriptpubkey_address" in vin["prevout"]
        ]
        is_incoming = addr not in input_addrs

        if is_incoming:
            for sender in set(input_addrs):
                if sender not in nodes:
                    nodes[sender] = {"id": sender, "role": "sender", "label": short_label(sender)}
                amount = sum(
                    vout["value"]
                    for vout in tx.get("vout", [])
                    if vout.get("scriptpubkey_address") == addr
                )
                edges.append({
                    "source": sender,
                    "target": addr,
                    "amount_btc": satoshi_to_btc(amount),
                    "txid": tx["txid"]
                })
        else:
            for vout in tx.get("vout", []):
                receiver = vout.get("scriptpubkey_address")
                if receiver and receiver != addr:
                    if receiver not in nodes:
                        nodes[receiver] = {"id": receiver, "role": "receiver", "label": short_label(receiver)}
                    edges.append({
                        "source": addr,
                        "target": receiver,
                        "amount_btc": satoshi_to_btc(vout["value"]),
                        "txid": tx["txid"]
                    })

    return {"nodes": list(nodes.values()), "edges": edges}
