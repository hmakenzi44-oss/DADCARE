'use strict';

let _products = [];
let _productPage = 1;
let _productSearch = '';
let _productFilter = '';

Router.register('products', async (params = {}) => {
  _productFilter = params.filter || '';
  return renderProductsPage(await loadProducts());
});

async function loadProducts(page = 1, search = _productSearch, filter = _productFilter) {
  _productPage = page;
  const p = {page, per_page: 50};
  if (search) p.search = search;
  if (filter === 'low_stock') p.low_stock = '1';
  try {
    const data = await API.getProducts(p);
    _products = data.products || [];
    return data;
  } catch (e) {
    Toast.error(e.message);
    return {products: [], total: 0};
  }
}

function renderProductsPage(data) {
  const role = State.business?.role || 'staff';
  const canEdit = ['owner','manager'].includes(role);
  const rows = renderProductRows(data.products || []);

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('dashboard')">&#8592;</button>
    <span class="topbar-title">Bidhaa</span>
    ${canEdit ? `<button class="topbar-action text-brand" onclick="showAddProduct()" title="Ongeza">+</button>` : ''}
  </div>
  <div class="page">
    <div class="search-wrap">
      <div class="search-bar">
        <input id="prod-search" type="search" placeholder="Tafuta bidhaa au barcode..." value="${_productSearch}"
          oninput="debounce(()=>searchProducts(this.value),500)">
      </div>
    </div>
    <div class="filter-tabs">
      <button class="filter-tab ${!_productFilter?'active':''}" onclick="filterProducts('')">Zote</button>
      <button class="filter-tab ${_productFilter==='low_stock'?'active':''}" onclick="filterProducts('low_stock')">Stoo Chini</button>
    </div>
    <div class="px-16 mb-8 flex justify-between items-center">
      <span style="font-size:12px;color:var(--text-muted)">${data.total || 0} bidhaa</span>
      <div class="flex gap-8">
        <button class="btn btn-ghost btn-sm" id="btn-view-grid" onclick="setView('grid')" title="Grid">&#9783;</button>
        <button class="btn btn-ghost btn-sm" id="btn-view-list" onclick="setView('list')" title="List">&#9776;</button>
      </div>
    </div>
    <div id="products-container" class="product-list-view">
      ${rows}
    </div>
    <div id="prod-pagination"></div>
  </div>

  <div class="bottom-nav">
    <button class="nav-item" onclick="Router.go('dashboard')"><span class="nav-icon">&#127968;</span><span>Nyumbani</span></button>
    <button class="nav-item active" data-page="products"><span class="nav-icon">&#128230;</span><span>Bidhaa</span></button>
    <button class="nav-item" onclick="Router.go('pos')">
      <div style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,var(--brand),#7B8FFF);display:flex;align-items:center;justify-content:center;margin-top:-20px;box-shadow:0 4px 16px rgba(91,110,245,0.4)">
        <span style="font-size:24px;color:#fff">+</span>
      </div>
      <span>Uza</span>
    </button>
    <button class="nav-item" onclick="Router.go('sales')"><span class="nav-icon">&#128176;</span><span>Mauzo</span></button>
    <button class="nav-item" onclick="Router.go('more')"><span class="nav-icon">&#8942;</span><span>Zaidi</span></button>
  </div>`;
}

function renderProductRows(products) {
  if (!products.length) return `<div class="empty"><div class="empty-icon">&#128230;</div><div class="empty-text">Hakuna bidhaa</div><div class="empty-sub">Bonyeza + kuongeza bidhaa ya kwanza</div></div>`;

  return `<div class="card mx-16">` + products.map(p => {
    const stockClass = p.stock_quantity === 0 ? 'stock-out' : p.is_low_stock ? 'stock-low' : 'stock-ok';
    const stockLabel = p.stock_quantity === 0 ? 'Imekwisha' : p.is_low_stock ? 'Chini' : 'Sawa';
    return `
    <div class="list-item" onclick="showProductDetail('${p.id}')">
      <div class="list-item-icon brand" style="border-radius:10px;overflow:hidden">
        ${p.images && p.images[0] ? `<img src="${p.images[0]}" style="width:100%;height:100%;object-fit:cover">` : '<span style="font-size:22px">&#128230;</span>'}
      </div>
      <div class="list-item-body">
        <div class="list-item-title">${p.name}</div>
        <div class="list-item-sub flex items-center gap-8">
          <span class="stock-dot ${stockClass}"></span>
          <span>${p.stock_quantity} ${p.unit || 'pcs'} • ${stockLabel}</span>
          ${p.category ? `<span>• ${p.category}</span>` : ''}
        </div>
      </div>
      <div class="list-item-right">
        <div class="list-item-value text-accent">${fmtCurrency(p.selling_price)}</div>
        ${p.cost_price ? `<div class="list-item-meta">Gharama: ${fmtCurrency(p.cost_price)}</div>` : ''}
      </div>
    </div>`;
  }).join('') + '</div>';
}

