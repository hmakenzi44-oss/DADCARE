'use strict';

Router.register('receipt', async (params) => {
  const { sale_id } = params;
  if (!sale_id) { Router.go('sales'); return ''; }
  let sale, items, shop;
  try {
    const data = await API.getSale(sale_id);
    sale = data.sale; items = data.items || []; shop = data.shop || {};
  } catch (e) { return `<div class="empty"><div class="empty-text">${e.message}</div></div>`; }

  const shopName = shop.shop_name || State.business?.tenant_name || 'DADCARE';
  const currency = shop.currency || State.currency || 'TZS';

  const waText = encodeURIComponent(
    `*${shopName}*\n` +
    `Risiti: ${sale.sale_number}\n` +
    `Tarehe: ${fmtDateTime(sale.created_at)}\n` +
    `─────────────────\n` +
    items.map(i => `${i.product_name} x${i.quantity} = ${fmtCurrency(i.total_price, currency)}`).join('\n') +
    `\n─────────────────\n` +
    (sale.discount > 0 ? `Punguzo: -${fmtCurrency(sale.discount, currency)}\n` : '') +
    `*JUMLA: ${fmtCurrency(sale.total, currency)}*\n` +
    `Malipo: ${sale.payment_method}\n` +
    (shop.receipt_footer ? `\n${shop.receipt_footer}` : '')
  );
  const waLink = shop.whatsapp
    ? `https://wa.me/${shop.whatsapp.replace(/\D/g,'')}?text=${waText}` : null;

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('dashboard')">&#127968;</button>
    <span class="topbar-title">Risiti</span>
    ${waLink ? `<a href="${waLink}" target="_blank" class="topbar-action" style="color:#25D366">&#128172;</a>` : ''}
  </div>
  <div class="page">
    <div class="receipt" style="margin:16px">
      <div class="receipt-head">
        <div class="receipt-head-name">${shopName}</div>
        <div class="receipt-head-sub">${sale.sale_number} • ${fmtDateTime(sale.created_at)}</div>
        ${sale.status === 'voided' ? '<div style="background:var(--danger);color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;display:inline-block;margin-top:6px">IMEBATILISHWA</div>' : ''}
      </div>
      <div class="receipt-body">
        ${items.map(i => `
        <div class="receipt-row">
          <div>
            <div style="font-size:13px">${i.product_name}</div>
            <div style="font-size:11px;color:var(--text-muted)">${i.quantity} × ${fmtCurrency(i.unit_price, currency)}</div>
          </div>
          <div style="font-weight:700">${fmtCurrency(i.total_price, currency)}</div>
        </div>`).join('')}
        <div class="receipt-divider"></div>
        ${sale.discount > 0 ? `<div class="receipt-row"><span>Punguzo</span><span style="color:var(--success)">- ${fmtCurrency(sale.discount, currency)}</span></div>` : ''}
        ${sale.tax > 0 ? `<div class="receipt-row"><span>Kodi</span><span>${fmtCurrency(sale.tax, currency)}</span></div>` : ''}
        <div class="receipt-total">
          <span>JUMLA</span>
          <span>${fmtCurrency(sale.total, currency)}</span>
        </div>
        <div class="receipt-row" style="margin-top:8px">
          <span style="color:var(--text-muted)">Njia ya Malipo</span>
          <span style="font-weight:600">${sale.payment_method}</span>
        </div>
        ${shop.receipt_footer ? `<div style="text-align:center;margin-top:12px;font-size:12px;color:var(--text-muted)">${shop.receipt_footer}</div>` : ''}
      </div>
    </div>

    <div style="padding:0 16px;display:flex;flex-direction:column;gap:12px;margin-top:8px">
      ${waLink ? `<a href="${waLink}" target="_blank" class="btn btn-whatsapp"><span>&#128172;</span> Shiriki WhatsApp</a>` : ''}
      ${sale.status === 'completed' ? `<button class="btn btn-ghost" onclick="showVoidSale('${sale.sale_id||sale_id}','${sale.sale_number}')">Batilisha Mauzo</button>` : ''}
      <button class="btn btn-primary" onclick="Router.go('pos')">+ Uuzaji Mpya</button>
    </div>
  </div>`;
});

Router.register('sales', async () => {
  let data = {sales: [], total: 0};
  try { data = await API.getSales({page: 1}); } catch (e) {}

  const rows = data.sales?.length
    ? data.sales.map(s => `
    <div class="list-item" onclick="Router.go('receipt',{sale_id:'${s.id}'})">
      <div class="list-item-icon ${s.status==='voided'?'danger':'success'}">
        ${s.status==='voided' ? '&#10005;' : '&#128176;'}
      </div>
      <div class="list-item-body">
        <div class="list-item-title">${s.sale_number}</div>
        <div class="list-item-sub">${fmtDateTime(s.created_at)} • ${s.payment_method}</div>
      </div>
      <div class="list-item-right">
        <div class="list-item-value ${s.status==='voided'?'text-muted':'text-accent'}">${fmtCurrency(s.total)}</div>
        <div class="list-item-meta">${statusBadge(s.status)}</div>
      </div>
    </div>`)
    .join('')
    : '<div class="empty"><div class="empty-icon">&#128176;</div><div class="empty-text">Hakuna mauzo bado</div></div>';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('dashboard')">&#8592;</button>
    <span class="topbar-title">Historia ya Mauzo</span>
    <button class="topbar-action" onclick="showSalesFilter()">&#128269;</button>
  </div>
  <div class="page">
    <div class="card mx-16 mt-16">
      <div id="sales-list">${rows}</div>
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
    <button class="nav-item active" data-page="sales"><span class="nav-icon">&#128176;</span><span>Mauzo</span></button>
    <button class="nav-item" onclick="Router.go('more')"><span class="nav-icon">&#8942;</span><span>Zaidi</span></button>
  </div>`;
});

