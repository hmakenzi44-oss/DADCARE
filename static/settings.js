'use strict';

Router.register('settings', async () => {
  let settings = {};
  try { settings = await API.getSettings(); } catch (e) {}

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Mipangilio</span>
  </div>
  <div class="page">
    <div class="form-section">
      <div class="section-header mb-16"><span class="section-title">Biashara Yangu</span></div>

      <div class="form-group">
        <label class="form-label">Jina la Duka</label>
        <input id="s-name" value="${settings.shop_name||''}" placeholder="Jina la duka lako">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Simu</label>
          <input id="s-phone" type="tel" value="${settings.phone||''}">
        </div>
        <div class="form-group">
          <label class="form-label">WhatsApp</label>
          <input id="s-wa" type="tel" value="${settings.whatsapp||''}">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Anwani</label>
        <textarea id="s-address" rows="2">${settings.address||''}</textarea>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Mji</label>
          <input id="s-city" value="${settings.city||''}">
        </div>
        <div class="form-group">
          <label class="form-label">Sarafu</label>
          <select id="s-currency">
            <option value="TZS" ${settings.currency==='TZS'?'selected':''}>TZS (Shilingi ya Tanzania)</option>
            <option value="ZMW" ${settings.currency==='ZMW'?'selected':''}>ZMW (Kwacha ya Zambia)</option>
            <option value="KES" ${settings.currency==='KES'?'selected':''}>KES (Shilingi ya Kenya)</option>
            <option value="USD" ${settings.currency==='USD'?'selected':''}>USD (Dola ya Amerika)</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Kodi ya Ushuru (%)</label>
          <input id="s-tax" type="number" inputmode="decimal" value="${settings.tax_rate||0}" placeholder="0">
        </div>
        <div class="form-group">
          <label class="form-label">Lugha</label>
          <select id="s-lang">
            <option value="sw" ${settings.language==='sw'?'selected':''}>Kiswahili</option>
            <option value="en" ${settings.language==='en'?'selected':''}>English</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Mwisho wa Risiti</label>
        <textarea id="s-footer" rows="2" placeholder="Mfano: Asante kwa kununua!">${settings.receipt_footer||''}</textarea>
      </div>

      <button class="btn btn-primary btn-block mt-8" id="btn-save-settings" style="padding:15px">
        Hifadhi Mipangilio
      </button>

      <div class="divider"></div>
      <div class="section-header"><span class="section-title">Akaunti</span></div>

      <button class="btn btn-ghost btn-block mb-12" onclick="showChangePassword()">
        &#128273; Badilisha Nywila
      </button>
      <button class="btn btn-ghost btn-block" style="color:var(--danger)" onclick="doLogout()">
        &#9873; Toka kwenye Akaunti
      </button>
    </div>
  </div>`;
});

document.addEventListener('page:ready', ({detail: {page}}) => {
  if (page !== 'settings') return;
  document.getElementById('btn-save-settings')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-save-settings');
    btn.disabled = true; btn.textContent = 'Inahifadhi...';
    try {
      await API.saveSettings({
        shop_name: document.getElementById('s-name')?.value.trim(),
        phone: document.getElementById('s-phone')?.value.trim(),
        whatsapp: document.getElementById('s-wa')?.value.trim(),
        address: document.getElementById('s-address')?.value.trim(),
        city: document.getElementById('s-city')?.value.trim(),
        currency: document.getElementById('s-currency')?.value,
        tax_rate: parseFloat(document.getElementById('s-tax')?.value) || 0,
        language: document.getElementById('s-lang')?.value,
        receipt_footer: document.getElementById('s-footer')?.value.trim(),
      });
      State.currency = document.getElementById('s-currency')?.value || State.currency;
      Toast.success('Mipangilio imehifadhiwa!');
    } catch (e) { Toast.error(e.message); }
    btn.disabled = false; btn.textContent = 'Hifadhi Mipangilio';
  });
});

function showChangePassword() {
  Sheet.show('Badilisha Nywila', `
    <div class="form-group">
      <label class="form-label">Nywila ya Sasa</label>
      <input id="cp-current" type="password">
    </div>
    <div class="form-group">
      <label class="form-label">Nywila Mpya</label>
      <input id="cp-new" type="password">
      <div class="form-hint">Angalau herufi 8</div>
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-change-pw">Badilisha</button>
    </div>`
  );
  document.getElementById('btn-change-pw')?.addEventListener('click', async () => {
    const current = document.getElementById('cp-current')?.value;
    const newPw = document.getElementById('cp-new')?.value;
    if (!current || !newPw) { Toast.error('Jaza sehemu zote'); return; }
    if (newPw.length < 8) { Toast.error('Nywila lazima iwe herufi 8+'); return; }
    try {
      await API.changePassword({current_password: current, new_password: newPw});
      Toast.success('Nywila imebadilishwa!');
      Sheet.hide();
    } catch (e) { Toast.error(e.message); }
  });
}

// ── PURCHASE ORDERS ───────────────────────────────────────
Router.register('purchase-orders', async () => {
  let data = {purchase_orders: []};
  try { data = await API.getPurchaseOrders(); } catch (e) {}

  const rows = data.purchase_orders?.length
    ? data.purchase_orders.map(o => `
    <div class="list-item" onclick="showPODetail('${o.id}','${o.order_number}')">
      <div class="list-item-icon warning">&#128666;</div>
      <div class="list-item-body">
        <div class="list-item-title">${o.order_number}</div>
        <div class="list-item-sub">${fmtDate(o.created_at)}</div>
      </div>
      <div class="list-item-right">
        <div class="list-item-value">${fmtCurrency(o.total)}</div>
        <div>${statusBadge(o.status)}</div>
      </div>
    </div>`)
    .join('')
    : '<div class="empty"><div class="empty-icon">&#128666;</div><div class="empty-text">Hakuna maagizo ya ununuzi</div></div>';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Maagizo ya Ununuzi</span>
    <button class="topbar-action text-brand" onclick="Router.go('new-purchase-order')">+</button>
  </div>
  <div class="page">
    <div class="card mx-16 mt-16">${rows}</div>
  </div>`;
});