document.addEventListener('page:ready', ({detail: {page}}) => {
  if (page !== 'products') return;
  // Pagination
  renderProductPagination(0);
});

function renderProductPagination(total) {
  const el = document.getElementById('prod-pagination');
  if (el) el.innerHTML = '';
}

async function searchProducts(val) {
  _productSearch = val;
  const data = await loadProducts(1, val);
  const container = document.getElementById('products-container');
  if (container) container.innerHTML = renderProductRows(data.products || []);
}

function filterProducts(filter) {
  _productFilter = filter;
  document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  loadProducts(1, _productSearch, filter).then(data => {
    const container = document.getElementById('products-container');
    if (container) container.innerHTML = renderProductRows(data.products || []);
  });
}

function setView(view) {
  // Toggle grid/list view
  const container = document.getElementById('products-container');
  if (!container) return;
  if (view === 'grid') {
    container.className = 'product-grid-view px-16';
    container.innerHTML = renderProductGrid(_products);
  } else {
    container.className = 'product-list-view';
    container.innerHTML = renderProductRows(_products);
  }
}

function renderProductGrid(products) {
  if (!products.length) return '<div class="empty"><div class="empty-text">Hakuna bidhaa</div></div>';
  return products.map(p => `
  <div class="product-card" onclick="showProductDetail('${p.id}')">
    <div class="product-card-img">
      ${p.images && p.images[0] ? `<img src="${p.images[0]}">` : '<span>&#128230;</span>'}
    </div>
    <div class="product-card-body">
      <div class="product-card-name">${p.name}</div>
      <div class="product-card-price">${fmtCurrency(p.selling_price)}</div>
      <div class="product-card-stock flex items-center gap-6">
        <span class="stock-dot ${p.stock_quantity===0?'stock-out':p.is_low_stock?'stock-low':'stock-ok'}"></span>
        <span>${p.stock_quantity} ${p.unit||'pcs'}</span>
      </div>
    </div>
  </div>`).join('');
}

