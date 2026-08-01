/**
 * DADCARE — Page renderers
 * Each function returns HTML string injected by Router.
 * Event binding happens in 'page:rendered' listener at bottom.
 */

'use strict';

// ── LANGUAGE SELECT ──────────────────────────────────────
Router.register('lang-select', () => {
  return `
  <div class="lang-screen">
    <div class="text-center">
      <div class="lang-logo">DADCARE</div>
      <p class="lang-subtitle mt-8">Business Ecosystem for Africa<br>Mfumo wa Biashara wa Afrika</p>
    </div>
    <div class="lang-options">
      <button class="lang-btn" data-lang="sw" data-ripple>
        <span class="lang-flag">&#127472;&#127466;</span>
        <span>Kiswahili</span>
      </button>
      <button class="lang-btn" data-lang="en" data-ripple>
        <span class="lang-flag">&#127468;&#127463;</span>
        <span>English</span>
      </button>
    </div>
    <p class="caption text-center text-muted">Unaweza kubadilisha lugha wakati wowote</p>
  </div>`;
});

// ── WELCOME ──────────────────────────────────────────────
Router.register('welcome', () => {
  const t = App.t.bind(App);
  return `
  <div class="welcome-screen">
    <div class="welcome-hero">
      <div class="lang-logo" style="font-size:42px">DADCARE</div>
      <p class="welcome-tagline">${t('tagline')}</p>
    </div>
    <div class="welcome-paths">
      <button class="welcome-path primary" id="btn-browse" data-ripple>
        <span class="welcome-path-icon">&#128717;</span>
        <div class="welcome-path-text">
          <div class="welcome-path-title">${t('browse')}</div>
          <div class="welcome-path-sub">${t('browse_sub')}</div>
        </div>
        <span style="font-size:18px;opacity:0.7">&#8250;</span>
      </button>
      <button class="welcome-path secondary" id="btn-business" data-ripple>
        <span class="welcome-path-icon">&#127978;</span>
        <div class="welcome-path-text">
          <div class="welcome-path-title">${t('i_have_business')}</div>
          <div class="welcome-path-sub" style="color:var(--text-muted)">${t('business_sub')}</div>
        </div>
        <span style="font-size:18px;color:var(--text-muted)">&#8250;</span>
      </button>
    </div>
    <button class="btn btn-ghost btn-sm" id="btn-change-lang" style="margin-top:8px">
      &#127760; ${t('select_language')}
    </button>
  </div>`;
});

