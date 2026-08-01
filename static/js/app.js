/**
 * DADCARE — Core JS
 * No framework. Android WebView safe. No emojis in JS strings.
 * i18n, API helpers, toast, router.
 */

'use strict';

// ── TRANSLATIONS ──────────────────────────────────────────
const TRANSLATIONS = {
  sw: {
    app_name: 'DADCARE',
    tagline: 'Mfumo wa Biashara wa Afrika',
    browse: 'Tazama Bidhaa',
    i_have_business: 'Nina Biashara',
    browse_sub: 'Tafuta bidhaa bila usajili',
    business_sub: 'Simamia biashara yako',
    select_language: 'Chagua Lugha',
    english: 'English',
    swahili: 'Kiswahili',
    continue: 'Endelea',
    login: 'Ingia',
    register: 'Jisajili',
    logout: 'Toka',
    email: 'Barua pepe',
    password: 'Nywila',
    full_name: 'Jina Kamili',
    search: 'Tafuta...',
    products: 'Bidhaa',
    sales: 'Mauzo',
    stock: 'Stoo',
    reports: 'Ripoti',
    settings: 'Mipangilio',
    dashboard: 'Dashibodi',
    customers: 'Wateja',
    suppliers: 'Wasambazaji',
    orders: 'Maagizo',
    staff: 'Wafanyakazi',
    marketplace: 'Soko',
    new_sale: 'Uuzaji Mpya',
    add_product: 'Ongeza Bidhaa',
    save: 'Hifadhi',
    cancel: 'Ghairi',
    delete: 'Futa',
    confirm: 'Thibitisha',
    loading: 'Inapakia...',
    error: 'Hitilafu',
    success: 'Imefanikiwa',
    no_results: 'Hakuna matokeo',
    coming_soon: 'Inakuja Hivi Karibuni',
    contact_seller: 'Wasiliana na Muuzaji',
    price: 'Bei',
    quantity: 'Idadi',
    total: 'Jumla',
    payment_method: 'Njia ya Malipo',
    cash: 'Pesa Taslimu',
    mpesa: 'M-Pesa',
    receive_payment: 'Pokea Malipo',
    void: 'Batilisha',
    receipt: 'Risiti',
    share_whatsapp: 'Shiriki WhatsApp',
    low_stock: 'Stoo Chini',
    out_of_stock: 'Stoo Imekwisha',
    trial_expires: 'Jaribio Linaisha',
    days_left: 'siku zilizobaki',
    my_businesses: 'Biashara Zangu',
    create_business: 'Unda Biashara',
    join_business: 'Jiunge na Biashara',
    invite_code: 'Nambari ya Mwaliko',
    role_owner: 'Mmiliki',
    role_manager: 'Meneja',
    role_cashier: 'Mhesabu',
    role_staff: 'Mfanyakazi',
    subscription_active: 'Usajili Hai',
    subscription_trial: 'Kipindi cha Majaribio',
    subscription_expired: 'Usajili Umekwisha',
    pay_subscription: 'Lipa Usajili',
  },
  en: {
    app_name: 'DADCARE',
    tagline: 'Business Ecosystem for Africa',
    browse: 'Browse Products',
    i_have_business: 'I Have a Business',
    browse_sub: 'Find products without signing up',
    business_sub: 'Manage your business',
    select_language: 'Select Language',
    english: 'English',
    swahili: 'Kiswahili',
    continue: 'Continue',
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    email: 'Email',
    password: 'Password',
    full_name: 'Full Name',
    search: 'Search...',
    products: 'Products',
    sales: 'Sales',
    stock: 'Stock',
    reports: 'Reports',
    settings: 'Settings',
    dashboard: 'Dashboard',
    customers: 'Customers',
    suppliers: 'Suppliers',
    orders: 'Orders',
    staff: 'Staff',
    marketplace: 'Marketplace',
    new_sale: 'New Sale',
    add_product: 'Add Product',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    confirm: 'Confirm',
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    no_results: 'No results found',
    coming_soon: 'Coming Soon',
    contact_seller: 'Contact Seller',
    price: 'Price',
    quantity: 'Quantity',
    total: 'Total',
    payment_method: 'Payment Method',
    cash: 'Cash',
    mpesa: 'M-Pesa',
    receive_payment: 'Receive Payment',
    void: 'Void',
    receipt: 'Receipt',
    share_whatsapp: 'Share on WhatsApp',
    low_stock: 'Low Stock',
    out_of_stock: 'Out of Stock',
    trial_expires: 'Trial Expires',
    days_left: 'days left',
    my_businesses: 'My Businesses',
    create_business: 'Create Business',
    join_business: 'Join a Business',
    invite_code: 'Invite Code',
    role_owner: 'Owner',
    role_manager: 'Manager',
    role_cashier: 'Cashier',
    role_staff: 'Staff',
    subscription_active: 'Subscription Active',
    subscription_trial: 'Trial Period',
    subscription_expired: 'Subscription Expired',
    pay_subscription: 'Pay Subscription',
  }
};