function showProductDetail(id) {
  const product = _products.find(p => p.id === id);
  if (!product) return;
  const role = State.business?.role || 'staff';
  const canEdit = ['owner','manager'].includes(role);
  const canAdjust = canEdit || (State.business?.permissions?.can_adjust_stock);

  Sheet.show(product.name, `
    <div class="flex gap-14 mb-16 items-start">
      <div style="width:72px;height:72px;border-radius:12px;background:var(--bg-card2);display:flex;align-items:center;justify-content:center;font-size:32px;overflow:hidden;flex-shrink:0">
        ${product.images?.[0] ? `<img src="${product.images[0]}" style="width:100%;height:100%;object-fit:cover">` : '&#128230;'}
      </div>
      <div style="flex:1">
        <div style="font-size:16px;font-weight:700;margin-bottom:6px">${product.name}</div>
        <div class="flex gap-8 flex-wrap">
          ${statusBadge(product.stock_quantity===0?'out_of_stock':product.is_low_stock?'low_stock':'in_stock')}
          ${product.category ? `<span class="badge badge-muted">${product.category}</span>` : ''}
        </div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
      <div style="background:var(--bg-card2);border-radius:10px;padding:12px">
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">Bei ya Kuuza</div>
        <div style="font-size:18px;font-weight:800;color:var(--accent)">${fmtCurrency(product.selling_price)}</div>
      </div>
      ${product.cost_price ? `
      <div style="background:var(--bg-card2);border-radius:10px;padding:12px">
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">Gharama</div>
        <div style="font-size:18px;font-weight:800">${fmtCurrency(product.cost_price)}</div>
      </div>` : ''}
      <div style="background:var(--bg-card2);border-radius:10px;padding:12px">
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">Stoo</div>
        <div style="font-size:18px;font-weight:800;color:${product.stock_quantity===0?'var(--danger)':product.is_low_stock?'var(--warning)':'var(--success)'}">${product.stock_quantity} ${product.unit||'pcs'}</div>
      </div>
      ${product.cost_price && product.selling_price ? `
      <div style="background:var(--bg-card2);border-radius:10px;padding:12px">
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">Faida</div>
        <div style="font-size:18px;font-weight:800;color:var(--success)">${fmtCurrency(product.selling_price - product.cost_price)}</div>
      </div>` : ''}
    </div>
    ${product.description ? `<p style="font-size:13px;color:var(--text-dim);margin-bottom:16px">${product.description}</p>` : ''}
    ${product.barcode ? `<div style="font-size:12px;color:var(--text-muted)">Barcode: <span class="bold">${product.barcode}</span></div>` : ''}`,

    `<div class="flex gap-10 flex-wrap">
      <button class="btn btn-primary btn-sm" onclick="Sheet.hide();Router.go('pos')">+ Uza</button>
      ${canAdjust ? `<button class="btn btn-ghost btn-sm" onclick="showAdjustStock('${product.id}','${product.name}',${product.stock_quantity})">Rekebisha Stoo</button>` : ''}
      ${canEdit ? `<button class="btn btn-ghost btn-sm" onclick="showEditProduct('${product.id}')">Hariri</button>` : ''}
    </div>`
  );
}

function showAddProduct() {
  Sheet.show('Ongeza Bidhaa', `
    <div class="form-group">
      <label class="form-label">Jina la Bidhaa *</label>
      <input id="ap-name" type="text" placeholder="Mfano: Sukari KG">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Bei ya Kuuza *</label>
        <input id="ap-price" type="number" inputmode="decimal" placeholder="0">
      </div>
      <div class="form-group">
        <label class="form-label">Gharama ya Kununua</label>
        <input id="ap-cost" type="number" inputmode="decimal" placeholder="0">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Stoo ya Awali</label>
        <input id="ap-stock" type="number" inputmode="numeric" placeholder="0" value="0">
      </div>
      <div class="form-group">
        <label class="form-label">Kiasi Kidogo (Alert)</label>
        <input id="ap-low" type="number" inputmode="numeric" placeholder="10" value="10">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Kategoria</label>
        <input id="ap-cat" type="text" placeholder="Mfano: Chakula">
      </div>
      <div class="form-group">
        <label class="form-label">Kipimo</label>
        <select id="ap-unit">
          <option value="pcs">Vipande</option>
          <option value="kg">Kilo</option>
          <option value="ltr">Lita</option>
          <option value="box">Sanduku</option>
          <option value="pkt">Pakiti</option>
        </select>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Barcode</label>
      <input id="ap-barcode" type="text" placeholder="Scan au weka manually">
    </div>
    <div class="form-group">
      <label class="form-label">Maelezo</label>
      <textarea id="ap-desc" rows="2" placeholder="Maelezo ya bidhaa..."></textarea>
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-save-product">Hifadhi Bidhaa</button>
    </div>`
  );

  document.getElementById('btn-save-product')?.addEventListener('click', async () => {
    const name = document.getElementById('ap-name')?.value.trim();
    const price = parseFloat(document.getElementById('ap-price')?.value);
    if (!name) { Toast.error('Jina la bidhaa linahitajika'); return; }
    if (!price || price <= 0) { Toast.error('Bei ya kuuza inahitajika'); return; }
    try {
      await API.createProduct({
        name,
        selling_price: price,
        cost_price: parseFloat(document.getElementById('ap-cost')?.value) || null,
        stock_quantity: parseInt(document.getElementById('ap-stock')?.value) || 0,
        low_stock_threshold: parseInt(document.getElementById('ap-low')?.value) || 10,
        category: document.getElementById('ap-cat')?.value.trim(),
        unit: document.getElementById('ap-unit')?.value,
        barcode: document.getElementById('ap-barcode')?.value.trim(),
        description: document.getElementById('ap-desc')?.value.trim(),
      });
      Toast.success('Bidhaa imeongezwa!');
      Sheet.hide();
      const data = await loadProducts();
      const container = document.getElementById('products-container');
      if (container) container.innerHTML = renderProductRows(data.products || []);
    } catch (e) { Toast.error(e.message); }
  });
}

