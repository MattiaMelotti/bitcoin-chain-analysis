let cy = null;
let currentAddr = null;

function isValidBitcoinAddress(addr) {
  if (!addr) return false;
  if (/^1[a-km-zA-HJ-NP-Z1-9]{24,33}$/.test(addr)) return true;
  if (/^3[a-km-zA-HJ-NP-Z1-9]{24,33}$/.test(addr)) return true;
  if (/^bc1[a-zA-HJ-NP-Z0-9]{39,59}$/.test(addr)) return true;
  return false;
}

function setError(msg) {
  document.getElementById('error-msg').textContent = msg;
}

function clearError() {
  document.getElementById('error-msg').textContent = '';
}

function showSpinner(on) {
  document.getElementById('spinner').style.display = on ? 'block' : 'none';
}

function showStats(on) {
  document.getElementById('stats-section').style.display = on ? 'block' : 'none';
}

async function search() {
  const addr = document.getElementById('addr-input').value.trim();
  clearError();
  showStats(false);

  if (!isValidBitcoinAddress(addr)) {
    setError('Formato indirizzo non valido. Supportati: Legacy (1...), P2SH (3...), Bech32 (bc1...)');
    return;
  }

  currentAddr = addr;
  showSpinner(true);

  try {
    const [statsRes, graphRes] = await Promise.all([
      fetch(`/api/address/${addr}`),
      fetch(`/api/address/${addr}/graph`)
    ]);

    showSpinner(false);

    if (statsRes.status === 404) {
      setError('Indirizzo non trovato o senza transazioni.');
      return;
    }
    if (statsRes.status === 502) {
      setError('Servizio temporaneamente non disponibile. Riprova.');
      return;
    }
    if (statsRes.status === 504) {
      setError('Timeout — riprova tra qualche secondo.');
      return;
    }
    if (!statsRes.ok) {
      setError('Errore imprevisto. Riprova.');
      return;
    }

    const stats = await statsRes.json();
    const graph = graphRes.ok ? await graphRes.json() : { nodes: [], edges: [] };

    renderStats(stats);
    renderTable(stats.transactions);
    renderGraph(graph, addr);
    showStats(true);
  } catch (e) {
    showSpinner(false);
    setError('Errore di rete. Verifica la connessione.');
  }
}

function renderStats(stats) {
  document.getElementById('stat-balance').textContent = stats.balance_btc.toFixed(8);
  document.getElementById('stat-received').textContent = stats.total_received_btc.toFixed(8);
  document.getElementById('stat-sent').textContent = stats.total_sent_btc.toFixed(8);
  document.getElementById('stat-txcount').textContent = stats.tx_count;
}

function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach((btn, i) => {
    btn.classList.toggle('active', (i === 0 && name === 'graph') || (i === 1 && name === 'table'));
  });
  document.getElementById('tab-graph').classList.toggle('active', name === 'graph');
  document.getElementById('tab-table').classList.toggle('active', name === 'table');
  if (name === 'graph' && cy) cy.resize();
}

document.getElementById('addr-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') search();
});

function renderTable(transactions) {
  const tbody = document.getElementById('tx-tbody');
  if (!transactions || transactions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Nessuna transazione trovata</td></tr>';
    return;
  }
  tbody.innerHTML = transactions.map(tx => {
    const date = tx.date
      ? new Date(tx.date * 1000).toLocaleDateString('it-IT')
      : 'Non confermata';
    const shortTxid = tx.txid.slice(0, 8) + '...' + tx.txid.slice(-4);
    const sign = tx.type === 'received' ? '+' : '-';
    return `<tr>
      <td>${date}</td>
      <td><a class="txid-link" href="https://mempool.space/tx/${tx.txid}" target="_blank" rel="noopener">${shortTxid}</a></td>
      <td class="amount ${tx.type}">${sign}${tx.amount_btc.toFixed(8)} BTC</td>
      <td><span class="badge ${tx.type}">${tx.type === 'received' ? 'Ricevuta' : 'Inviata'}</span></td>
    </tr>`;
  }).join('');
}

function renderGraph(graphData, centralAddr) {
  const nodeColors = { central: '#f7931a', sender: '#ef4444', receiver: '#22c55e' };
  const elements = [];

  graphData.nodes.forEach(n => {
    elements.push({
      data: { id: n.id, label: n.label, role: n.role, color: nodeColors[n.role] || '#8b949e' }
    });
  });

  graphData.edges.forEach((e, i) => {
    elements.push({
      data: {
        id: `e${i}`,
        source: e.source,
        target: e.target,
        label: e.amount_btc.toFixed(4) + ' BTC'
      }
    });
  });

  if (cy) cy.destroy();

  cy = cytoscape({
    container: document.getElementById('graph-container'),
    elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': 'data(color)',
          'label': 'data(label)',
          'color': '#e6edf3',
          'font-size': '10px',
          'text-valign': 'bottom',
          'text-halign': 'center',
          'text-margin-y': '4px',
          'width': '40px',
          'height': '40px',
          'border-width': '2px',
          'border-color': '#21262d'
        }
      },
      {
        selector: `node[id = "${centralAddr}"]`,
        style: { 'width': '55px', 'height': '55px', 'border-color': '#f7931a', 'border-width': '3px' }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#30363d',
          'target-arrow-color': '#30363d',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': '9px',
          'color': '#8b949e',
          'text-rotation': 'autorotate'
        }
      }
    ],
    layout: { name: 'cose', animate: false, padding: 40 },
    userZoomingEnabled: true,
    userPanningEnabled: true
  });

  cy.on('tap', 'node', evt => {
    const nodeId = evt.target.id();
    if (nodeId !== centralAddr) {
      document.getElementById('addr-input').value = nodeId;
      search();
    }
  });
}
