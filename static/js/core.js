/**
 * DADCARE Shop ERP — Core JS
 * API client, Toast, Sheet, Router, i18n, formatters
 */
'use strict';

// ── STATE ──────────────────────────────────────────────────
const State = {
  user: null,
  business: null,
  cart: [],
  lang: localStorage.getItem('dadcare_lang') || 'sw',
  currency: 'TZS',
};

// ── i18n ──────────────────────────────────────────────────
const T = {
  sw: {
    dashboard:'Dashibodi',products:'Bidhaa',sales:'Mauzo',customers:'Wateja',
    suppliers:'Wasambazaji',orders:'Maagizo',reports:'Ripoti',staff:'Wafanyakazi',
    settings:'Mipangilio',marketplace:'Soko',pos:'Uuzaji Mpya',
    search:'Tafuta...', save:'Hifadhi', cancel:'Ghairi', delete:'Futa',
    confirm:'Thibitisha', loading:'Inapakia...', error:'Hitilafu',
    success:'Imefanikiwa', no_results:'Hakuna matokeo',
    add_product:'Ongeza Bidhaa', new_sale:'Uuzaji Mpya',
    total:'Jumla', subtotal:'Jumla Ndogo', discount:'Punguzo',
    tax:'Kodi', payment:'Malipo', cash:'Pesa Taslimu',
    receipt:'Risiti', share:'Shiriki', print:'Chapisha',
    stock:'Stoo', low_stock:'Stoo Chini', out_of_stock:'Stoo Imekwisha',
    price:'Bei', cost:'Gharama', profit:'Faida',
    today:'Leo', this_week:'Wiki Hii', this_month:'Mwezi Huu',
    revenue:'Mapato', expenses:'Gharama', gross_profit:'Faida Ghafi',
    name:'Jina', phone:'Simu', email:'Barua Pepe', address:'Anwani',
    role:'Jukumu', permissions:'Ruhusa', invite:'Mwaliko',
    owner:'Mmiliki', manager:'Meneja', cashier:'Mhesabu',
    my_businesses:'Biashara Zangu', switch_business:'Badilisha Biashara',
    logout:'Toka', back:'Rudi',
    purchase_order:'Oda ya Ununuzi', wholesale_order:'Oda ya Jumla',
    receive:'Pokea', approve:'Thibitisha', reject:'Kataa', void:'Batilisha',
    reason:'Sababu', notes:'Maelezo',
  },
  en: {
    dashboard:'Dashboard',products:'Products',sales:'Sales',customers:'Customers',
    suppliers:'Suppliers',orders:'Orders',reports:'Reports',staff:'Staff',
    settings:'Settings',marketplace:'Marketplace',pos:'New Sale',
    search:'Search...', save:'Save', cancel:'Cancel', delete:'Delete',
    confirm:'Confirm', loading:'Loading...', error:'Error',
    success:'Success', no_results:'No results found',
    add_product:'Add Product', new_sale:'New Sale',
    total:'Total', subtotal:'Subtotal', discount:'Discount',
    tax:'Tax', payment:'Payment', cash:'Cash',
    receipt:'Receipt', share:'Share', print:'Print',
    stock:'Stock', low_stock:'Low Stock', out_of_stock:'Out of Stock',
    price:'Price', cost:'Cost', profit:'Profit',
    today:'Today', this_week:'This Week', this_month:'This Month',
    revenue:'Revenue', expenses:'Expenses', gross_profit:'Gross Profit',
    name:'Name', phone:'Phone', email:'Email', address:'Address',
    role:'Role', permissions:'Permissions', invite:'Invite',
    owner:'Owner', manager:'Manager', cashier:'Cashier',
    my_businesses:'My Businesses', switch_business:'Switch Business',
    logout:'Logout', back:'Back',
    purchase_order:'Purchase Order', wholesale_order:'Wholesale Order',
    receive:'Receive', approve:'Approve', reject:'Reject', void:'Void',
    reason:'Reason', notes:'Notes',
  }
};

function t(key) {
  return (T[State.lang] || T.sw)[key] || key;
}

