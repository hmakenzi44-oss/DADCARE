'use strict';

// ── MORE PAGE (hub for all other features) ──────────────────
Router.register('more', () => {
  const role = State.business?.role || 'staff';
  const isOwnerOrManager = ['owner','manager'].includes(role);

  const menuItems = [
    {icon:'&#128101;', label:'Wateja', sub:'Orodha na mikopo', page:'customers', show:true},
    {icon:'&#128666;', label:'Wasambazaji', sub:'Orodha ya wasambazaji', page:'suppliers', show:true},
    {icon:'&#128203;', label:'Maagizo ya Ununuzi', sub:'Nunua stoo kutoka wasambazaji', page:'purchase-orders', show:isOwnerOrManager},
    {icon:'&#128722;', label:'Maagizo ya Jumla', sub:'Mauzo ya jumla kwa wateja', page:'wholesale-orders', show:true},
    {icon:'&#128202;', label:'Ripoti', sub:'Mapato, faida, bidhaa bora', page:'reports', show:isOwnerOrManager},
    {icon:'&#128101;', label:'Wafanyakazi', sub:'Simamia timu yako', page:'staff', show:role==='owner'},
    {icon:'&#127978;', label:'Soko la DADCARE', sub:'Tanga bidhaa zako hadharani', page:'my-listings', show:true},
    {icon:'&#9881;', label:'Mipangilio', sub:'Biashara, sarafu, risiti', page:'settings', show:true},
    {icon:'&#8646;', label:'Badilisha Biashara', sub:'Nenda kwenye biashara nyingine', page:'businesses', show:true},
  ].filter(m => m.show);

  return `
  <div class="topbar">
    <div class="topbar-logo">D</div>
    <span class="topbar-title">Zaidi</span>
    <button class="topbar-action" onclick="doLogout()" title="Toka">&#9873;</button>
  </div>
  <div class="page">
    <div class="section">
      <!-- USER INFO -->
      <div style="background:var(--bg-card);border-radius:var(--radius);padding:16px;display:flex;align-items:center;gap:14px;margin-bottom:20px">
        <div style="width:52px;height:52px;border-radius:50%;background:var(--brand-glow);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:var(--brand)">
          ${(State.user?.full_name||'U').charAt(0).toUpperCase()}
        </div>
        <div style="flex:1;min-width:0">
          <div style="font-size:15px;font-weight:700;truncate">${State.user?.full_name||'Mtumiaji'}</div>
          <div style="font-size:12px;color:var(--text-muted)">${State.user?.email||''}</div>
          <div style="margin-top:4px">${statusBadge(role)}</div>
        </div>
      </div>

      <!-- BUSINESS INFO -->
      <div style="background:var(--brand-glow);border:1px solid var(--brand);border-radius:var(--radius);padding:14px;margin-bottom:20px;display:flex;align-items:center;gap:12px">
        <div style="font-size:24px">&#127978;</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:700;truncate">${State.business?.tenant_name||'Biashara'}</div>
          <div style="font-size:12px;color:var(--text-dim)">${statusBadge(State.business?.role||'')}</div>
        </div>
      </div>
    </div>

    <div class="card mx-16">
      ${menuItems.map(m => `
      <div class="list-item" onclick="Router.go('${m.page}')">
        <div class="list-item-icon brand" style="background:var(--brand-glow)">${m.icon}</div>
        <div class="list-item-body">
          <div class="list-item-title">${m.label}</div>
          <div class="list-item-sub">${m.sub}</div>
        </div>
        <span style="color:var(--text-muted)">&#8250;</span>
      </div>`).join('')}
    </div>

    <div style="padding:20px 16px;text-align:center">
      <button class="btn btn-ghost btn-sm" onclick="doLogout()">&#9873; Toka kwenye Akaunti</button>
    </div>
  </div>

  <div class="bottom-nav">
    <button class="nav-item" onclick="Router.go('dashboard')"><span class="nav-icon">&#127968;</span><span>Nyumbani</span></button>
    <button class="nav-item" onclick="Router.go('products')"><span class="nav-icon">&#128230;</span><span>Bidhaa</span></button>
    <button class="nav-item" onclick="Router.go('pos')">
      <div style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,var(--brand),#7B8FFF);display:flex;align-items:center;justify-content:center;margin-top:-20px;box-shadow:0 4px 16px rgba(91,110,245,0.4)">
        <span style="font-size:24px;color:#fff">+</span>
      </div>
      <span>Uza</span>
    </button>
    <button class="nav-item" onclick="Router.go('sales')"><span class="nav-icon">&#128176;</span><span>Mauzo</span></button>
    <button class="nav-item active" data-page="more"><span class="nav-icon">&#8942;</span><span>Zaidi</span></button>
  </div>`;
});

