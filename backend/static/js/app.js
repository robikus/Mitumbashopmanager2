/**
 * Mitumba Shop Manager — Frontend SPA
 *
 * All data is per-user and stored in PostgreSQL via Django REST API.
 *
 * API endpoints:
 *   GET/PUT  /api/settings/
 *   GET/POST /api/purchases/           DELETE /api/purchases/<id>/
 *   GET/POST /api/sales/               DELETE /api/sales/<id>/
 *   GET/POST /api/other-costs/         DELETE /api/other-costs/<id>/
 *   GET      /api/dashboard/
 *   GET      /api/finance/?year=&month=
 *   GET      /api/finance/stock/
 */

// ── Constants ────────────────────────────────────────────────────────────────

const CSRF   = window.MITUMBA.csrfToken;
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const MLONG  = ['January','February','March','April','May','June','July','August','September','October','November','December'];

const COST_LABELS = {
  rent:            '🏠 Rent',
  wages:           '👤 Wages',
  tax:             '🏛️ Tax',
  loan_repayment:  '🏦 Loan Repayment',
  extra_repayment: '🏦 Extra Repayment',
  other:           '📦 Other',
};

// ── Local cache ───────────────────────────────────────────────────────────────
let _settings   = null;
let _purchases  = [];
let _sales      = [];
let _costs      = [];
let _selMo      = new Date().getMonth();
let _selYr      = new Date().getFullYear();
let _sItemCount = 1;

// ── API helpers ───────────────────────────────────────────────────────────────

async function api(method, path, body = null) {
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken':  CSRF,
    },
    credentials: 'same-origin',
  };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(path, opts);
  if (resp.status === 401 || resp.status === 403) {
    window.location.href = '/auth/login/';
    return null;
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(JSON.stringify(err));
  }
  if (resp.status === 204) return null;
  return resp.json();
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function initApp() {
  try {
    [_settings, _purchases, _sales, _costs] = await Promise.all([
      api('GET', '/api/settings/'),
      api('GET', '/api/purchases/'),
      api('GET', '/api/sales/'),
      api('GET', '/api/other-costs/'),
    ]);
    if (_purchases && _purchases.results) _purchases = _purchases.results;
    if (_sales     && _sales.results)     _sales     = _sales.results;
    if (_costs     && _costs.results)     _costs     = _costs.results;

    loadSettingsUI();
    renderPurchases();
    renderSales();
    renderOtherCosts();
    await renderDashboard();
    renderFinanceMonthBar();
  } catch (e) {
    console.error('initApp failed:', e);
    toast('⚠️ Failed to load data', true);
  }
}

// ── NAV ───────────────────────────────────────────────────────────────────────

function nav(id, btn) {
  document.querySelectorAll('.pg').forEach(p => p.classList.remove('on'));
  document.querySelectorAll('.ntab').forEach(t => t.classList.remove('on'));
  document.getElementById('pg-' + id).classList.add('on');
  btn.classList.add('on');
  if (id === 'dashboard')   renderDashboard();
  if (id === 'finance')     renderFinance(_selYr, _selMo);
  if (id === 'stock')       renderStock();
  if (id === 'other-costs') renderOtherCosts();
}

// ── Modals ────────────────────────────────────────────────────────────────────

function showModal(id) {
  if (id === 'mPurchase') initPurchaseModal();
  if (id === 'mSale')     initSaleModal();
  if (id === 'mCost')     initCostModal();
  document.getElementById(id).style.display = 'flex';
}
function hideModal(id) { document.getElementById(id).style.display = 'none'; }
function bgClose(e, id) { if (e.target.id === id) hideModal(id); }

// ── Settings ──────────────────────────────────────────────────────────────────

function loadSettingsUI() {
  if (!_settings) return;
  const s = _settings;
  document.getElementById('sName').value    = s.shop_name || '';
  document.getElementById('sLoanTot').value = s.loan_total || '';
  document.getElementById('sUnsell').value  = s.unsellable_rate || 20;
  document.getElementById('sLowSt').value   = s.low_stock_threshold || 10;

  const cats = (s.categories || []).map(c => c.name);
  const g = document.getElementById('sCats');
  g.innerHTML = '';
  for (let i = 0; i < 10; i++) {
    g.innerHTML += `<div class="fg mb0"><label class="fl">Cat ${i+1}</label><input class="fi" id="sc${i}" value="${cats[i] || ''}"></div>`;
  }
}