function showAdjustStock(id, name, current) {
  Sheet.show('Rekebisha Stoo: ' + name, `
    <div style="text-align:center;margin-bottom:20px">
      <div style="font-size:14px;color:var(--text-muted)">Stoo ya Sasa</div>
      <div style="font-size:36px;font-weight:800;color:var(--brand)">${current}</div>
    </div>
    <div class="form-group">
      <label class="form-label">Badiliko (+ kuongeza, - kupunguza)</label>
      <input id="adj-qty" type="number" inputmode="numeric" placeholder="Mfano: +10 au -5">
    </div>
    <div class="form-group">
      <label class="form-label">Sababu</label>
      <select id="adj-reason">
        <option value="adjustment">Marekebisho ya kawaida</option>
        <option value="damage">Uharibifu / Upotevu</option>
        <option value="return">Bidhaa iliyorudishwa</option>
        <option value="count_correction">Marekebisho ya hesabu</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Maelezo (si lazima)</label>
      <textarea id="adj-notes" rows="2"></textarea>
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-adj-stock">Hifadhi</button>
    </div>`
  );

  document.getElementById('btn-adj-stock')?.addEventListener('click', async () => {
    const qty = parseInt(document.getElementById('adj-qty')?.value);
    if (!qty) { Toast.error('Weka kiasi cha badiliko'); return; }
    try {
      await API.adjustStock(id, {
        quantity_change: qty,
        reason: document.getElementById('adj-notes')?.value.trim() || document.getElementById('adj-reason')?.value,
      });
      Toast.success(`Stoo imebadilishwa: ${current} → ${current + qty}`);
      Sheet.hide();
      const data = await loadProducts();
      const container = document.getElementById('products-container');
      if (container) container.innerHTML = renderProductRows(data.products || []);
    } catch (e) { Toast.error(e.message); }
  });
}

async function showEditProduct(id) {
  const product = _products.find(p => p.id === id);
  if (!product) return;
  Sheet.show('Hariri: ' + product.name, `
    <div class="form-group">
      <label class="form-label">Jina *</label>
      <input id="ep-name" value="${product.name}">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Bei ya Kuuza *</label>
        <input id="ep-price" type="number" value="${product.selling_price}">
      </div>
      <div class="form-group">
        <label class="form-label">Gharama</label>
        <input id="ep-cost" type="number" value="${product.cost_price||''}">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Kategoria</label>
        <input id="ep-cat" value="${product.category||''}">
      </div>
      <div class="form-group">
        <label class="form-label">Kipimo</label>
        <input id="ep-unit" value="${product.unit||'pcs'}">
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Kiasi Kidogo (Alert)</label>
      <input id="ep-low" type="number" value="${product.low_stock_threshold||10}">
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-update-prod">Hifadhi</button>
    </div>`
  );

  document.getElementById('btn-update-prod')?.addEventListener('click', async () => {
    try {
      await API.updateProduct(id, {
        name: document.getElementById('ep-name')?.value.trim(),
        selling_price: parseFloat(document.getElementById('ep-price')?.value),
        cost_price: parseFloat(document.getElementById('ep-cost')?.value) || null,
        category: document.getElementById('ep-cat')?.value.trim(),
        unit: document.getElementById('ep-unit')?.value.trim(),
        low_stock_threshold: parseInt(document.getElementById('ep-low')?.value) || 10,
      });
      Toast.success('Bidhaa imehifadhiwa');
      Sheet.hide();
      const data = await loadProducts();
      const container = document.getElementById('products-container');
      if (container) container.innerHTML = renderProductRows(data.products || []);
    } catch (e) { Toast.error(e.message); }
  });
}

// Debounce utility
function debounce(fn, ms) {
  clearTimeout(debounce._t);
  debounce._t = setTimeout(fn, ms);
}