// ── MARKETPLACE BROWSE ───────────────────────────────────
Router.register('marketplace', async (params = {}) => {
  const t = App.t.bind(App);
  let listings = [];
  let categories = [];
  try {
    const [mkt, cats] = await Promise.all([
      API.getMarketplace(params),
      API.getCategories()
    ]);
    listings = mkt.listings || [];
    categories = cats.categories || [];
  } catch (e) { /* show empty state */ }

  const catPills = categories.slice(0, 10).map(c =>
    `<button class="pill" data-cat="${c.category}">${c.category} (${c.count})</button>`
  ).join('');

  const cards = listings.length ? listings.map(l => `
    <div class="product-card" data-id="${l.id}" data-ripple style="cursor:pointer">
      <div class="product-card-img">
        ${l.images && l.images[0]
          ? `<img src="${l.images[0]}" alt="${l.title}" loading="lazy">`
          : `<div class="no-img" style="font-size:36px">&#128722;</div>`}
      </div>
      <div class="product-card-body">
        <div class="product-card-name">${l.title}</div>
        <div class="product-card-price">${l.price ? App.formatCurrency(l.price, l.currency) : t('price') + ': ?'}</div>
        <div class="product-card-seller">${l.seller.name} &bull; ${l.city || ''}</div>
      </div>
    </div>`).join('')
  : `<div class="empty" style="grid-column:1/-1">
      <div class="empty-icon">&#128722;</div>
      <p class="body">${t('no_results')}</p>
    </div>`;

  return `
  <div class="app-shell">
    <div class="topbar">
      <div class="topbar-logo">DADCARE</div>
      <div class="topbar-title">${t('marketplace')}</div>
      <button class="topbar-action" id="btn-profile">&#9881;</button>
    </div>
    <div class="page">
      <div class="search-bar" style="margin-top:16px">
        <input type="search" id="mkt-search" placeholder="${t('search')}" value="${params.search || ''}">
      </div>
      <div class="category-pills">
        <button class="pill ${!params.category ? 'active' : ''}" data-cat="">Yote / All</button>
        ${catPills}
      </div>
      <div class="card-grid" id="listing-grid">
        ${cards}
      </div>
    </div>
    <div class="bottom-nav">
      <button class="nav-item active">
        <span class="nav-icon">&#127978;</span>
        <span>${t('marketplace')}</span>
      </button>
      <button class="nav-item" id="nav-business">
        <span class="nav-icon">&#128201;</span>
        <span>${t('dashboard')}</span>
      </button>
    </div>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── LISTING DETAIL ───────────────────────────────────────
Router.register('listing-detail', async ({ id }) => {
  const t = App.t.bind(App);
  let listing = null;
  try {
    listing = await API.getListing(id);
  } catch (e) {
    return `<div class="empty"><p>${t('error')}: ${e.message}</p></div>`;
  }

  const imgs = listing.images && listing.images.length
    ? `<img src="${listing.images[0]}" style="width:100%;max-height:280px;object-fit:cover">`
    : `<div style="height:200px;background:var(--bg-card);display:flex;align-items:center;justify-content:center;font-size:60px">&#128722;</div>`;

  const waLink = listing.contact_whatsapp
    ? `https://wa.me/${listing.contact_whatsapp.replace(/\D/g,'')}?text=${encodeURIComponent('Habari, nimeona ' + listing.title + ' kwenye DADCARE. Je, inapatikana?')}`
    : null;

  const phoneLink = listing.contact_phone
    ? 'tel:' + listing.contact_phone : null;

  return `
  <div class="app-shell">
    <div class="topbar">
      <button class="topbar-action" id="btn-back">&#8592;</button>
      <div class="topbar-title">${listing.title}</div>
    </div>
    <div class="page">
      ${imgs}
      <div class="section">
        <h2 class="heading">${listing.title}</h2>
        <div class="mt-8" style="font-size:24px;font-weight:800;color:var(--accent)">
          ${listing.price ? App.formatCurrency(listing.price, listing.currency) : ''}
        </div>
        ${listing.category ? `<div class="mt-8"><span class="badge badge-brand">${listing.category}</span></div>` : ''}
        ${listing.description ? `<p class="body mt-16">${listing.description}</p>` : ''}
        <div class="divider"></div>
        <div class="flex items-center gap-8 mb-8">
          <span style="font-size:20px">&#127979;</span>
          <div>
            <div class="subhead">${listing.seller.name}</div>
            <div class="caption">${listing.city || ''} ${listing.country_code || ''}</div>
          </div>
        </div>
        <div class="divider"></div>
        <p class="label mb-8">${t('contact_seller')}</p>
        <div class="flex flex-col gap-12">
          ${waLink ? `<a href="${waLink}" class="whatsapp-btn" target="_blank">
            <span style="font-size:22px">&#128172;</span>
            WhatsApp
          </a>` : ''}
          ${phoneLink ? `<a href="${phoneLink}" class="btn btn-ghost btn-block">
            <span>&#128222;</span> ${listing.contact_phone}
          </a>` : ''}
        </div>
      </div>
    </div>
  </div>`;
});

// ── LOGIN ────────────────────────────────────────────────
Router.register('login', () => {
  const t = App.t.bind(App);
  return `
  <div class="app-shell">
    <div class="topbar">
      <button class="topbar-action" id="btn-back">&#8592;</button>
      <div class="topbar-title">${t('login')}</div>
    </div>
    <div class="page section">
      <div class="mt-24">
        <div class="form-group">
          <label class="form-label">${t('email')}</label>
          <input type="email" id="inp-email" autocomplete="email" inputmode="email">
        </div>
        <div class="form-group">
          <label class="form-label">${t('password')}</label>
          <input type="password" id="inp-password" autocomplete="current-password">
        </div>
        <button class="btn btn-primary btn-block mt-24" id="btn-login" data-ripple>${t('login')}</button>
        <p class="text-center mt-16 body">
          ${App.lang === 'sw' ? 'Huna akaunti?' : "Don't have an account?"}
          <button class="text-brand bold" style="background:none;border:none;font-size:15px" id="btn-go-register">${t('register')}</button>
        </p>
      </div>
    </div>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── REGISTER ─────────────────────────────────────────────
Router.register('register', () => {
  const t = App.t.bind(App);
  return `
  <div class="app-shell">
    <div class="topbar">
      <button class="topbar-action" id="btn-back">&#8592;</button>
      <div class="topbar-title">${t('register')}</div>
    </div>
    <div class="page section">
      <div class="mt-16">
        <div class="form-group">
          <label class="form-label">${t('full_name')}</label>
          <input type="text" id="inp-name" autocomplete="name">
        </div>
        <div class="form-group">
          <label class="form-label">${t('email')}</label>
          <input type="email" id="inp-email" autocomplete="email" inputmode="email">
        </div>
        <div class="form-group">
          <label class="form-label">${t('password')}</label>
          <input type="password" id="inp-password" autocomplete="new-password">
          <div class="form-hint">${App.lang === 'sw' ? 'Herufi 8 au zaidi' : 'At least 8 characters'}</div>
        </div>
        <button class="btn btn-primary btn-block mt-24" id="btn-register" data-ripple>${t('register')}</button>
        <p class="text-center mt-16 body">
          ${App.lang === 'sw' ? 'Una akaunti?' : 'Already have an account?'}
          <button class="text-brand bold" style="background:none;border:none;font-size:15px" id="btn-go-login">${t('login')}</button>
        </p>
      </div>
    </div>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── BUSINESS SELECTOR ────────────────────────────────────
Router.register('select-business', async () => {
  const t = App.t.bind(App);
  let businesses = [];
  try {
    const data = await API.getProfile();
    businesses = data.businesses || [];
    App.user = data.user;
  } catch (e) {
    Router.navigate('login');
    return '';
  }

  const cards = businesses.length ? businesses.map(b => {
    const statusBadge = {
      trial: `<span class="badge badge-warning">${t('subscription_trial')}</span>`,
      active: `<span class="badge badge-success">${t('subscription_active')}</span>`,
      expired: `<span class="badge badge-danger">${t('subscription_expired')}</span>`,
    }[b.subscription_status] || '';

    return `
    <button class="card card-body flex items-center gap-12" data-business-id="${b.id}" data-ripple style="text-align:left;width:100%">
      <div style="width:48px;height:48px;border-radius:12px;background:var(--brand-glow);display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0">
        &#127978;
      </div>
      <div style="flex:1;min-width:0">
        <div class="subhead" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${b.name}</div>
        <div class="flex gap-8 mt-8 items-center flex-wrap">
          ${statusBadge}
          <span class="badge badge-muted">${t('role_' + b.role) || b.role}</span>
        </div>
      </div>
    </button>`;
  }).join('') : `
  <div class="empty">
    <div class="empty-icon">&#127978;</div>
    <p class="body">${App.lang === 'sw' ? 'Huna biashara bado' : 'No businesses yet'}</p>
  </div>`;

  return `
  <div class="app-shell">
    <div class="topbar">
      <div class="topbar-logo">DADCARE</div>
      <div class="topbar-title">${t('my_businesses')}</div>
    </div>
    <div class="page section">
      <div class="card-list mt-8">
        ${cards}
      </div>
      <div class="flex flex-col gap-12 mt-24">
        <button class="btn btn-primary btn-block" id="btn-create-biz" data-ripple>+ ${t('create_business')}</button>
        <button class="btn btn-ghost btn-block" id="btn-join-biz">&#128279; ${t('join_business')}</button>
        <button class="btn btn-ghost btn-block btn-sm" id="btn-goto-marketplace">&#127978; ${t('marketplace')}</button>
      </div>
    </div>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── SHOP DASHBOARD ───────────────────────────────────────
Router.register('shop-dashboard', async () => {
  const t = App.t.bind(App);
  let stats = {};
  try {
    stats = await API.getDashboard();
  } catch (e) { /* empty stats */ }

  const today = stats.today || {};
  const currency = App.business?.currency || 'TZS';

  return `
  <div class="app-shell">
    <div class="topbar">
      <div class="topbar-logo">DADCARE</div>
      <div class="topbar-title" style="font-size:14px">${App.business?.tenant_name || ''}</div>
      <button class="topbar-action" id="btn-biz-menu">&#9776;</button>
    </div>
    <div class="page">
      <div class="section">
        <p class="label mb-8">${App.lang === 'sw' ? 'Leo' : 'Today'}</p>
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-value">${today.sale_count || 0}</div>
            <div class="stat-label">${t('sales')}</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="font-size:15px">${App.formatCurrency(today.revenue || 0, currency)}</div>
            <div class="stat-label">${App.lang === 'sw' ? 'Mapato' : 'Revenue'}</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color:${stats.low_stock_count > 0 ? 'var(--warning)' : 'var(--success)'}">${stats.low_stock_count || 0}</div>
            <div class="stat-label">${t('low_stock')}</div>
          </div>
        </div>
      </div>
      <div class="section">
        <p class="label mb-12">${App.lang === 'sw' ? 'Mini-Apps' : 'Mini-Apps'}</p>
        <div class="mini-app-grid">
          <button class="mini-app-item" id="nav-products" data-ripple>
            <span class="mini-app-icon">&#128230;</span>
            <span class="mini-app-name">${t('products')}</span>
          </button>
          <button class="mini-app-item" id="nav-sales" data-ripple>
            <span class="mini-app-icon">&#128176;</span>
            <span class="mini-app-name">${t('sales')}</span>
          </button>
          <button class="mini-app-item" id="nav-customers" data-ripple>
            <span class="mini-app-icon">&#128101;</span>
            <span class="mini-app-name">${t('customers')}</span>
          </button>
          <button class="mini-app-item" id="nav-suppliers" data-ripple>
            <span class="mini-app-icon">&#128666;</span>
            <span class="mini-app-name">${t('suppliers')}</span>
          </button>
          <button class="mini-app-item" id="nav-reports" data-ripple>
            <span class="mini-app-icon">&#128202;</span>
            <span class="mini-app-name">${t('reports')}</span>
          </button>
          <button class="mini-app-item" id="nav-settings" data-ripple>
            <span class="mini-app-icon">&#9881;</span>
            <span class="mini-app-name">${t('settings')}</span>
          </button>
        </div>
      </div>
    </div>
    <div class="bottom-nav">
      <button class="nav-item active" id="bn-dash">
        <span class="nav-icon">&#127968;</span>
        <span>${t('dashboard')}</span>
      </button>
      <button class="nav-item" id="bn-products">
        <span class="nav-icon">&#128230;</span>
        <span>${t('products')}</span>
      </button>
      <button class="nav-item" id="bn-sales">
        <span class="nav-icon">&#128176;</span>
        <span>${t('sales')}</span>
      </button>
      <button class="nav-item" id="bn-marketplace">
        <span class="nav-icon">&#127978;</span>
        <span>${t('marketplace')}</span>
      </button>
    </div>
    <button class="fab" id="btn-pos" title="${t('new_sale')}">&#43;</button>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── PRODUCTS LIST ─────────────────────────────────────────
Router.register('products', async () => {
  const t = App.t.bind(App);
  let products = [];
  try {
    const data = await API.getProducts({});
    products = data.products || [];
  } catch (e) { /* empty */ }

  const rows = products.length ? products.map(p => `
    <div class="card card-body flex items-center gap-12" style="cursor:pointer" data-product-id="${p.id}" data-ripple>
      <div style="width:48px;height:48px;border-radius:10px;background:var(--bg-card2);display:flex;align-items:center;justify-content:center;flex-shrink:0;overflow:hidden">
        ${p.images && p.images[0]
          ? `<img src="${p.images[0]}" style="width:100%;height:100%;object-fit:cover">`
          : '<span style="font-size:24px">&#128230;</span>'}
      </div>
      <div style="flex:1;min-width:0">
        <div class="subhead">${p.name}</div>
        <div class="flex items-center gap-8 mt-4">
          <span class="caption text-accent bold">${App.formatCurrency(p.selling_price)}</span>
          <span class="${p.is_low_stock ? 'stock-dot low' : (p.stock_quantity === 0 ? 'stock-dot out' : 'stock-dot ok')}"></span>
          <span class="caption text-muted">${p.stock_quantity} ${p.unit || 'pcs'}</span>
        </div>
      </div>
    </div>`).join('')
  : `<div class="empty"><div class="empty-icon">&#128230;</div><p class="body">${t('no_results')}</p></div>`;

  return `
  <div class="app-shell">
    <div class="topbar">
      <button class="topbar-action" id="btn-back">&#8592;</button>
      <div class="topbar-title">${t('products')}</div>
      <button class="topbar-action" id="btn-add-product">&#43;</button>
    </div>
    <div class="page">
      <div class="search-bar" style="margin-top:16px">
        <input type="search" id="product-search" placeholder="${t('search')}">
      </div>
      <div class="card-list" id="product-list">
        ${rows}
      </div>
    </div>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── POS (NEW SALE) ────────────────────────────────────────
Router.register('pos', async () => {
  const t = App.t.bind(App);
  App.cart = [];
  let products = [];
  try {
    const data = await API.getProducts({ per_page: 200 });
    products = data.products || [];
  } catch (e) { /* empty */ }

  const prodRows = products.map(p => `
    <div class="card card-body flex items-center gap-12" style="cursor:pointer" data-add-to-cart
         data-id="${p.id}" data-name="${p.name.replace(/"/g,'&quot;')}"
         data-price="${p.selling_price}" data-stock="${p.stock_quantity}" data-ripple>
      <div style="flex:1">
        <div class="subhead">${p.name}</div>
        <div class="caption text-accent">${App.formatCurrency(p.selling_price)}</div>
      </div>
      <div class="caption text-muted">${p.stock_quantity} ${p.unit || 'pcs'}</div>
      <div style="width:32px;height:32px;border-radius:50%;background:var(--brand);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">+</div>
    </div>`).join('');

  return `
  <div class="app-shell">
    <div class="topbar">
      <button class="topbar-action" id="btn-back">&#8592;</button>
      <div class="topbar-title">${t('new_sale')}</div>
      <button class="btn btn-accent btn-sm" id="btn-checkout" style="padding:8px 14px">${t('receive_payment')}</button>
    </div>
    <div class="page">
      <div id="cart-section" class="section" style="display:none">
        <p class="label mb-8">${App.lang === 'sw' ? 'Kikapu' : 'Cart'}</p>
        <div id="cart-items"></div>
        <div class="receipt-total mt-8">
          <span>${t('total')}</span>
          <span id="cart-total">TZS 0</span>
        </div>
      </div>
      <div class="section">
        <p class="label mb-8">${t('products')}</p>
        <div class="search-bar" style="margin:0 0 12px">
          <input type="search" id="pos-search" placeholder="${t('search')}">
        </div>
        <div class="card-list" id="pos-product-list">
          ${prodRows}
        </div>
      </div>
    </div>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── SALES HISTORY ─────────────────────────────────────────
Router.register('sales', async () => {
  const t = App.t.bind(App);
  let sales = [];
  try {
    const data = await API.getSales({});
    sales = data.sales || [];
  } catch (e) { /* empty */ }

  const rows = sales.length ? sales.map(s => `
    <div class="card card-body flex items-center gap-12" style="cursor:pointer" data-sale-id="${s.id}" data-ripple>
      <div style="flex:1">
        <div class="subhead">${s.sale_number}</div>
        <div class="caption text-muted">${App.formatDate(s.created_at)} &bull; ${s.payment_method}</div>
      </div>
      <div>
        <div class="bold text-accent">${App.formatCurrency(s.total)}</div>
        <span class="badge ${s.status === 'voided' ? 'badge-danger' : 'badge-success'}">${s.status}</span>
      </div>
    </div>`).join('')
  : `<div class="empty"><div class="empty-icon">&#128176;</div><p class="body">${t('no_results')}</p></div>`;

  return `
  <div class="app-shell">
    <div class="topbar">
      <button class="topbar-action" id="btn-back">&#8592;</button>
      <div class="topbar-title">${t('sales')}</div>
    </div>
    <div class="page">
      <div class="card-list section">
        ${rows}
      </div>
    </div>
    <button class="fab" id="btn-pos">&#43;</button>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── RECEIPT PAGE ──────────────────────────────────────────
Router.register('receipt', async ({ saleId }) => {
  const t = App.t.bind(App);
  let sale = null, items = [], shop = {};
  try {
    const data = await API.getSale(saleId);
    sale = data.sale;
    items = data.items;
    shop = data.shop || {};
  } catch (e) {
    return `<div class="empty"><p>${e.message}</p></div>`;
  }

  const itemRows = items.map(i => `
    <div class="receipt-row">
      <span>${i.product_name} x${i.quantity}</span>
      <span>${App.formatCurrency(i.total_price, shop.currency || 'TZS')}</span>
    </div>`).join('');

  const waText = encodeURIComponent(
    (shop.shop_name || 'DADCARE') + ' - ' + t('receipt') + '\n' +
    t('sales') + ': ' + sale.sale_number + '\n' +
    t('total') + ': ' + App.formatCurrency(sale.total, shop.currency || 'TZS') + '\n' +
    t('payment_method') + ': ' + sale.payment_method
  );
  const waLink = shop.whatsapp
    ? `https://wa.me/${shop.whatsapp.replace(/\D/g,'')}?text=${waText}` : null;

  return `
  <div class="app-shell">
    <div class="topbar">
      <button class="topbar-action" id="btn-back">&#8592;</button>
      <div class="topbar-title">${t('receipt')}</div>
    </div>
    <div class="page section">
      <div class="receipt">
        <div class="receipt-header">
          <div style="font-size:20px;font-weight:800">${shop.shop_name || 'DADCARE'}</div>
          <div style="font-size:13px;opacity:0.85;margin-top:4px">${sale.sale_number} &bull; ${App.formatDate(sale.created_at)}</div>
        </div>
        <div class="receipt-body">
          ${itemRows}
          <div class="divider"></div>
          <div class="receipt-row">
            <span>${App.lang === 'sw' ? 'Jumla Ndogo' : 'Subtotal'}</span>
            <span>${App.formatCurrency(sale.subtotal, shop.currency || 'TZS')}</span>
          </div>
          ${sale.discount > 0 ? `<div class="receipt-row"><span>${App.lang === 'sw' ? 'Punguzo' : 'Discount'}</span><span>-${App.formatCurrency(sale.discount, shop.currency || 'TZS')}</span></div>` : ''}
          ${sale.tax > 0 ? `<div class="receipt-row"><span>${App.lang === 'sw' ? 'Kodi' : 'Tax'}</span><span>${App.formatCurrency(sale.tax, shop.currency || 'TZS')}</span></div>` : ''}
          <div class="receipt-total">
            <span>${t('total')}</span>
            <span>${App.formatCurrency(sale.total, shop.currency || 'TZS')}</span>
          </div>
          <div class="caption text-center mt-8 text-muted">${t('payment_method')}: ${sale.payment_method}</div>
          ${shop.receipt_footer ? `<div class="caption text-center mt-8">${shop.receipt_footer}</div>` : ''}
        </div>
      </div>
      <div class="flex flex-col gap-12 mt-16">
        ${waLink ? `<a href="${waLink}" class="whatsapp-btn" target="_blank">&#128172; ${t('share_whatsapp')}</a>` : ''}
        <button class="btn btn-ghost btn-block" id="btn-new-sale">+ ${t('new_sale')}</button>
      </div>
    </div>
    <div id="toast-container" class="toast-container"></div>
  </div>`;
});

// ── EVENT BINDINGS (runs after each page render) ──────────
document.addEventListener('page:rendered', ({ detail: { page, params } }) => {
  Toast.init();

  // ── Lang select
  document.querySelectorAll('[data-lang]').forEach(btn => {
    btn.onclick = () => {
      App.setLang(btn.dataset.lang);
      Router.navigate('welcome');
    };
  });

  // ── Welcome
  document.getElementById('btn-browse')?.addEventListener('click', () => Router.navigate('marketplace'));
  document.getElementById('btn-business')?.addEventListener('click', () => {
    App.user ? Router.navigate('select-business') : Router.navigate('login');
  });
  document.getElementById('btn-change-lang')?.addEventListener('click', () => Router.navigate('lang-select'));

  // ── Back buttons
  document.querySelectorAll('#btn-back').forEach(b => b.onclick = () => Router.navigate('shop-dashboard'));

  // ── Login
  document.getElementById('btn-login')?.addEventListener('click', async () => {
    const email = document.getElementById('inp-email')?.value.trim();
    const password = document.getElementById('inp-password')?.value;
    if (!email || !password) { Toast.error(App.lang === 'sw' ? 'Jaza sehemu zote' : 'Fill all fields'); return; }
    try {
      const data = await API.login({ email, password });
      App.user = data.user;
      Toast.success(App.lang === 'sw' ? 'Umeingia!' : 'Logged in!');
      setTimeout(() => Router.navigate('select-business'), 700);
    } catch (e) { Toast.error(e.message); }
  });
  document.getElementById('btn-go-register')?.addEventListener('click', () => Router.navigate('register'));

  // ── Register
  document.getElementById('btn-register')?.addEventListener('click', async () => {
    const name = document.getElementById('inp-name')?.value.trim();
    const email = document.getElementById('inp-email')?.value.trim();
    const password = document.getElementById('inp-password')?.value;
    if (!name || !email || !password) { Toast.error(App.lang === 'sw' ? 'Jaza sehemu zote' : 'Fill all fields'); return; }
    try {
      const data = await API.register({ full_name: name, email, password, language: App.lang });
      App.user = data.user;
      Toast.success(App.lang === 'sw' ? 'Akaunti imeundwa!' : 'Account created!');
      setTimeout(() => Router.navigate('select-business'), 700);
    } catch (e) { Toast.error(e.message); }
  });
  document.getElementById('btn-go-login')?.addEventListener('click', () => Router.navigate('login'));

  // ── Business select
  document.querySelectorAll('[data-business-id]').forEach(btn => {
    btn.onclick = async () => {
      try {
        const data = await API.selectBusiness(btn.dataset.businessId);
        App.business = data.business;
        Toast.success(data.business.name);
        setTimeout(() => Router.navigate('shop-dashboard'), 500);
      } catch (e) { Toast.error(e.message); }
    };
  });
  document.getElementById('btn-create-biz')?.addEventListener('click', () => Router.navigate('create-business'));
  document.getElementById('btn-join-biz')?.addEventListener('click', () => {
    const code = prompt(App.t('invite_code'));
    if (code) API.joinBusiness(code.trim()).then(() => Router.navigate('select-business')).catch(e => Toast.error(e.message));
  });
  document.getElementById('btn-goto-marketplace')?.addEventListener('click', () => Router.navigate('marketplace'));

  // ── Dashboard nav
  document.getElementById('nav-products')?.addEventListener('click', () => Router.navigate('products'));
  document.getElementById('nav-sales')?.addEventListener('click', () => Router.navigate('sales'));
  document.getElementById('btn-pos')?.addEventListener('click', () => Router.navigate('pos'));
  document.querySelectorAll('#bn-products, .btn-products').forEach(b => b.onclick = () => Router.navigate('products'));
  document.querySelectorAll('#bn-sales').forEach(b => b.onclick = () => Router.navigate('sales'));
  document.querySelectorAll('#bn-marketplace').forEach(b => b.onclick = () => Router.navigate('marketplace'));

  // ── Marketplace listing click
  document.querySelectorAll('[data-id].product-card').forEach(card => {
    card.onclick = () => Router.navigate('listing-detail', { id: card.dataset.id });
  });

  // ── Marketplace search
  const mktSearch = document.getElementById('mkt-search');
  if (mktSearch) {
    let timer;
    mktSearch.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => Router.navigate('marketplace', { search: mktSearch.value.trim() }), 600);
    });
  }

  // ── Category pills
  document.querySelectorAll('.pill[data-cat]').forEach(pill => {
    pill.onclick = () => Router.navigate('marketplace', { category: pill.dataset.cat });
  });

  // ── Product search (shop)
  const prodSearch = document.getElementById('product-search');
  if (prodSearch) {
    let timer;
    prodSearch.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        try {
          const data = await API.getProducts({ search: prodSearch.value.trim() });
          const list = document.getElementById('product-list');
          if (!list) return;
          list.innerHTML = data.products.map(p => `
            <div class="card card-body flex items-center gap-12" style="cursor:pointer" data-product-id="${p.id}">
              <div style="flex:1"><div class="subhead">${p.name}</div>
              <div class="caption text-accent bold">${App.formatCurrency(p.selling_price)}</div></div>
              <span class="caption text-muted">${p.stock_quantity}</span>
            </div>`).join('') || `<div class="empty"><p>${App.t('no_results')}</p></div>`;
        } catch (e) { Toast.error(e.message); }
      }, 500);
    });
  }

  // ── Add product button
  document.getElementById('btn-add-product')?.addEventListener('click', () => {
    Sheet.show(`
      <div class="form-group"><label class="form-label">${App.t('full_name').replace('Name','Product Name')}</label><input id="sh-name" type="text"></div>
      <div class="form-group"><label class="form-label">${App.t('price')}</label><input id="sh-price" type="number" inputmode="decimal"></div>
      <div class="form-group"><label class="form-label">${App.lang==='sw'?'Stoo':'Stock'}</label><input id="sh-stock" type="number" inputmode="numeric" value="0"></div>
      <button class="btn btn-primary btn-block" id="sh-save-product">${App.t('save')}</button>
    `, App.t('add_product'));

    document.getElementById('sh-save-product')?.addEventListener('click', async () => {
      const name = document.getElementById('sh-name')?.value.trim();
      const price = document.getElementById('sh-price')?.value;
      const stock = document.getElementById('sh-stock')?.value || 0;
      if (!name || !price) { Toast.error(App.lang==='sw'?'Jaza jina na bei':'Fill name and price'); return; }
      try {
        await API.createProduct({ name, selling_price: parseFloat(price), stock_quantity: parseInt(stock) });
        Sheet.hide();
        Toast.success(App.lang==='sw'?'Bidhaa imeongezwa!':'Product added!');
        Router.navigate('products');
      } catch (e) { Toast.error(e.message); }
    });
  });

  // ── POS: add to cart
  document.querySelectorAll('[data-add-to-cart]').forEach(btn => {
    btn.onclick = () => {
      const { id, name, price, stock } = btn.dataset;
      const existing = App.cart.find(i => i.id === id);
      if (existing) {
        if (existing.qty >= parseInt(stock)) { Toast.error(App.lang==='sw'?'Stoo haitoshi':'Insufficient stock'); return; }
        existing.qty++;
      } else {
        App.cart.push({ id, name, price: parseFloat(price), qty: 1, stock: parseInt(stock) });
      }
      updateCart();
    };
  });

  // ── POS search
  const posSearch = document.getElementById('pos-search');
  if (posSearch) {
    posSearch.addEventListener('input', () => {
      const q = posSearch.value.toLowerCase();
      document.querySelectorAll('#pos-product-list [data-add-to-cart]').forEach(el => {
        el.style.display = el.dataset.name.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }

  // ── POS checkout
  document.getElementById('btn-checkout')?.addEventListener('click', () => {
    if (!App.cart.length) { Toast.error(App.lang==='sw'?'Kikapu kiko tupu':'Cart is empty'); return; }
    const total = App.cart.reduce((s, i) => s + i.price * i.qty, 0);
    Sheet.show(`
      <div class="mb-16">
        ${App.cart.map(i => `<div class="receipt-row"><span>${i.name} x${i.qty}</span><span>${App.formatCurrency(i.price*i.qty)}</span></div>`).join('')}
        <div class="receipt-total"><span>${App.t('total')}</span><span>${App.formatCurrency(total)}</span></div>
      </div>
      <div class="form-group">
        <label class="form-label">${App.t('payment_method')}</label>
        <select id="sh-payment">
          <option value="cash">${App.t('cash')}</option>
          <option value="mpesa">M-Pesa</option>
          <option value="tigopesa">Tigo Pesa</option>
          <option value="airtelmoney">Airtel Money</option>
          <option value="bank_transfer">Bank Transfer</option>
        </select>
      </div>
      <button class="btn btn-accent btn-block" id="sh-confirm-sale">${App.t('confirm')}</button>
    `, App.t('receive_payment'));

    document.getElementById('sh-confirm-sale')?.addEventListener('click', async () => {
      const method = document.getElementById('sh-payment')?.value || 'cash';
      try {
        const result = await API.processSale({
          items: App.cart.map(i => ({ product_id: i.id, quantity: i.qty, unit_price: i.price })),
          payment_method: method,
        });
        Sheet.hide();
        App.cart = [];
        Toast.success(App.lang==='sw'?'Mauzo yamekamilika!':'Sale complete!');
        setTimeout(() => Router.navigate('receipt', { saleId: result.sale_id }), 600);
      } catch (e) { Toast.error(e.message); }
    });
  });

  // ── Receipt
  document.getElementById('btn-new-sale')?.addEventListener('click', () => Router.navigate('pos'));

  // ── Sales history: click sale
  document.querySelectorAll('[data-sale-id]').forEach(el => {
    el.onclick = () => Router.navigate('receipt', { saleId: el.dataset.saleId });
  });
});

// ── CART UPDATE HELPER ────────────────────────────────────
function updateCart() {
  const section = document.getElementById('cart-section');
  const itemsEl = document.getElementById('cart-items');
  const totalEl = document.getElementById('cart-total');
  if (!section || !itemsEl) return;

  if (!App.cart.length) { section.style.display = 'none'; return; }
  section.style.display = '';

  const total = App.cart.reduce((s, i) => s + i.price * i.qty, 0);
  if (totalEl) totalEl.textContent = App.formatCurrency(total);

  itemsEl.innerHTML = App.cart.map(item => `
    <div class="cart-item">
      <div class="cart-item-name">${item.name}</div>
      <div class="cart-item-qty">
        <button class="qty-btn" data-dec="${item.id}">-</button>
        <span class="qty-val">${item.qty}</span>
        <button class="qty-btn" data-inc="${item.id}">+</button>
      </div>
      <span class="caption text-accent">${App.formatCurrency(item.price * item.qty)}</span>
    </div>`).join('');

  itemsEl.querySelectorAll('[data-dec]').forEach(b => {
    b.onclick = () => {
      const item = App.cart.find(i => i.id === b.dataset.dec);
      if (item) { item.qty > 1 ? item.qty-- : App.cart.splice(App.cart.indexOf(item), 1); }
      updateCart();
    };
  });
  itemsEl.querySelectorAll('[data-inc]').forEach(b => {
    b.onclick = () => {
      const item = App.cart.find(i => i.id === b.dataset.inc);
      if (item && item.qty < item.stock) item.qty++;
      updateCart();
    };
  });
}