async function saveSettings() {
  const cats = [];
  for (let i = 0; i < 10; i++) {
    const v = (document.getElementById('sc' + i)?.value || '').trim();
    if (v) cats.push({ name: v, sort_order: i });
  }
  const payload = {
    shop_name:           document.getElementById('sName').value || 'My Shop',
    loan_total:          +document.getElementById('sLoanTot').value || 0,
    unsellable_rate:     +document.getElementById('sUnsell').value  || 20,
    low_stock_threshold: +document.getElementById('sLowSt').value   || 10,
    categories:          cats,
  };
  try {
    _settings = await api('PUT', '/api/settings/', payload);
    toast('✅ Settings saved!');
  } catch (e) {
    toast('❌ Save failed: ' + e.message, true);
  }
}

// ── Purchases ─────────────────────────────────────────────────────────────────

function initPurchaseModal() {
  document.getElementById('pDate').value  = toDay();
  document.getElementById('pQty').value   = '';
  document.getElementById('pCost').value  = '';
  document.getElementById('pType').value  = 'Single';
  document.getElementById('pPrev').textContent = 'Fill in pieces and cost to see calculation preview.';
  const cats = (_settings?.categories || []).map(c => c.name);
  const sel  = document.getElementById('pCat');
  sel.innerHTML = cats.map(c => `<option value="${c}">${c}</option>`).join('');
}

function updPurchPrev() {
  const qty  = +document.getElementById('pQty').value;
  const cost = +document.getElementById('pCost').value;
  const typ  = document.getElementById('pType').value;
  const ur   = (_settings?.unsellable_rate || 20) / 100;
  if (!qty || !cost) {
    document.getElementById('pPrev').textContent = 'Fill in pieces and cost to see calculation preview.';
    return;
  }
  const unsellPcs = typ === 'Bale' ? Math.round(qty * ur) : 0;
  const sellable  = qty - unsellPcs;
  const cpp       = sellable > 0 ? (cost / sellable).toFixed(1) : '-';
  document.getElementById('pPrev').innerHTML =
    `<strong>Sellable pieces:</strong> ${sellable}` +
    (typ === 'Bale' ? `&nbsp;·&nbsp;<strong>Unsellable:</strong> ${unsellPcs}` : '') +
    `&nbsp;·&nbsp;<strong>Cost per piece:</strong> KES ${cpp}`;
}

async function savePurchase() {
  const payload = {
    date:          document.getElementById('pDate').value,
    category:      document.getElementById('pCat').value,
    purchase_type: document.getElementById('pType').value,
    total_pieces:  +document.getElementById('pQty').value,
    total_cost:    +document.getElementById('pCost').value,
  };
  if (!payload.date || !payload.category || !payload.total_pieces || !payload.total_cost) {
    toast('⚠️ Please fill all fields', true);
    return;
  }
  try {
    const p = await api('POST', '/api/purchases/', payload);
    _purchases.unshift(p);
    hideModal('mPurchase');
    renderPurchases();
    toast('✅ Purchase saved!');
  } catch (e) {
    toast('❌ ' + e.message, true);
  }
}

function renderPurchases() {
  const tb = document.getElementById('tPurchases');
  const em = document.getElementById('ePurchases');
  if (!_purchases.length) {
    tb.innerHTML = '';
    em.style.display = 'block';
    return;
  }
  em.style.display = 'none';
  const rows = [..._purchases].sort((a, b) => b.date.localeCompare(a.date));
  tb.innerHTML = rows.map(p => `<tr>
    <td>${fmtD(p.date)}</td>
    <td><span class="badge bg">${p.category}</span></td>
    <td><span class="badge ${p.purchase_type === 'Bale' ? 'bb' : 'bo'}">${p.purchase_type}</span></td>
    <td>${p.total_pieces}</td>
    <td>${p.sellable_pieces}</td>
    <td>${fmtN(p.total_cost)}</td>
    <td>${fmtN(p.cost_per_piece)}</td>
    <td><button class="btn bd bsm" onclick="delPurchase(${p.id})">✕</button></td>
  </tr>`).join('');
}

async function delPurchase(id) {
  try {
    await api('DELETE', `/api/purchases/${id}/`);
    _purchases = _purchases.filter(p => p.id !== id);
    renderPurchases();
    toast('🗑️ Deleted');
  } catch (e) {
    toast('❌ Delete failed', true);
  }
}

// ── Sales ─────────────────────────────────────────────────────────────────────

function initSaleModal() {
  document.getElementById('sDate').value  = toDay();
  document.getElementById('sType').value  = 'B2C';
  document.getElementById('sRev').value   = '';
  document.getElementById('sNotes').value = '';
  _sItemCount = 1;
  renderSaleItems();
}