// ── STATE ────────────────────────────────────────────────
const App = {
  lang: localStorage.getItem('dadcare_lang') || 'sw',
  user: null,
  business: null,
  cart: [],

  t(key) {
    return (TRANSLATIONS[this.lang] || TRANSLATIONS.sw)[key] || key;
  },

  setLang(lang) {
    this.lang = lang;
    localStorage.setItem('dadcare_lang', lang);
    document.documentElement.lang = lang;
  },

  formatCurrency(amount, currency = 'TZS') {
    const num = parseFloat(amount) || 0;
    const formatted = num.toLocaleString('sw-TZ', { minimumFractionDigits: 0 });
    return currency + ' ' + formatted;
  },

  formatDate(iso) {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString(this.lang === 'sw' ? 'sw-TZ' : 'en-TZ', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  },
};

// ── API HELPERS ──────────────────────────────────────────
const API = {
  base: '/api',

  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
    };
    if (body) opts.body = JSON.stringify(body);

    try {
      const res = await fetch(this.base + path, opts);
      const data = await res.json();
      if (!res.ok) throw new APIError(data.error || App.t('error'), res.status);
      return data;
    } catch (e) {
      if (e instanceof APIError) throw e;
      throw new APIError('Hitilafu ya mtandao. Angalia muunganisho wako.', 0);
    }
  },

  get(path)         { return this.request('GET', path); },
  post(path, body)  { return this.request('POST', path, body); },
  patch(path, body) { return this.request('PATCH', path, body); },
  delete(path)      { return this.request('DELETE', path); },

  // Auth
  register(data)         { return this.post('/auth/register/', data); },
  login(data)            { return this.post('/auth/login/', data); },
  logout()               { return this.post('/auth/logout/'); },
  getProfile()           { return this.get('/auth/profile/'); },
  selectBusiness(tid)    { return this.post('/auth/select-business/', { tenant_id: tid }); },

  // Marketplace (public)
  getMarketplace(params) { return this.get('/marketplace/?' + new URLSearchParams(params)); },
  getListing(id)         { return this.get('/marketplace/' + id + '/'); },
  getCategories()        { return this.get('/marketplace/categories/'); },
  submitListing(data)    { return this.post('/marketplace/listings/submit/', data); },
  getMyListings()        { return this.get('/marketplace/listings/mine/'); },

  // Tenants
  getMiniApps()          { return this.get('/tenants/mini-apps/'); },
  createBusiness(data)   { return this.post('/tenants/create/', data); },
  getMyBusiness()        { return this.get('/tenants/me/'); },
  getMembers()           { return this.get('/tenants/members/'); },
  createInvite(data)     { return this.post('/tenants/invite/', data); },
  joinBusiness(code)     { return this.post('/tenants/join/', { code }); },

  // Shop
  getDashboard()         { return this.get('/shop/dashboard/'); },
  getProducts(params)    { return this.get('/shop/products/?' + new URLSearchParams(params)); },
  getProduct(id)         { return this.get('/shop/products/' + id + '/'); },
  createProduct(data)    { return this.post('/shop/products/create/', data); },
  updateProduct(id, d)   { return this.patch('/shop/products/' + id + '/update/', d); },
  adjustStock(id, data)  { return this.post('/shop/products/' + id + '/adjust-stock/', data); },
  getSales(params)       { return this.get('/shop/sales/?' + new URLSearchParams(params)); },
  getSale(id)            { return this.get('/shop/sales/' + id + '/'); },
  processSale(data)      { return this.post('/shop/sales/new/', data); },
  voidSale(id, reason)   { return this.post('/shop/sales/' + id + '/void/', { reason }); },
  getCustomers(q)        { return this.get('/shop/customers/?' + new URLSearchParams({ search: q })); },
  createCustomer(data)   { return this.post('/shop/customers/create/', data); },
  getSuppliers()         { return this.get('/shop/suppliers/'); },
  getSalesReport(p)      { return this.get('/shop/reports/sales/?' + new URLSearchParams(p)); },
  getSettings()          { return this.get('/shop/settings/'); },
  saveSettings(data)     { return this.post('/shop/settings/update/', data); },
};

