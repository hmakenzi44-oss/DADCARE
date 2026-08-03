'use strict';

let _posProducts = [];
let _cart = [];
let _posCustomer = null;

Router.register('pos', async () => {
  try {
    const data = await API.getProducts({per_page: 200});
    _posProducts = data.products || [];
  } catch (e) { _posProducts = []; }
  _cart = State.cart || [];
  return renderPOS();
});

function renderPOS() {
  const cartCount = _cart.reduce((s, i) => s + i.quantity, 0);
  const cartTotal = _cart.reduce((s, i) => s + (i.unit_price * i.quantity) - (i.discount || 0), 0);

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('dashboard')">&#8592;</button>
    <span class="topbar-title">Uuzaji Mpya</span>
    <button class="topbar-action" style="position:relative" onclick="showCart()">
      &#128717;
      ${cartCount > 0 ? `<span class="nav-badge">${cartCount}</span>` : ''}
    </button>
  </div>
  <div class="page" style="padding-bottom:140px">
    <!-- SEARCH -->
    <div class="search-wrap">
      <div class="search-bar">
        <input id="pos-search" type="search" placeholder="Tafuta bidhaa au scan barcode..."
          oninput="filterPOSProducts(this.value)">
      </div>
    </div>

    <!-- MINI CART SUMMARY -->
    ${_cart.length > 0 ? `
    <div onclick="showCart()" style="margin:0 16px 12px;background:var(--brand-glow);border:1.5px solid var(--brand);border-radius:12px;padding:14px 16px;display:flex;align-items:center;gap:12px;cursor:pointer">
      <div style="flex:1">
        <div style="font-size:13px;font-weight:700;color:var(--brand)">${cartCount} bidhaa kwenye kikapu</div>
        <div style="font-size:12px;color:var(--text-dim);margin-top:2px">Jumla: ${fmtCurrency(cartTotal)}</div>
      </div>
      <button class="btn btn-accent btn-sm" onclick="event.stopPropagation();showCheckout()">Lipa &#8250;</button>
    </div>` : ''}

    <!-- PRODUCTS GRID -->
    <div id="pos-product-container" class="product-grid" style="padding-bottom:8px">
      ${renderPOSGrid(_posProducts)}
    </div>
  </div>

  ${_cart.length > 0 ? `
  <div style="position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:480px;padding:12px 16px;background:rgba(19,22,41,0.97);backdrop-filter:blur(20px);border-top:1px solid var(--border);z-index:200">
    <button class="btn btn-accent btn-block" style="padding:16px;font-size:16px" onclick="showCheckout()">
      Lipa ${fmtCurrency(cartTotal)} &#8250;
    </button>
  </div>` : ''}`;
}

function renderPOSGrid(products) {
  if (!products.length) return '<div class="empty" style="grid-column:1/-1"><div class="empty-text">Hakuna bidhaa</div></div>';
  return products.map(p => {
    const inCart = _cart.find(i => i.product_id === p.id);
    const outOfStock = p.stock_quantity === 0;
    return `
    <div class="product-card ${outOfStock ? 'opacity-50' : ''}" onclick="${outOfStock ? '' : `addToCart('${p.id}')`}" style="${outOfStock ? 'opacity:0.5;pointer-events:none' : ''}">
      <div class="product-card-img">
        ${p.images?.[0] ? `<img src="${p.images[0]}">` : '<span>&#128230;</span>'}
        ${inCart ? `<div style="position:absolute;top:6px;right:6px;background:var(--brand);color:#fff;border-radius:10px;padding:2px 8px;font-size:11px;font-weight:700">x${inCart.quantity}</div>` : ''}
      </div>
      <div class="product-card-body">
        <div class="product-card-name">${p.name}</div>
        <div class="product-card-price">${fmtCurrency(p.selling_price)}</div>
        <div class="product-card-stock">
          <span class="stock-dot ${p.stock_quantity===0?'stock-out':p.is_low_stock?'stock-low':'stock-ok'}"></span>
          ${p.stock_quantity} ${p.unit||'pcs'}
        </div>
      </div>
    </div>`;
  }).join('');
}

function addToCart(productId) {
  const product = _posProducts.find(p => p.id === productId);
  if (!product) return;
  const existing = _cart.find(i => i.product_id === productId);
  if (existing) {
    if (existing.quantity >= product.stock_quantity) {
      Toast.warning('Stoo haitoshi');
      return;
    }
    existing.quantity++;
  } else {
    _cart.push({
      product_id: productId,
      product_name: product.name,
      quantity: 1,
      unit_price: product.selling_price,
      stock: product.stock_quantity,
      discount: 0,
    });
  }
  State.cart = _cart;
  Toast.info(product.name + ' imeongezwa');
  // Re-render grid to update cart badges
  const container = document.getElementById('pos-product-container');
  if (container) container.innerHTML = renderPOSGrid(
    document.getElementById('pos-search')?.value
      ? _posProducts.filter(p => p.name.toLowerCase().includes(document.getElementById('pos-search').value.toLowerCase()))
      : _posProducts
  );
  // Update cart summary
  const cartCount = _cart.reduce((s, i) => s + i.quantity, 0);
  const cartTotal = _cart.reduce((s, i) => s + (i.unit_price * i.quantity), 0);
  // Simple re-render of summary area
  updateCartSummary(cartCount, cartTotal);
}

function updateCartSummary(count, total) {
  // Update cart badge on topbar
  const badge = document.querySelector('.topbar-action .nav-badge');
  if (badge) badge.textContent = count;
  else if (count > 0) {
    const btn = document.querySelectorAll('.topbar-action')[1];
    if (btn) btn.innerHTML = `&#128717;<span class="nav-badge">${count}</span>`;
  }
}