function renderSaleItems() {
  const cats = (_settings?.categories || []).map(c => c.name);
  const opts = cats.map(c => `<option value="${c}">${c}</option>`).join('');
  let h = '';
  for (let i = 0; i < _sItemCount; i++) {
    h += `<div class="brow">
      <select class="fs" id="siC${i}">${opts}</select>
      <input class="fi" id="siQ${i}" type="number" placeholder="Qty" min="1">
      <button class="bdel" onclick="remSaleItem(${i})">✕</button>
    </div>`;
  }
  document.getElementById('sItems').innerHTML = h;
}

function addSaleItem() {
  if (_sItemCount >= 6) { toast('Max 6 categories per sale'); return; }
  _sItemCount++;
  renderSaleItems();
}

function remSaleItem(idx) {
  const vals = [];
  for (let j = 0; j < _sItemCount; j++) {
    if (j !== idx) vals.push({
      c: document.getElementById('siC' + j)?.value,
      q: document.getElementById('siQ' + j)?.value,
    });
  }
  _sItemCount = Math.max(1, vals.length);
  renderSaleItems();
  vals.forEach((v, j) => {
    const sel = document.getElementById('siC' + j);
    if (sel && v.c) sel.value = v.c;
    const inp = document.getElementById('siQ' + j);
    if (inp && v.q) inp.value = v.q;
  });
}

async function saveSale() {
  const items = [];
  for (let i = 0; i < _sItemCount; i++) {
    const cat = document.getElementById('siC' + i)?.value;
    const qty = +document.getElementById('siQ' + i)?.value;
    if (cat && qty > 0) items.push({ category: cat, quantity: qty });
  }
  const payload = {
    date:          document.getElementById('sDate').value,
    sale_type:     document.getElementById('sType').value,
    total_revenue: +document.getElementById('sRev').value,
    notes:         document.getElementById('sNotes').value,
    items,
  };
  if (!payload.date || !payload.total_revenue) { toast('⚠️ Please fill date and revenue', true); return; }
  if (!items.length)                            { toast('⚠️ Add at least one item', true);        return; }
  try {
    const s = await api('POST', '/api/sales/', payload);
    _sales.unshift(s);
    hideModal('mSale');
    renderSales();
    toast('✅ Sale saved!');
  } catch (e) {
    toast('❌ ' + e.message, true);
  }
}

function renderSales() {
  const lst = document.getElementById('salesList');
  const em  = document.getElementById('eSales');
  if (!_sales.length) { lst.innerHTML = ''; em.style.display = 'block'; return; }
  em.style.display = 'none';
  const rows = [..._sales].sort((a, b) => b.date.localeCompare(a.date));
  lst.innerHTML = rows.map(s => `<div style="background:var(--gr1);padding:12px;border-radius:8px;margin-bottom:8px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
      <div style="display:flex;gap:8px;align-items:center">
        <span style="font-weight:600">${fmtD(s.date)}</span>
        <span class="badge ${s.sale_type === 'B2C' ? 'bg' : 'bb'}">${s.sale_type}</span>
        <span style="font-weight:700;color:var(--g6)">KES ${fmtN(s.total_revenue)}</span>
      </div>
      <button class="btn bd bsm" onclick="delSale(${s.id})">✕</button>
    </div>
    <div class="saleDetail">📦 ${(s.items || []).map(i => `${i.quantity}× ${i.category}`).join(', ')}</div>
    ${s.notes ? `<div class="saleNote">👤 ${s.notes}</div>` : ''}
  </div>`).join('');
}

async function delSale(id) {
  try {
    await api('DELETE', `/api/sales/${id}/`);
    _sales = _sales.filter(s => s.id !== id);
    renderSales();
    toast('🗑️ Deleted');
  } catch (e) {
    toast('❌ Delete failed', true);
  }
}

// ── Other Costs ───────────────────────────────────────────────────────────────

function initCostModal() {
  document.getElementById('cDate').value   = toDay();
  document.getElementById('cCat').value    = 'rent';
  document.getElementById('cAmount').value = '';
  document.getElementById('cNotes').value  = '';
}

async function saveCost() {
  const payload = {
    date:     document.getElementById('cDate').value,
    category: document.getElementById('cCat').value,
    amount:   +document.getElementById('cAmount').value,
    notes:    document.getElementById('cNotes').value,
  };
  if (!payload.date || !payload.amount) {
    toast('⚠️ Please fill date and amount', true);
    return;
  }
  try {
    const c = await api('POST', '/api/other-costs/', payload);
    _costs.unshift(c);
    hideModal('mCost');
    renderOtherCosts();
    toast('✅ Entry saved!');
  } catch (e) {
    toast('❌ ' + e.message, true);
  }
}