// ── FORMATTERS ─────────────────────────────────────────────
function fmtCurrency(amount, currency) {
  const cur = currency || State.currency || 'TZS';
  const num = parseFloat(amount) || 0;
  return cur + ' ' + num.toLocaleString('sw-TZ', {minimumFractionDigits: 0, maximumFractionDigits: 2});
}

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('sw-TZ', {day:'numeric', month:'short', year:'numeric'});
}

function fmtDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('sw-TZ', {day:'numeric', month:'short', hour:'2-digit', minute:'2-digit'});
}

function fmtTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString('sw-TZ', {hour:'2-digit', minute:'2-digit'});
}

function statusBadge(status) {
  const map = {
    trial:'badge-warning', active:'badge-success', expired:'badge-danger',
    trial_expired:'badge-danger', suspended:'badge-muted',
    pending:'badge-warning', approved:'badge-success', rejected:'badge-danger',
    completed:'badge-success', voided:'badge-danger',
    draft:'badge-muted', confirmed:'badge-brand', paid:'badge-success',
    delivered:'badge-success', cancelled:'badge-danger',
    owner:'badge-brand', manager:'badge-brand', cashier:'badge-muted',
    staff:'badge-muted', viewer:'badge-muted',
  };
  const label = status?.replace(/_/g,' ') || status;
  return `<span class="badge ${map[status] || 'badge-muted'}">${label}</span>`;
}

// ── API CLIENT ─────────────────────────────────────────────
const API = {
  async req(method, path, body, extraHeaders = {}) {
    const opts = {
      method,
      headers: {'Content-Type': 'application/json', ...extraHeaders},
      credentials: 'same-origin',
    };
    if (body) opts.body = JSON.stringify(body);
    let res;
    try {
      res = await fetch('/api' + path, opts);
    } catch (e) {
      throw new Error('Hitilafu ya mtandao — angalia muunganisho wako');
    }
    let data = {};
    try { data = await res.json(); } catch (e) {}
    // FIX: 401 throws error instead of reloading page — prevents routing loop
    if (res.status === 401) {
      throw new Error('Authentication required');
    }
    if (!res.ok) throw new Error(data.error || `Hitilafu ${res.status}`);
    return data;
  },
  get(path)         { return this.req('GET', path); },
  post(path, body)  { return this.req('POST', path, body); },
  patch(path, body) { return this.req('PATCH', path, body); },
  del(path)         { return this.req('DELETE', path); },

  // Auth
  login(d)               { return this.post('/auth/login/', d); },
  register(d)            { return this.post('/auth/register/', d); },
  logout()               { return this.post('/auth/logout/'); },
  getProfile()           { return this.get('/auth/profile/'); },
  selectBusiness(tid)    { return this.post('/auth/select-business/', {tenant_id: tid}); },
  changePassword(d)      { return this.post('/auth/change-password/', d); },

  // Tenants
  getMiniApps()          { return this.get('/tenants/mini-apps/'); },
  createBusiness(d)      { return this.post('/tenants/create/', d); },
  getMyBusiness()        { return this.get('/tenants/me/'); },
  updateBusiness(d)      { return this.patch('/tenants/me/update/', d); },
  getMembers()           { return this.get('/tenants/members/'); },
  createInvite(d)        { return this.post('/tenants/invite/', d); },
  joinBusiness(code)     { return this.post('/tenants/join/', {code}); },
  removeMember(id)       { return this.del(`/tenants/members/${id}/remove/`); },
  updatePermissions(id,d){ return this.patch(`/tenants/members/${id}/permissions/`, d); },

  // Shop
  getDashboard()         { return this.get('/shop/dashboard/'); },
  getSettings()          { return this.get('/shop/settings/'); },
  saveSettings(d)        { return this.post('/shop/settings/update/', d); },

  // Products
  getProducts(p)         { return this.get('/shop/products/?' + new URLSearchParams(p||{})); },
  getProduct(id)         { return this.get(`/shop/products/${id}/`); },
  createProduct(d)       { return this.post('/shop/products/create/', d); },
  updateProduct(id,d)    { return this.patch(`/shop/products/${id}/update/`, d); },
  adjustStock(id,d)      { return this.post(`/shop/products/${id}/adjust-stock/`, d); },

  // Sales
  getSales(p)            { return this.get('/shop/sales/?' + new URLSearchParams(p||{})); },
  getSale(id)            { return this.get(`/shop/sales/${id}/`); },
  processSale(d)         { return this.post('/shop/sales/new/', d); },
  voidSale(id,d)         { return this.post(`/shop/sales/${id}/void/`, d); },

  // Customers
  getCustomers(p)        { return this.get('/shop/customers/?' + new URLSearchParams(p||{})); },
  createCustomer(d)      { return this.post('/shop/customers/create/', d); },
  updateCustomer(id,d)   { return this.patch(`/shop/customers/${id}/update/`, d); },

  // Suppliers
  getSuppliers()         { return this.get('/shop/suppliers/'); },
  createSupplier(d)      { return this.post('/shop/suppliers/create/', d); },

  // Purchase Orders
  getPurchaseOrders()    { return this.get('/shop/purchase-orders/'); },
  createPurchaseOrder(d) { return this.post('/shop/purchase-orders/create/', d); },
  receivePurchaseOrder(id,d){ return this.post(`/shop/purchase-orders/${id}/receive/`, d); },

  // Wholesale Orders
  getOrders(p)           { return this.get('/shop/orders/?' + new URLSearchParams(p||{})); },
  createOrder(d)         { return this.post('/shop/orders/create/', d); },
  updateOrderStatus(id,d){ return this.patch(`/shop/orders/${id}/status/`, d); },

  // Reports
  getSalesReport(p)      { return this.get('/shop/reports/sales/?' + new URLSearchParams(p||{})); },
  getStockMovements(p)   { return this.get('/shop/stock-movements/?' + new URLSearchParams(p||{})); },

  // Marketplace
  getMyListings()        { return this.get('/marketplace/listings/mine/'); },
  submitListing(d)       { return this.post('/marketplace/listings/submit/', d); },
  deleteListing(id)      { return this.del(`/marketplace/listings/${id}/delete/`); },
};

