'use strict';

Router.register('dashboard', async () => {
  let stats = {today:{}, low_stock_count:0, pending_orders:0};
  let shopName = State.business?.tenant_name || 'Biashara';
  let currency = State.currency || 'TZS';

  try {
    const [dash, settings] = await Promise.all([
      API.getDashboard(),
      API.getSettings().catch(() => ({}))
    ]);
    stats = dash;
    if (settings.shop_name) shopName = settings.shop_name;
    if (settings.currency) { currency = settings.currency; State.currency = currency; }
  } catch (e) {}

  const today = stats.today || {};
  const role = State.business?.role || 'staff';
  const canSeeProfit = ['owner','manager'].includes(role) || stats.today?.gross_profit !== undefined;

  // Low stock alert
  const lowStockAlert = stats.low_stock_count > 0
    ? `<div class="alert alert-warning mx-16 mb-0" style="margin:0 16px 16px">
        &#9888; Bidhaa ${stats.low_stock_count} zina stoo chini — 
        <button style="color:var(--warning);font-weight:700" onclick="Router.go('products',{filter:'low_stock'})">Angalia</button>
      </div>` : '';

  // Revenue chart (simple bar for last 7 days - placeholder data for now)
  const days = ['Ju','Al','Ij','Kh','Ij','Sa','Ap'];
  const chartBars = days.map((d,i) => {
    const h = i === 6 ? 70 : Math.floor(Math.random() * 60) + 10;
    return `<div class="chart-bar-col">
      <div class="chart-bar-fill" style="height:${h}%;background:${i===6?'var(--brand)':'var(--brand-glow)'}"></div>
      <div class="chart-bar-label">${d}</div>
    </div>`;
  }).join('');

  return `
  <div class="topbar">
    <div class="topbar-logo">D</div>
    <div style="flex:1;min-width:0">
      <div class="topbar-title truncate">${shopName}</div>
      <div style="font-size:10px;color:var(--text-muted);line-height:1">${statusBadge(State.business?.role||'')}</div>
    </div>
    <button class="topbar-action" onclick="Router.go('businesses')" title="Badilisha Biashara">&#8646;</button>
    <button class="topbar-action" onclick="Router.go('settings')">&#9881;</button>
  </div>

  <div class="page" style="padding-bottom:80px">
    ${lowStockAlert}

    <!-- TODAY STATS -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">Leo</span>
        <span style="font-size:12px;color:var(--text-muted)">${fmtDate(new Date().toISOString())}</span>
      </div>
      <div class="stats-row" style="padding:0;gap:10px">
        <div class="stat-card">
          <div class="stat-value brand">${today.sale_count || 0}</div>
          <div class="stat-label">Mauzo</div>
        </div>
        <div class="stat-card">
          <div class="stat-value accent" style="font-size:15px">${fmtCurrency(today.revenue || 0, currency)}</div>
          <div class="stat-label">Mapato</div>
        </div>
        ${canSeeProfit ? `
        <div class="stat-card">
          <div class="stat-value success" style="font-size:15px">${fmtCurrency(today.gross_profit || 0, currency)}</div>
          <div class="stat-label">Faida</div>
        </div>` : `
        <div class="stat-card">
          <div class="stat-value warning">${stats.low_stock_count || 0}</div>
          <div class="stat-label">Stoo Chini</div>
        </div>`}
      </div>
    </div>

    <!-- REVENUE CHART -->
    <div class="section" style="padding-top:0">
      <div class="card">
        <div class="card-header">
          <span class="card-title">Wiki Hii</span>
          <button class="btn btn-ghost btn-sm" onclick="Router.go('reports')">Ripoti &#8250;</button>
        </div>
        <div style="padding:16px 16px 8px">
          <div class="chart-bar">${chartBars}</div>
        </div>
      </div>
    </div>

    <!-- QUICK ACTIONS -->
    <div class="section" style="padding-top:0">
      <div class="section-header"><span class="section-title">Vitendo vya Haraka</span></div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
        ${quickAction('&#128176;','Uza','pos','brand')}
        ${quickAction('&#128230;','Bidhaa','products','success')}
        ${quickAction('&#128101;','Wateja','customers','warning')}
        ${quickAction('&#128666;','Wasambazaji','suppliers','danger')}
        ${quickAction('&#128202;','Ripoti','reports','brand')}
        ${quickAction('&#128101;','Wafanyakazi','staff','success')}
      </div>
    </div>

    <!-- PENDING ORDERS ALERT -->
    ${stats.pending_orders > 0 ? `
    <div class="section" style="padding-top:0">
      <div class="card" style="border-color:var(--warning)">
        <div class="list-item" onclick="Router.go('orders')">
          <div class="list-item-icon warning">&#128203;</div>
          <div class="list-item-body">
            <div class="list-item-title">Maagizo yanayosubiri</div>
            <div class="list-item-sub">${stats.pending_orders} maagizo yanahitaji hatua</div>
          </div>
          <span style="color:var(--warning)">&#8250;</span>
        </div>
      </div>
    </div>` : ''}
  </div>

  <div class="bottom-nav">
    <button class="nav-item active" data-page="dashboard" onclick="Router.go('dashboard')">
      <span class="nav-icon">&#127968;</span><span>Nyumbani</span>
    </button>
    <button class="nav-item" data-page="products" onclick="Router.go('products')">
      <span class="nav-icon">&#128230;</span><span>Bidhaa</span>
    </button>
    <button class="nav-item" data-page="pos" onclick="Router.go('pos')" style="position:relative">
      <div style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,var(--brand),#7B8FFF);display:flex;align-items:center;justify-content:center;margin-top:-20px;box-shadow:0 4px 16px rgba(91,110,245,0.4)">
        <span style="font-size:24px;color:#fff">+</span>
      </div>
      <span>Uza</span>
    </button>
    <button class="nav-item" data-page="sales" onclick="Router.go('sales')">
      <span class="nav-icon">&#128176;</span><span>Mauzo</span>
    </button>
    <button class="nav-item" data-page="more" onclick="Router.go('more')">
      <span class="nav-icon">&#8942;</span><span>Zaidi</span>
    </button>
  </div>`;
});

function quickAction(icon, label, page, color) {
  return `
  <button onclick="Router.go('${page}')" style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px 8px;display:flex;flex-direction:column;align-items:center;gap:8px;transition:all 0.16s;cursor:pointer" 
    onmousedown="this.style.transform='scale(0.95)'" onmouseup="this.style.transform=''" ontouchstart="this.style.transform='scale(0.95)'" ontouchend="this.style.transform=''">
    <div style="width:44px;height:44px;border-radius:12px;background:rgba(91,110,245,0.1);display:flex;align-items:center;justify-content:center;font-size:22px">${icon}</div>
    <span style="font-size:11px;font-weight:600;color:var(--text-dim)">${label}</span>
  </button>`;
}