function showVoidSale(saleId, saleNumber) {
  Sheet.show('Batilisha Mauzo', `
    <div class="alert alert-danger mb-16">Kumbuka: Stoo itarudishwa moja kwa moja.</div>
    <div class="form-group">
      <label class="form-label">Sababu ya Kubatilisha *</label>
      <textarea id="void-reason" rows="3" placeholder="Eleza sababu ya kubatilisha..."></textarea>
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-danger flex-1" id="btn-void">Batilisha</button>
    </div>`
  );
  document.getElementById('btn-void')?.addEventListener('click', async () => {
    const reason = document.getElementById('void-reason')?.value.trim();
    if (!reason) { Toast.error('Sababu inahitajika'); return; }
    try {
      await API.voidSale(saleId, {reason});
      Toast.warning(`Mauzo ${saleNumber} yamebatilishwa`);
      Sheet.hide();
      Router.go('sales');
    } catch (e) { Toast.error(e.message); }
  });
}

function showSalesFilter() {
  Sheet.show('Chuja Mauzo', `
    <div class="form-group">
      <label class="form-label">Kutoka</label>
      <input id="sf-from" type="date">
    </div>
    <div class="form-group">
      <label class="form-label">Hadi</label>
      <input id="sf-to" type="date">
    </div>
    <div class="form-group">
      <label class="form-label">Hali</label>
      <select id="sf-status">
        <option value="">Zote</option>
        <option value="completed">Zilizokamilika</option>
        <option value="voided">Zilizobatilishwa</option>
      </select>
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-apply-filter">Chuja</button>
    </div>`
  );
  document.getElementById('btn-apply-filter')?.addEventListener('click', async () => {
    const params = {};
    const from = document.getElementById('sf-from')?.value;
    const to = document.getElementById('sf-to')?.value;
    const status = document.getElementById('sf-status')?.value;
    if (from) params.from = from;
    if (to) params.to = to;
    if (status) params.status = status;
    try {
      const data = await API.getSales(params);
      const list = document.getElementById('sales-list');
      if (list) {
        list.innerHTML = data.sales?.length
          ? data.sales.map(s => `
          <div class="list-item" onclick="Router.go('receipt',{sale_id:'${s.id}'})">
            <div class="list-item-icon ${s.status==='voided'?'danger':'success'}">${s.status==='voided'?'✕':'₂'}</div>
            <div class="list-item-body">
              <div class="list-item-title">${s.sale_number}</div>
              <div class="list-item-sub">${fmtDateTime(s.created_at)}</div>
            </div>
            <div class="list-item-right">
              <div class="list-item-value text-accent">${fmtCurrency(s.total)}</div>
              <div>${statusBadge(s.status)}</div>
            </div>
          </div>`).join('')
          : '<div class="empty"><div class="empty-text">Hakuna mauzo</div></div>';
      }
      Sheet.hide();
    } catch (e) { Toast.error(e.message); }
  });
}