function filterPOSProducts(search) {
  const filtered = search
    ? _posProducts.filter(p =>
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        (p.barcode && p.barcode.includes(search))
      )
    : _posProducts;
  const container = document.getElementById('pos-product-container');
  if (container) container.innerHTML = renderPOSGrid(filtered);
}

function showCart() {
  if (!_cart.length) { Toast.info('Kikapu kiko tupu'); return; }
  const cartTotal = _cart.reduce((s, i) => s + (i.unit_price * i.quantity) - (i.discount || 0), 0);

  const rows = _cart.map((item, idx) => `
  <div class="cart-item">
    <div style="flex:1;min-width:0">
      <div class="cart-item-name truncate">${item.product_name}</div>
      <div class="cart-item-price">${fmtCurrency(item.unit_price)} x ${item.quantity}</div>
    </div>
    <div class="qty-control">
      <button class="qty-btn" onclick="changeQty(${idx},-1)">−</button>
      <span class="qty-val">${item.quantity}</span>
      <button class="qty-btn" onclick="changeQty(${idx},1)">+</button>
    </div>
    <div class="cart-item-total">${fmtCurrency(item.unit_price * item.quantity)}</div>
    <button onclick="removeFromCart(${idx})" style="color:var(--danger);font-size:18px;margin-left:8px">&#10005;</button>
  </div>`).join('');

  Sheet.show('Kikapu', `
    <div id="cart-rows">${rows}</div>
    <div class="divider"></div>
    <div class="receipt-total">
      <span>Jumla</span>
      <span>${fmtCurrency(cartTotal)}</span>
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost" onclick="clearCart()">Futa Zote</button>
      <button class="btn btn-accent flex-1" style="font-size:16px" onclick="Sheet.hide();showCheckout()">
        Lipa ${fmtCurrency(cartTotal)} &#8250;
      </button>
    </div>`
  );
}

function changeQty(idx, delta) {
  const item = _cart[idx];
  if (!item) return;
  const newQty = item.quantity + delta;
  if (newQty <= 0) {
    _cart.splice(idx, 1);
  } else if (newQty > item.stock) {
    Toast.warning('Stoo haitoshi');
    return;
  } else {
    item.quantity = newQty;
  }
  State.cart = _cart;
  // Re-render cart
  showCart();
}

function removeFromCart(idx) {
  _cart.splice(idx, 1);
  State.cart = _cart;
  if (_cart.length === 0) { Sheet.hide(); return; }
  showCart();
}

function clearCart() {
  _cart = [];
  State.cart = [];
  Sheet.hide();
  Router.go('pos');
}