// ── WHOLESALE ORDERS ──────────────────────────────────────
Router.register('wholesale-orders', async () => {
  let data = {orders: []};
  try { data = await API.getOrders({}); } catch (e) {}

  const rows = data.orders?.length
    ? data.orders.map(o => `
    <div class="list-item">
      <div class="list-item-icon brand">&#128722;</div>
      <div class="list-item-body">
        <div class="list-item-title">${o.order_number}</div>
        <div class="list-item-sub">${fmtDate(o.created_at)}</div>
      </div>
      <div class="list-item-right">
        <div class="list-item-value text-accent">${fmtCurrency(o.total)}</div>
        <div>${statusBadge(o.status)}</div>
      </div>
    </div>`)
    .join('')
    : '<div class="empty"><div class="empty-icon">&#128722;</div><div class="empty-text">Hakuna maagizo ya jumla</div></div>';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Maagizo ya Jumla</span>
    <button class="topbar-action text-brand" onclick="showCreateWholesaleOrder()">+</button>
  </div>
  <div class="page">
    <div class="card mx-16 mt-16">${rows}</div>
  </div>`;
});

// ── MY LISTINGS (Marketplace) ─────────────────────────────
Router.register('my-listings', async () => {
  let data = {listings: []};
  try { data = await API.getMyListings(); } catch (e) {}

  const rows = data.listings?.length
    ? data.listings.map(l => `
    <div class="list-item">
      <div class="list-item-icon brand" style="border-radius:10px;overflow:hidden">
        ${l.images?.[0] ? `<img src="${l.images[0]}" style="width:100%;height:100%;object-fit:cover">` : '&#127978;'}
      </div>
      <div class="list-item-body">
        <div class="list-item-title truncate">${l.title}</div>
        <div class="list-item-sub">${l.category||''} • ${l.city||''}</div>
      </div>
      <div class="list-item-right">
        ${l.price ? `<div class="list-item-value text-accent">${fmtCurrency(l.price, l.currency)}</div>` : ''}
        <div>${statusBadge(l.status)}</div>
        ${l.ai_score !== null ? `<div class="text-xs text-muted">AI: ${l.ai_score}</div>` : ''}
      </div>
    </div>`)
    .join('')
    : '<div class="empty"><div class="empty-icon">&#127978;</div><div class="empty-text">Hakuna matangazo bado</div><div class="empty-sub">Tanga bidhaa zako hadharani</div></div>';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Matangazo Yangu</span>
    <button class="topbar-action text-brand" onclick="showSubmitListing()">+</button>
  </div>
  <div class="page">
    <div class="alert alert-info mx-16 mt-16">
      Matangazo yanakaguliwa na AI. Alama &#8805;85 yanaidhinishwa moja kwa moja.
    </div>
    <div class="card mx-16">${rows}</div>
  </div>`;
});