// ── TOAST ──────────────────────────────────────────────────
const Toast = {
  show(msg, type = 'info', ms = 3500) {
    let root = document.getElementById('toast-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'toast-root';
      document.body.appendChild(root);
    }
    const icons = {success:'✓', error:'✕', warning:'!', info:'i'};
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span style="font-weight:800;font-size:12px">${icons[type]||'i'}</span><span>${msg}</span>`;
    root.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      el.style.transition = 'all 0.2s';
      setTimeout(() => el.remove(), 220);
    }, ms);
  },
  success(m) { this.show(m, 'success'); },
  error(m)   { this.show(m, 'error', 5000); },
  warning(m) { this.show(m, 'warning'); },
  info(m)    { this.show(m, 'info'); },
};

// ── SHEET ─────────────────────────────────────────────────
const Sheet = {
  show(title, content, actions = '') {
    this.hide();
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    overlay.id = 'sheet-overlay';
    const sheet = document.createElement('div');
    sheet.className = 'sheet';
    sheet.id = 'active-sheet';
    sheet.innerHTML = `
      <div class="sheet-handle"></div>
      <div class="sheet-header">
        <span class="sheet-title">${title}</span>
        <button class="btn btn-ghost btn-sm" onclick="Sheet.hide()">&#x2715;</button>
      </div>
      <div class="sheet-body">${content}</div>
      ${actions ? `<div class="sheet-body border-top" style="padding-top:14px">${actions}</div>` : ''}`;
    document.body.appendChild(overlay);
    document.body.appendChild(sheet);
    requestAnimationFrame(() => {
      overlay.classList.add('show');
      sheet.classList.add('show');
    });
    overlay.onclick = (e) => { if (e.target === overlay) this.hide(); };
  },
  hide() {
    const o = document.getElementById('sheet-overlay');
    const s = document.getElementById('active-sheet');
    if (o) { o.classList.remove('show'); setTimeout(() => o.remove(), 280); }
    if (s) { s.classList.remove('show'); setTimeout(() => s.remove(), 280); }
  },
};

// ── CONFIRM DIALOG ─────────────────────────────────────────
function Confirm(message, title = 'Thibitisha') {
  return new Promise((resolve) => {
    Sheet.show(title, `<p style="font-size:14px;color:var(--text-dim)">${message}</p>`,
      `<div class="flex gap-10">
        <button class="btn btn-ghost flex-1" onclick="Sheet.hide();window._confirmRes(false)">Ghairi</button>
        <button class="btn btn-danger flex-1" onclick="Sheet.hide();window._confirmRes(true)">Thibitisha</button>
      </div>`);
    window._confirmRes = resolve;
  });
}

// ── ROUTER ─────────────────────────────────────────────────
const Router = {
  routes: {},
  current: null,

  register(name, fn) { this.routes[name] = fn; },

  async go(page, params = {}) {
    const main = document.getElementById('main-content');
    if (!main) return;
    main.innerHTML = '<div class="loading-page"><div class="spinner"></div></div>';
    this.current = page;

    // Update bottom nav active state
    document.querySelectorAll('.nav-item[data-page]').forEach(el => {
      el.classList.toggle('active', el.dataset.page === page);
    });

    const fn = this.routes[page];
    if (!fn) { main.innerHTML = '<div class="empty"><div class="empty-icon">404</div></div>'; return; }
    try {
      const html = await fn(params);
      main.innerHTML = html || '';
      window.scrollTo(0, 0);
      document.dispatchEvent(new CustomEvent('page:ready', {detail: {page, params}}));
    } catch (e) {
      Toast.error(e.message);
      main.innerHTML = `<div class="empty"><div class="empty-text">${e.message}</div></div>`;
    }
  },
};

// ── PAGINATION ─────────────────────────────────────────────
function renderPagination(total, page, perPage, onPage) {
  const pages = Math.ceil(total / perPage);
  if (pages <= 1) return '';
  let html = `<div class="flex items-center justify-between px-16 py-16" style="font-size:13px">
    <span class="text-muted">Ukurasa ${page} / ${pages} (${total} jumla)</span>
    <div class="flex gap-8">`;
  if (page > 1) html += `<button class="btn btn-ghost btn-sm" onclick="(${onPage})(${page-1})">&#8249; Nyuma</button>`;
  if (page < pages) html += `<button class="btn btn-primary btn-sm" onclick="(${onPage})(${page+1})">Mbele &#8250;</button>`;
  return html + '</div></div>';
}

// ── INIT ───────────────────────────────────────────────────
// Guard: run once only — prevents re-entry from Router.go loops
let _appInitDone = false;

document.addEventListener('DOMContentLoaded', async () => {
  if (_appInitDone) return;
  _appInitDone = true;

  // Step 1: Language check first — if no lang set, show language selection
  const savedLang = localStorage.getItem('dadcare_lang');
  if (!savedLang) {
    Router.go('language-select');
    return;
  }
  State.lang = savedLang;

  // Step 2: Profile check — run ONCE, 401 is expected when not logged in
  let authed = false;
  try {
    const data = await API.getProfile();
    State.user = data.user;
    State.business = data.active_business;
    // User language preference overrides localStorage
    if (data.user?.language) {
      State.lang = data.user.language;
      localStorage.setItem('dadcare_lang', data.user.language);
    }
    if (data.active_business) {
      State.currency = 'TZS'; // fetched from shop settings later
    }
    authed = true;
  } catch (e) {
    // 401 or network error — not logged in, clear state
    State.user = null;
    State.business = null;
    // Only show network error if it's not an auth error
    if (e.message !== 'Authentication required') {
      Toast.warning('Tatizo la mtandao — jaribu tena');
    }
  }

  // Step 3: Route ONCE — no further profile calls from here
  if (!authed) {
    Router.go('login');
    return;
  }

  if (!State.business) {
    Router.go('businesses');
    return;
  }

  const hash = window.location.hash.slice(1) || '';
  const validPages = ['dashboard','products','sales','customers','suppliers','orders','reports','staff','settings','marketplace','pos'];
  Router.go(validPages.includes(hash) ? hash : 'dashboard');
});