// ── CUSTOMERS ─────────────────────────────────────────────
Router.register('customers', async () => {
  let data = {customers: []};
  try { data = await API.getCustomers({}); } catch (e) {}

  const rows = data.customers?.length
    ? data.customers.map(c => `
    <div class="list-item" onclick="showCustomerDetail(${JSON.stringify(c).replace(/"/g,'&quot;')})">
      <div class="list-item-icon warning">&#128101;</div>
      <div class="list-item-body">
        <div class="list-item-title">${c.name}</div>
        <div class="list-item-sub">${c.phone||''} ${c.city?'• '+c.city:''}</div>
      </div>
      <div class="list-item-right">
        ${c.credit_limit > 0 ? `<div class="list-item-value ${c.balance>0?'text-danger':''}">${fmtCurrency(c.balance)}</div><div class="list-item-meta text-muted">Mkopo: ${fmtCurrency(c.credit_limit)}</div>` : ''}
      </div>
    </div>`)
    .join('')
    : '<div class="empty"><div class="empty-icon">&#128101;</div><div class="empty-text">Hakuna wateja bado</div></div>';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Wateja</span>
    <button class="topbar-action text-brand" onclick="showAddCustomer()">+</button>
  </div>
  <div class="page">
    <div class="search-wrap">
      <div class="search-bar">
        <input type="search" placeholder="Tafuta mteja..." oninput="searchCustomers(this.value)">
      </div>
    </div>
    <div class="card mx-16" id="customer-list">${rows}</div>
  </div>`;
});

async function searchCustomers(query) {
  try {
    const data = await API.getCustomers({search: query});
    const list = document.getElementById('customer-list');
    if (list) list.innerHTML = data.customers?.length
      ? data.customers.map(c => `
        <div class="list-item" onclick="showCustomerDetail(${JSON.stringify(c).replace(/"/g,'&quot;')})">
          <div class="list-item-icon warning">&#128101;</div>
          <div class="list-item-body"><div class="list-item-title">${c.name}</div><div class="list-item-sub">${c.phone||''}</div></div>
          <span style="color:var(--text-muted)">&#8250;</span>
        </div>`).join('')
      : '<div class="empty"><div class="empty-text">Hakuna matokeo</div></div>';
  } catch (e) {}
}

function showCustomerDetail(c) {
  Sheet.show(c.name, `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
      <div><div class="form-label">Simu</div><div class="bold">${c.phone||'—'}</div></div>
      <div><div class="form-label">Barua Pepe</div><div>${c.email||'—'}</div></div>
      <div><div class="form-label">Mji</div><div>${c.city||'—'}</div></div>
      <div><div class="form-label">Mkopo Kikomo</div><div class="bold">${fmtCurrency(c.credit_limit)}</div></div>
      <div><div class="form-label">Deni la Sasa</div><div class="bold ${c.balance>0?'text-danger':''}">${fmtCurrency(c.balance)}</div></div>
    </div>
    ${c.address ? `<div class="form-group"><div class="form-label">Anwani</div><div>${c.address}</div></div>` : ''}`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Funga</button>
      <button class="btn btn-primary flex-1" onclick="Sheet.hide();Router.go('pos')">+ Uza</button>
    </div>`
  );
}

