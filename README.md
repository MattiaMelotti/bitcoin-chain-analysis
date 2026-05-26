# Bitcoin Chain Analysis

Strumento web didattico per esplorare la chain analysis di indirizzi Bitcoin.

Inserisci un indirizzo Bitcoin e ottieni istantaneamente:
- **Statistiche**: saldo, totale ricevuto/inviato, numero di transazioni
- **Tabella transazioni**: ultime 25 TX con data, importo e link diretto a mempool.space
- **Grafo interattivo**: connessioni tra indirizzi (mittenti in rosso, destinatari in verde, nodo centrale in arancione) — cliccabile per navigare tra indirizzi

![screenshot](https://raw.githubusercontent.com/MattiaMelotti/bitcoin-chain-analysis/master/docs/screenshot.png)

## Stack

- **Backend**: Python + FastAPI — proxy verso [Mempool.space API](https://mempool.space/api)
- **Frontend**: HTML/CSS/JS puro + [Cytoscape.js](https://cytoscape.org/) per il grafo
- **Test**: pytest + respx

Nessuna API key richiesta. Nessun database. Funziona tutto in locale.

## Avvio rapido

```bash
# Clona e installa
git clone https://github.com/MattiaMelotti/bitcoin-chain-analysis.git
cd bitcoin-chain-analysis
pip install -r requirements.txt

# Avvia
uvicorn main:app --reload

# Apri nel browser
http://localhost:8000
```

## Indirizzi di esempio

| Tipo | Indirizzo |
|------|-----------|
| Bech32 (SegWit) | `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh` |
| Legacy | `1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf Na` |
| P2SH | `3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy` |

## Struttura

```
bitcoin-chain-analysis/
├── main.py          ← FastAPI: 3 endpoint + serve frontend
├── requirements.txt
├── static/
│   ├── index.html   ← layout dark theme
│   └── app.js       ← validazione, fetch, Cytoscape
└── tests/
    └── test_main.py ← 5 test con respx mock
```

## API

| Endpoint | Descrizione |
|----------|-------------|
| `GET /` | Serve il frontend |
| `GET /api/address/{addr}` | Stats + ultime 25 transazioni |
| `GET /api/address/{addr}/graph` | Nodi e archi per il grafo (ultime 10 TX) |

## Test

```bash
pytest tests/ -v
```
