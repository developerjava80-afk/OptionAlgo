async function fetchStrategies() {
  const res = await fetch('/api/strategies');
  return res.json();
}

async function fetchSymbols(q) {
  const url = '/api/symbols?q=' + encodeURIComponent(q || '');
  const res = await fetch(url);
  return res.json();
}

function showResults(text) {
  document.getElementById('results').textContent = JSON.stringify(text, null, 2);
}

async function populateStrategies() {
  const strategies = await fetchStrategies();
  const sel = document.getElementById('strategy');
  sel.innerHTML = '';
  strategies.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id; opt.textContent = s.name;
    sel.appendChild(opt);
  });
}

let symbolList = [];

async function populateSymbols(q) {
  const data = await fetchSymbols(q);
  if (data && data.error) {
    showResults(data);
    return;
  }
  symbolList = data;
  const sel = document.getElementById('symbols');
  sel.innerHTML = '';
  data.forEach(s => {
    const opt = document.createElement('option');
    opt.value = JSON.stringify(s);
    opt.textContent = `${s.symbol} ${s.name || ''}`;
    sel.appendChild(opt);
  });
}

document.getElementById('search').addEventListener('input', (e) => {
  const q = e.target.value;
  populateSymbols(q);
});

document.getElementById('run').addEventListener('click', async () => {
  const sel = document.getElementById('symbols');
  const strategy = document.getElementById('strategy').value;
  if (!sel.selectedOptions.length) {
    alert('Select a symbol first');
    return;
  }
  const s = JSON.parse(sel.selectedOptions[0].value);
  showResults({status: 'running', symbol: s});
  const res = await fetch('/api/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ symbol: s.symbol, instrument_token: s.instrument_token, strategy })
  });
  const json = await res.json();
  showResults(json);
});

// initial load
populateStrategies();
populateSymbols('');