async function delCost(id) {
  try {
    await api('DELETE', `/api/other-costs/${id}/`);
    _costs = _costs.filter(c => c.id !== id);
    renderOtherCosts();
    toast('🗑️ Deleted');
  } catch (e) {
    toast('❌ Delete failed', true);
  }
}

function renderOtherCosts() {
  const tb = document.getElementById('tCosts');
  const em = document.getElementById('eCosts');
  if (!_costs.length) {
    tb.innerHTML = '';
    em.style.display = 'block';
    return;
  }
  em.style.display = 'none';
  const rows = [..._costs].sort((a, b) => b.date.localeCompare(a.date));
  tb.innerHTML = rows.map(c => `<tr>
    <td>${fmtD(c.date)}</td>
    <td>${COST_LABELS[c.category] || c.category}</td>
    <td>${fmtN(c.amount)}</td>
    <td style="color:var(--gr5);font-size:.85rem">${c.notes || '—'}</td>
    <td><button class="btn bd bsm" onclick="delCost(${c.id})">✕</button></td>
  </tr>`).join('');
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

async function renderDashboard() {
  try {
    const d = await api('GET', '/api/dashboard/');
    if (!d) return;

    const net = d.net_profit;
    document.getElementById('dNet').textContent   = fmtKES(net);
    document.getElementById('dNet').style.color   = net >= 0 ? 'var(--gold)' : '#ff6b6b';
    document.getElementById('dMonth').textContent = d.month;
    document.getElementById('dRev').textContent   = fmtKES(d.revenue);
    document.getElementById('dCosts').textContent = fmtKES(d.total_costs);
    document.getElementById('dLoan').textContent  = fmtKES(d.loan_remaining);
    document.getElementById('dStock').textContent = d.total_in_stock + ' pcs';

    document.getElementById('dTop').textContent    = d.top_category || 'No sales yet';
    document.getElementById('dTopSub').textContent = d.top_category ? d.top_qty + ' pieces sold this month' : '';

    const alerts = d.low_stock_alerts || [];
    document.getElementById('dAlerts').innerHTML = alerts.length
      ? alerts.map(a => `<div class="srow"><div class="sname">${a.category}</div><span class="badge ${a.in_stock === 0 ? 'br' : 'bo'}">${a.in_stock === 0 ? 'OUT OF STOCK' : 'LOW: ' + a.in_stock + ' pcs'}</span></div>`).join('')
      : '<p style="font-size:.85rem;color:var(--gr4)">All categories well stocked ✅</p>';

    const recent = d.recent_sales || [];
    document.getElementById('dRecent').innerHTML = recent.length
      ? recent.map(s => `<div class="fline"><span class="flab">${fmtD(s.date)} · <span class="badge ${s.sale_type === 'B2C' ? 'bg' : 'bb'}">${s.sale_type}</span> ${(s.items || []).map(i => i.quantity + '× ' + i.category).join(', ')}</span><span class="fval tg">${fmtKES(s.total_revenue)}</span></div>`).join('')
      : '<p style="font-size:.85rem;color:var(--gr4)">No sales yet.</p>';
  } catch (e) {
    console.error('renderDashboard failed:', e);
  }
}

// ── Finance ───────────────────────────────────────────────────────────────────

function renderFinanceMonthBar() {
  const bar = document.getElementById('mBar');
  bar.innerHTML = MONTHS.map((m, i) =>
    `<button class="mchip${i === _selMo ? ' on' : ''}" onclick="selMonth(${i})">${m} ${_selYr}</button>`
  ).join('');
}

function selMonth(m) {
  _selMo = m;
  renderFinanceMonthBar();
  renderFinance(_selYr, _selMo);
}

function costLine(label, amount) {
  if (amount === 0) {
    return `<div class="fline"><span class="flab">${label}</span><span class="fval" style="color:var(--gr5)">KES 0</span></div>`;
  }
  return `<div class="fline fcost"><span class="flab">${label}</span><span class="fval">–${fmtKES(amount)}</span></div>`;
}

async function renderFinance(yr, mo) {
  try {
    const d = await api('GET', `/api/finance/?year=${yr}&month=${mo + 1}`);
    if (!d) return;
    const net = d.net_profit;
    document.getElementById('finBody').innerHTML = `
      <div class="pdraw" style="margin-bottom:16px">
        <div class="plabel">💰 Money for personal use — ${MLONG[mo]} ${yr}</div>
        <div class="pamount" style="color:${net >= 0 ? 'var(--gold)' : '#ff6b6b'}">${fmtKES(net)}</div>
        <div class="psub">${net >= 0 ? '✅ Profitable month!' : '⚠️ Costs exceed revenue this month'}</div>
      </div>
      <div class="card">
        <div class="ctitle">Revenue &amp; Stock Cost</div>
        <div class="fline"><span class="flab">💰 Total Sales Revenue</span><span class="fval tg">${fmtKES(d.revenue)}</span></div>
        <div class="fline fcost"><span class="flab">📦 Stock Purchased (Cost)</span><span class="fval">–${fmtKES(d.cogs)}</span></div>
        <div class="fline ftot"><span class="flab">GROSS PROFIT</span><span class="fval">${fmtKES(d.gross_profit)}</span></div>
      </div>
      <div class="card">
        <div class="ctitle">Other Monthly Costs</div>
        ${costLine('🏠 Rent',             d.costs.rent)}
        ${costLine('👤 Wages',            d.costs.wages)}
        ${costLine('🏛️ Tax',              d.costs.tax)}
        ${costLine('🏦 Loan Repayment',   d.costs.loan_repayment)}
        ${costLine('🏦 Extra Repayment',  d.costs.extra_repayment)}
        ${costLine('📦 Other',            d.costs.other)}
        <div class="fline ftot" style="background:#fff0f0"><span class="flab">TOTAL COSTS</span><span class="fval" style="color:var(--red)">–${fmtKES(d.costs.total)}</span></div>
      </div>
      <div class="card">
        <div class="ctitle">🏦 Loan Status</div>
        <div class="fline"><span class="flab">Original loan</span><span class="fval">${fmtKES(d.loan.total)}</span></div>
        <div class="fline"><span class="flab">Total repaid</span><span class="fval tg">${fmtKES(d.loan.total_repaid)}</span></div>
        <div class="lprog"><div class="lbar" style="width:${d.loan.percent_repaid}%"></div></div>
        <div class="fline ftot"><span class="flab">REMAINING BALANCE</span><span class="fval" style="color:var(--orange)">${fmtKES(d.loan.remaining)}</span></div>
      </div>`;
  } catch (e) {
    console.error('renderFinance failed:', e);
  }
}

// ── Stock ─────────────────────────────────────────────────────────────────────

async function renderStock() {
  try {
    const d = await api('GET', '/api/finance/stock/');
    if (!d) return;

    const cats = d.categories || [];
    const al   = _settings?.low_stock_threshold || 10;
    const mx   = Math.max(...cats.map(c => c.in_stock), 1);

    document.getElementById('stockList').innerHTML = cats.map(c => {
      const pct  = Math.round(c.in_stock / mx * 100);
      const cls  = c.in_stock === 0 ? 'out' : c.in_stock <= al ? 'low' : 'ok';
      const bcls = c.in_stock === 0 ? 'br'  : c.in_stock <= al ? 'bo'  : 'bg';
      const lbl  = c.in_stock === 0 ? 'OUT' : c.in_stock <= al ? 'LOW' : 'OK';
      return `<div class="srow">
        <div class="sname">${c.category}</div>
        <div class="sbwrap"><div class="sbar ${cls}" style="width:${pct}%"></div></div>
        <div class="sqty">${c.in_stock}</div>
        <span class="badge ${bcls}">${lbl}</span>
      </div>`;
    }).join('');

    document.getElementById('stockTot').textContent = d.total_pieces + ' pcs';
    document.getElementById('stockVal').textContent = fmtN(d.total_value);
  } catch (e) {
    console.error('renderStock failed:', e);
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function toDay() { return new Date().toISOString().split('T')[0]; }
function fmtD(d) {
  if (!d) return '';
  const [y, m, day] = d.split('-');
  return `${day}/${m}/${y}`;
}
function fmtN(n)   { return Math.round(+n).toLocaleString(); }
function fmtKES(n) { return 'KES ' + Math.round(+n).toLocaleString(); }

let _toastT = null;
function toast(msg, err) {
  const t = document.getElementById('toast');
  t.textContent      = msg;
  t.style.background = err ? 'var(--red)' : 'var(--g8)';
  t.classList.add('on');
  if (_toastT) clearTimeout(_toastT);
  _toastT = setTimeout(() => t.classList.remove('on'), 2800);
}

// ── Boot ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', initApp);