function showAddCustomer() {
  Sheet.show('Mteja Mpya', `
    <div class="form-group"><label class="form-label">Jina *</label><input id="ac-name" type="text"></div>
    <div class="form-group"><label class="form-label">Simu</label><input id="ac-phone" type="tel" inputmode="tel"></div>
    <div class="form-group"><label class="form-label">Barua Pepe</label><input id="ac-email" type="email" inputmode="email"></div>
    <div class="form-group"><label class="form-label">Mji</label><input id="ac-city" type="text"></div>
    <div class="form-group"><label class="form-label">Anwani</label><textarea id="ac-address" rows="2"></textarea></div>
    <div class="form-group"><label class="form-label">Kikomo cha Mkopo</label><input id="ac-credit" type="number" inputmode="decimal" placeholder="0"></div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-save-customer">Hifadhi</button>
    </div>`
  );
  document.getElementById('btn-save-customer')?.addEventListener('click', async () => {
    const name = document.getElementById('ac-name')?.value.trim();
    if (!name) { Toast.error('Jina linahitajika'); return; }
    try {
      await API.createCustomer({
        name,
        phone: document.getElementById('ac-phone')?.value.trim(),
        email: document.getElementById('ac-email')?.value.trim(),
        city: document.getElementById('ac-city')?.value.trim(),
        address: document.getElementById('ac-address')?.value.trim(),
        credit_limit: parseFloat(document.getElementById('ac-credit')?.value) || 0,
      });
      Toast.success('Mteja ameongezwa!');
      Sheet.hide();
      Router.go('customers');
    } catch (e) { Toast.error(e.message); }
  });
}

// ── SUPPLIERS ─────────────────────────────────────────────
Router.register('suppliers', async () => {
  let data = {suppliers: []};
  try { data = await API.getSuppliers(); } catch (e) {}

  const rows = data.suppliers?.length
    ? data.suppliers.map(s => `
    <div class="list-item" onclick="showSupplierDetail(${JSON.stringify(s).replace(/"/g,'&quot;')})">
      <div class="list-item-icon danger">&#128666;</div>
      <div class="list-item-body">
        <div class="list-item-title">${s.name}</div>
        <div class="list-item-sub">${s.contact_person||''} ${s.phone?'• '+s.phone:''}</div>
      </div>
      <span style="color:var(--text-muted)">&#8250;</span>
    </div>`)
    .join('')
    : '<div class="empty"><div class="empty-icon">&#128666;</div><div class="empty-text">Hakuna wasambazaji bado</div></div>';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Wasambazaji</span>
    <button class="topbar-action text-brand" onclick="showAddSupplier()">+</button>
  </div>
  <div class="page">
    <div class="card mx-16 mt-16">${rows}</div>
  </div>`;
});

function showSupplierDetail(s) {
  Sheet.show(s.name, `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div><div class="form-label">Mawasiliano</div><div class="bold">${s.contact_person||'—'}</div></div>
      <div><div class="form-label">Simu</div><div>${s.phone||'—'}</div></div>
      <div><div class="form-label">Barua Pepe</div><div>${s.email||'—'}</div></div>
    </div>
    ${s.payment_terms ? `<div class="mt-12"><div class="form-label">Masharti ya Malipo</div><div>${s.payment_terms}</div></div>` : ''}
    ${s.address ? `<div class="mt-12"><div class="form-label">Anwani</div><div>${s.address}</div></div>` : ''}`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Funga</button>
      <button class="btn btn-primary flex-1" onclick="Sheet.hide();Router.go('purchase-orders')">+ Oda</button>
    </div>`
  );
}

function showAddSupplier() {
  Sheet.show('Msambazaji Mpya', `
    <div class="form-group"><label class="form-label">Jina la Kampuni *</label><input id="as-name" type="text"></div>
    <div class="form-group"><label class="form-label">Mtu wa Mawasiliano</label><input id="as-contact" type="text"></div>
    <div class="form-group"><label class="form-label">Simu</label><input id="as-phone" type="tel" inputmode="tel"></div>
    <div class="form-group"><label class="form-label">Barua Pepe</label><input id="as-email" type="email" inputmode="email"></div>
    <div class="form-group"><label class="form-label">Masharti ya Malipo</label><textarea id="as-terms" rows="2" placeholder="Mfano: Siku 30 baada ya kupokea"></textarea></div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-save-supplier">Hifadhi</button>
    </div>`
  );
  document.getElementById('btn-save-supplier')?.addEventListener('click', async () => {
    const name = document.getElementById('as-name')?.value.trim();
    if (!name) { Toast.error('Jina linahitajika'); return; }
    try {
      await API.createSupplier({
        name,
        contact_person: document.getElementById('as-contact')?.value.trim(),
        phone: document.getElementById('as-phone')?.value.trim(),
        email: document.getElementById('as-email')?.value.trim(),
        payment_terms: document.getElementById('as-terms')?.value.trim(),
      });
      Toast.success('Msambazaji ameongezwa!');
      Sheet.hide();
      Router.go('suppliers');
    } catch (e) { Toast.error(e.message); }
  });
}