function showCheckout() {
  if (!_cart.length) { Toast.error('Kikapu kiko tupu'); return; }
  const subtotal = _cart.reduce((s, i) => s + (i.unit_price * i.quantity), 0);

  const paymentMethods = [
    {id:'cash', label:'Pesa Taslimu', icon:'💵'},
    {id:'mpesa', label:'M-Pesa', icon:'📱'},
    {id:'tigopesa', label:'Tigo Pesa', icon:'📱'},
    {id:'airtelmoney', label:'Airtel', icon:'📱'},
    {id:'bank_transfer', label:'Benki', icon:'🏦'},
    {id:'credit', label:'Mkopo', icon:'📝'},
  ];

  let selectedPayment = 'cash';

  Sheet.show('Lipa', `
    <div class="mb-16">
      ${_cart.map(i => `
      <div class="receipt-row">
        <span>${i.product_name} x${i.quantity}</span>
        <span class="bold">${fmtCurrency(i.unit_price * i.quantity)}</span>
      </div>`).join('')}
      <div class="receipt-divider"></div>
      <div class="receipt-total">
        <span>Jumla</span>
        <span id="checkout-total">${fmtCurrency(subtotal)}</span>
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Punguzo</label>
      <input id="checkout-discount" type="number" inputmode="decimal" placeholder="0" value="0"
        oninput="updateCheckoutTotal(${subtotal},this.value)">
    </div>

    <div class="form-group">
      <label class="form-label">Njia ya Malipo</label>
      <div class="payment-grid" id="payment-grid">
        ${paymentMethods.map(m => `
        <button class="payment-btn ${m.id==='cash'?'selected':''}" data-method="${m.id}" onclick="selectPayment('${m.id}')">
          <span class="payment-icon">${m.icon}</span>
          <span>${m.label}</span>
        </button>`).join('')}
      </div>
    </div>

    <div id="payment-ref-group" class="form-group hidden">
      <label class="form-label">Nambari ya Malipo (Ref)</label>
      <input id="checkout-ref" type="text" placeholder="Nambari ya muamala">
    </div>

    <div class="form-group">
      <label class="form-label">Mteja (si lazima)</label>
      <input id="checkout-customer" type="text" placeholder="Tafuta jina au simu..." oninput="searchCheckoutCustomer(this.value)">
      <div id="customer-suggestions" style="display:none"></div>
    </div>
    <input type="hidden" id="selected-customer-id" value="">

    <div class="form-group">
      <label class="form-label">Maelezo</label>
      <textarea id="checkout-notes" rows="2" placeholder="Maelezo ya ziada..."></textarea>
    </div>`,

    `<div class="flex gap-10">
      <button class="btn btn-ghost" onclick="Sheet.hide()">Rudi</button>
      <button class="btn btn-accent flex-1" style="font-size:16px" id="btn-confirm-sale">
        Thibitisha Mauzo
      </button>
    </div>`
  );

  document.getElementById('btn-confirm-sale')?.addEventListener('click', confirmSale);
}

function updateCheckoutTotal(subtotal, discount) {
  const disc = parseFloat(discount) || 0;
  const total = Math.max(0, subtotal - disc);
  const el = document.getElementById('checkout-total');
  if (el) el.textContent = fmtCurrency(total);
}

function selectPayment(method) {
  document.querySelectorAll('.payment-btn').forEach(b => b.classList.remove('selected'));
  document.querySelector(`[data-method="${method}"]`)?.classList.add('selected');
  const refGroup = document.getElementById('payment-ref-group');
  if (refGroup) refGroup.classList.toggle('hidden', method === 'cash');
}

async function searchCheckoutCustomer(query) {
  if (query.length < 2) {
    document.getElementById('customer-suggestions').style.display = 'none';
    return;
  }
  try {
    const data = await API.getCustomers({search: query});
    const suggestions = document.getElementById('customer-suggestions');
    if (!suggestions) return;
    if (!data.customers?.length) { suggestions.style.display = 'none'; return; }
    suggestions.style.display = 'block';
    suggestions.style.cssText = 'border:1px solid var(--border);border-radius:8px;background:var(--bg-card);margin-top:4px;max-height:160px;overflow-y:auto';
    suggestions.innerHTML = data.customers.map(c => `
      <div onclick="selectCheckoutCustomer('${c.id}','${c.name}')"
        style="padding:10px 14px;cursor:pointer;border-bottom:1px solid var(--border);font-size:13px">
        <div class="bold">${c.name}</div>
        <div style="color:var(--text-muted);font-size:11px">${c.phone||''}</div>
      </div>`).join('');
  } catch (e) {}
}

function selectCheckoutCustomer(id, name) {
  document.getElementById('checkout-customer').value = name;
  document.getElementById('selected-customer-id').value = id;
  document.getElementById('customer-suggestions').style.display = 'none';
}

async function confirmSale() {
  const btn = document.getElementById('btn-confirm-sale');
  if (btn) { btn.disabled = true; btn.textContent = 'Inaprocess...'; }

  const selectedMethod = document.querySelector('.payment-btn.selected')?.dataset.method || 'cash';
  const discount = parseFloat(document.getElementById('checkout-discount')?.value) || 0;
  const notes = document.getElementById('checkout-notes')?.value.trim();
  const ref = document.getElementById('checkout-ref')?.value.trim();
  const customerId = document.getElementById('selected-customer-id')?.value;

  try {
    const result = await API.processSale({
      items: _cart.map(i => ({
        product_id: i.product_id,
        quantity: i.quantity,
        unit_price: i.unit_price,
        discount: i.discount || 0,
      })),
      payment_method: selectedMethod,
      payment_reference: ref,
      discount,
      customer_id: customerId || null,
      notes,
    });

    _cart = [];
    State.cart = [];
    Sheet.hide();
    Toast.success('Mauzo yamekamilika!');
    Router.go('receipt', {sale_id: result.sale_id});
  } catch (e) {
    Toast.error(e.message);
    if (btn) { btn.disabled = false; btn.textContent = 'Thibitisha Mauzo'; }
  }
}