class APIError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

// ── TOAST SYSTEM ────────────────────────────────────────
const Toast = {
  container: null,

  init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 3200) {
    if (!this.container) this.init();
    const icons = { success: 'check-circle', error: 'x-circle', info: 'info' };
    const emojiMap = { success: '[OK]', error: '[!]', info: '[i]' };

    const el = document.createElement('div');
    el.className = 'toast ' + type;
    el.innerHTML = '<span class="toast-icon">' + emojiMap[type] + '</span><span>' + message + '</span>';
    this.container.appendChild(el);

    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px)';
      el.style.transition = 'all 0.2s';
      setTimeout(() => el.remove(), 200);
    }, duration);
  },

  success(msg) { this.show(msg, 'success'); },
  error(msg)   { this.show(msg, 'error'); },
  info(msg)    { this.show(msg, 'info'); },
};

// ── SHEET (bottom drawer) ────────────────────────────────
const Sheet = {
  overlay: null,
  sheet: null,

  show(contentHTML, title = '') {
    // Remove existing
    document.getElementById('sheet-overlay')?.remove();

    const overlay = document.createElement('div');
    overlay.id = 'sheet-overlay';
    overlay.className = 'overlay';
    overlay.onclick = () => this.hide();

    const sheet = document.createElement('div');
    sheet.id = 'active-sheet';
    sheet.className = 'sheet';
    sheet.innerHTML = '<div class="sheet-handle"></div>' +
      (title ? '<h3 class="heading mb-16">' + title + '</h3>' : '') +
      contentHTML;

    document.body.appendChild(overlay);
    document.body.appendChild(sheet);

    requestAnimationFrame(() => {
      overlay.classList.add('visible');
      sheet.classList.add('visible');
    });
  },

  hide() {
    const overlay = document.getElementById('sheet-overlay');
    const sheet = document.getElementById('active-sheet');
    if (overlay) { overlay.classList.remove('visible'); setTimeout(() => overlay.remove(), 280); }
    if (sheet)   { sheet.classList.remove('visible');   setTimeout(() => sheet.remove(), 280); }
  },
};

// ── ROUTER ──────────────────────────────────────────────
const Router = {
  routes: {},
  currentPage: null,

  register(name, renderFn) {
    this.routes[name] = renderFn;
  },

  async navigate(page, params = {}) {
    const render = this.routes[page];
    if (!render) { console.warn('Unknown page:', page); return; }

    const shell = document.getElementById('app');
    if (!shell) return;

    shell.innerHTML = '<div class="app-shell"><div class="page"><div class="empty"><div class="spinner"></div></div></div></div>';

    try {
      const html = await render(params);
      shell.innerHTML = html;
      this.currentPage = page;
      window.history.pushState({ page, params }, '', '#' + page);
      // Re-bind all event listeners
      document.dispatchEvent(new CustomEvent('page:rendered', { detail: { page, params } }));
    } catch (e) {
      Toast.error(e.message || App.t('error'));
    }
  },
};

// ── RIPPLE EFFECT ────────────────────────────────────────
document.addEventListener('click', (e) => {
  const target = e.target.closest('[data-ripple]');
  if (!target) return;
  const ripple = document.createElement('span');
  const rect = target.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  ripple.style.cssText = [
    'position:absolute', 'border-radius:50%',
    'background:rgba(255,255,255,0.18)',
    'width:' + size + 'px', 'height:' + size + 'px',
    'left:' + (e.clientX - rect.left - size/2) + 'px',
    'top:' + (e.clientY - rect.top - size/2) + 'px',
    'transform:scale(0)', 'animation:ripple 0.5s linear',
    'pointer-events:none'
  ].join(';');
  target.style.position = 'relative';
  target.style.overflow = 'hidden';
  target.appendChild(ripple);
  setTimeout(() => ripple.remove(), 500);
});

// ── INIT ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  Toast.init();
  document.documentElement.lang = App.lang;

  // Determine start screen
  const lang = localStorage.getItem('dadcare_lang');
  if (!lang) {
    Router.navigate('lang-select');
    return;
  }

  // Check auth
  try {
    const data = await API.getProfile();
    App.user = data.user;
    App.business = data.active_business;

    if (App.business) {
      Router.navigate('shop-dashboard');
    } else {
      Router.navigate('welcome');
    }
  } catch (e) {
    Router.navigate('welcome');
  }
});