// ── REPORTS ───────────────────────────────────────────────
Router.register('reports', async () => {
  let data = {};
  const today = new Date().toISOString().split('T')[0];
  const monthStart = today.slice(0, 8) + '01';
  try { data = await API.getSalesReport({from: monthStart, to: today}); } catch (e) {}
  const s = data.summary || {};
  const currency = State.currency || 'TZS';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Ripoti</span>
  </div>
  <div class="page">
    <div class="section">
      <div class="section-header">
        <span class="section-title">Mwezi Huu</span>
        <button class="btn btn-ghost btn-sm" onclick="showDateFilter()">Badilisha &#9660;</button>
      </div>
      <div class="stats-row" style="padding:0">
        <div class="stat-card">
          <div class="stat-value brand">${Math.round(s.total_sales)||0}</div>
          <div class="stat-label">Mauzo</div>
        </div>
        <div class="stat-card">
          <div class="stat-value accent" style="font-size:14px">${fmtCurrency(s.total_revenue||0, currency)}</div>
          <div class="stat-label">Mapato</div>
        </div>
        <div class="stat-card">
          <div class="stat-value success" style="font-size:14px">${fmtCurrency((s.total_revenue||0)-(s.total_discounts||0), currency)}</div>
          <div class="stat-label">Halisi</div>
        </div>
      </div>
    </div>

    <!-- BY PAYMENT METHOD -->
    ${data.by_payment_method?.length ? `
    <div class="section" style="padding-top:0">
      <div class="card">
        <div class="card-header"><span class="card-title">Njia za Malipo</span></div>
        ${data.by_payment_method.map(m => `
        <div class="list-item" style="padding:12px 16px">
          <div class="list-item-body">
            <div class="list-item-title">${m.payment_method}</div>
            <div class="list-item-sub">${m.count} muamala</div>
          </div>
          <div class="list-item-value text-accent">${fmtCurrency(m.total, currency)}</div>
        </div>`).join('')}
      </div>
    </div>` : ''}

    <!-- TOP PRODUCTS -->
    ${data.top_products?.length ? `
    <div class="section" style="padding-top:0">
      <div class="card">
        <div class="card-header"><span class="card-title">Bidhaa Bora 10</span></div>
        ${data.top_products.map((p,i) => `
        <div class="list-item" style="padding:12px 16px">
          <div style="width:28px;height:28px;border-radius:50%;background:var(--brand-glow);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:var(--brand);flex-shrink:0">${i+1}</div>
          <div class="list-item-body">
            <div class="list-item-title">${p.product_name}</div>
            <div class="list-item-sub">Vilivyouzwa: ${p.qty_sold}</div>
          </div>
          <div class="list-item-value text-accent">${fmtCurrency(p.revenue, currency)}</div>
        </div>`).join('')}
      </div>
    </div>` : ''}
  </div>`;
});

function showDateFilter() {
  Sheet.show('Chagua Kipindi', `
    <div class="flex gap-10 flex-wrap" style="margin-bottom:16px">
      ${[
        {label:'Leo', days:0},
        {label:'Wiki Hii', days:7},
        {label:'Mwezi Huu', days:30},
        {label:'Miezi 3', days:90},
      ].map(p => `<button class="btn btn-ghost btn-sm" onclick="setReportPeriod(${p.days})">${p.label}</button>`).join('')}
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">Kutoka</label><input id="rf-from" type="date"></div>
      <div class="form-group"><label class="form-label">Hadi</label><input id="rf-to" type="date"></div>
    </div>`,
    `<button class="btn btn-primary btn-block" onclick="applyReportFilter()">Tazama Ripoti</button>`
  );
}

async function setReportPeriod(days) {
  const to = new Date().toISOString().split('T')[0];
  const from = new Date(Date.now() - days * 86400000).toISOString().split('T')[0];
  document.getElementById('rf-from').value = from;
  document.getElementById('rf-to').value = to;
}

async function applyReportFilter() {
  const from = document.getElementById('rf-from')?.value;
  const to = document.getElementById('rf-to')?.value;
  Sheet.hide();
  try {
    const data = await API.getSalesReport({from, to});
    // Re-render would go here - simplified for now
    Toast.info('Ripoti imefanyiwa upya');
    Router.go('reports');
  } catch (e) { Toast.error(e.message); }
}