function showSubmitListing() {
  Sheet.show('Tanga Bidhaa Sokoni', `
    <div class="form-group"><label class="form-label">Kichwa cha Tangazo *</label><input id="sl-title" type="text" placeholder="Mfano: Sukari ya Jumla Dar es Salaam"></div>
    <div class="form-group"><label class="form-label">Maelezo</label><textarea id="sl-desc" rows="3" placeholder="Eleza bidhaa au huduma yako..."></textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">Bei</label><input id="sl-price" type="number" inputmode="decimal" placeholder="0"></div>
      <div class="form-group"><label class="form-label">Sarafu</label>
        <select id="sl-currency"><option value="TZS">TZS</option><option value="USD">USD</option><option value="KES">KES</option></select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">Kategoria</label><input id="sl-cat" placeholder="Mfano: Chakula"></div>
      <div class="form-group"><label class="form-label">Mji</label><input id="sl-city" placeholder="Dar es Salaam"></div>
    </div>
    <div class="form-group"><label class="form-label">Nambari ya WhatsApp</label><input id="sl-wa" type="tel" inputmode="tel" placeholder="+255..."></div>
    <div class="form-group"><label class="form-label">Nambari ya Simu</label><input id="sl-phone" type="tel" inputmode="tel" placeholder="+255..."></div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-submit-listing">Tuma kwa AI</button>
    </div>`
  );
  document.getElementById('btn-submit-listing')?.addEventListener('click', async () => {
    const title = document.getElementById('sl-title')?.value.trim();
    if (!title) { Toast.error('Kichwa cha tangazo kinahitajika'); return; }
    try {
      const result = await API.submitListing({
        title,
        description: document.getElementById('sl-desc')?.value.trim(),
        price: parseFloat(document.getElementById('sl-price')?.value) || null,
        currency: document.getElementById('sl-currency')?.value || 'TZS',
        category: document.getElementById('sl-cat')?.value.trim(),
        city: document.getElementById('sl-city')?.value.trim(),
        contact_whatsapp: document.getElementById('sl-wa')?.value.trim(),
        contact_phone: document.getElementById('sl-phone')?.value.trim(),
      });
      Toast.success(`Tangazo limetumwa! AI Score: ${result.ai_score||'?'}`);
      Sheet.hide();
      Router.go('my-listings');
    } catch (e) { Toast.error(e.message); }
  });
}

function showCreateWholesaleOrder() {
  Sheet.show('Oda Mpya ya Jumla', `
    <div class="alert alert-info mb-16">Chagua mteja na bidhaa kwa oda ya jumla.</div>
    <div class="form-group">
      <label class="form-label">Mteja</label>
      <input id="wo-customer" type="text" placeholder="Tafuta mteja...">
    </div>
    <div class="form-group">
      <label class="form-label">Maelezo</label>
      <textarea id="wo-notes" rows="2"></textarea>
    </div>`,
    `<button class="btn btn-primary btn-block" onclick="Toast.info('Tumia POS kwa oda rahisi')">Endelea</button>`
  );
}

function showPODetail(id, number) {
  Toast.info('Maagizo ya ununuzi: ' + number);
}
