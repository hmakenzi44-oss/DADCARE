'use strict';

// ── WELCOME PAGE ───────────────────────────────────────────
Router.register('welcome', () => `
<div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px 24px;gap:32px">
  <div style="text-align:center">
    <div style="font-size:52px;font-weight:900;background:linear-gradient(135deg,var(--brand),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-0.04em;margin-bottom:8px">DADCARE</div>
    <p style="font-size:15px;color:var(--text-dim)">Mfumo wa Biashara wa Afrika ya Mashariki</p>
  </div>
  <div style="display:flex;flex-direction:column;gap:14px;width:100%;max-width:340px">
    <button class="btn btn-primary" style="padding:18px;font-size:16px" onclick="Router.go('login')">
      Ingia Akaunti
    </button>
    <button class="btn btn-ghost" style="padding:18px;font-size:16px" onclick="Router.go('register')">
      Jisajili Bure
    </button>
    <button class="btn btn-ghost btn-sm" onclick="Router.go('marketplace-browse')">
      Tazama Soko la DADCARE
    </button>
  </div>
  <p style="font-size:11px;color:var(--text-muted);text-align:center">
    Majaribio ya bure siku 90. Hakuna kadi ya benki.
  </p>
</div>`);

// ── LOGIN PAGE ─────────────────────────────────────────────
Router.register('login', () => `
<div style="min-height:100vh;display:flex;flex-direction:column;padding:0">
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('welcome')">&#8592;</button>
    <span class="topbar-title">Ingia</span>
  </div>
  <div class="form-section" style="padding-top:32px;flex:1">
    <div class="form-group">
      <label class="form-label">Barua Pepe</label>
      <input id="l-email" type="email" inputmode="email" autocomplete="email" placeholder="wewe@mfano.com">
    </div>
    <div class="form-group">
      <label class="form-label">Nywila</label>
      <div class="input-group">
        <input id="l-pass" type="password" autocomplete="current-password" placeholder="Nywila yako">
        <span class="input-group-icon" onclick="togglePass('l-pass')" style="pointer-events:all;cursor:pointer">&#128065;</span>
      </div>
    </div>
    <button class="btn btn-primary btn-block mt-24" id="btn-login" style="padding:15px">Ingia</button>
    <div class="divider-text mt-20">au</div>
    <p class="text-center mt-16" style="font-size:14px;color:var(--text-dim)">
      Huna akaunti? 
      <button style="color:var(--brand);font-weight:700;font-size:14px" onclick="Router.go('register')">Jisajili</button>
    </p>
  </div>
</div>`);

document.addEventListener('page:ready', ({detail: {page}}) => {
  if (page === 'login') {
    const btn = document.getElementById('btn-login');
    const doLogin = async () => {
      const email = document.getElementById('l-email')?.value.trim();
      const password = document.getElementById('l-pass')?.value;
      if (!email || !password) { Toast.error('Jaza barua pepe na nywila'); return; }
      btn.disabled = true;
      btn.textContent = 'Inaingia...';
      try {
        const data = await API.login({email, password});
        State.user = data.user;
        State.lang = data.user?.language || 'sw';
        Toast.success('Karibu ' + data.user.full_name);
        if (data.businesses?.length > 0) {
          Router.go('businesses');
        } else {
          Router.go('create-business');
        }
      } catch (e) {
        Toast.error(e.message);
        btn.disabled = false;
        btn.textContent = 'Ingia';
      }
    };
    btn?.addEventListener('click', doLogin);
    document.getElementById('l-pass')?.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
  }
});

// ── REGISTER PAGE ──────────────────────────────────────────
Router.register('register', () => `
<div style="min-height:100vh;display:flex;flex-direction:column">
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('welcome')">&#8592;</button>
    <span class="topbar-title">Jisajili</span>
  </div>
  <div class="form-section" style="padding-top:24px;flex:1">
    <div class="form-group">
      <label class="form-label">Jina Kamili</label>
      <input id="r-name" type="text" autocomplete="name" placeholder="Jina lako kamili">
    </div>
    <div class="form-group">
      <label class="form-label">Barua Pepe</label>
      <input id="r-email" type="email" inputmode="email" autocomplete="email" placeholder="wewe@mfano.com">
    </div>
    <div class="form-group">
      <label class="form-label">Nywila</label>
      <div class="input-group">
        <input id="r-pass" type="password" autocomplete="new-password" placeholder="Angalau herufi 8">
        <span class="input-group-icon" onclick="togglePass('r-pass')" style="pointer-events:all;cursor:pointer">&#128065;</span>
      </div>
      <div class="form-hint">Angalau herufi 8</div>
    </div>
    <div class="form-group">
      <label class="form-label">Lugha</label>
      <select id="r-lang">
        <option value="sw">Kiswahili</option>
        <option value="en">English</option>
      </select>
    </div>
    <button class="btn btn-primary btn-block mt-16" id="btn-register" style="padding:15px">Jisajili Bure</button>
    <p class="text-center mt-16" style="font-size:14px;color:var(--text-dim)">
      Una akaunti? 
      <button style="color:var(--brand);font-weight:700;font-size:14px" onclick="Router.go('login')">Ingia</button>
    </p>
    <p class="text-center mt-12 text-xs text-muted">Majaribio ya bure siku 90. Hakuna malipo.</p>
  </div>
</div>`);

document.addEventListener('page:ready', ({detail: {page}}) => {
  if (page === 'register') {
    document.getElementById('btn-register')?.addEventListener('click', async () => {
      const name = document.getElementById('r-name')?.value.trim();
      const email = document.getElementById('r-email')?.value.trim();
      const password = document.getElementById('r-pass')?.value;
      const language = document.getElementById('r-lang')?.value || 'sw';
      if (!name || !email || !password) { Toast.error('Jaza sehemu zote'); return; }
      if (password.length < 8) { Toast.error('Nywila lazima iwe herufi 8+'); return; }
      try {
        const data = await API.register({full_name: name, email, password, language});
        State.user = data.user;
        State.lang = language;
        Toast.success('Akaunti imeundwa!');
        Router.go('create-business');
      } catch (e) { Toast.error(e.message); }
    });
  }
});

// ── BUSINESS SELECTOR ──────────────────────────────────────
Router.register('businesses', async () => {
  let businesses = [];
  try {
    const data = await API.getProfile();
    State.user = data.user;
    businesses = data.businesses || [];
  } catch (e) {
    Router.go('login');
    return '';
  }

  const cards = businesses.length ? businesses.map(b => {
    const initial = b.name.charAt(0).toUpperCase();
    const isActive = State.business?.tenant_id === b.id;
    return `
    <div class="biz-card ${isActive ? 'active' : ''}" data-biz-id="${b.id}" style="margin-bottom:12px">
      <div class="biz-avatar">${b.logo_url ? `<img src="${b.logo_url}">` : initial}</div>
      <div style="flex:1;min-width:0">
        <div class="biz-name truncate">${b.name}</div>
        <div class="biz-meta">${statusBadge(b.role)} ${statusBadge(b.subscription_status)}</div>
      </div>
      ${isActive ? '<span style="font-size:20px;color:var(--brand)">&#10003;</span>' : '<span style="font-size:18px;color:var(--text-muted)">&#8250;</span>'}
    </div>`;
  }).join('') : `<div class="empty"><div class="empty-icon">&#127978;</div><div class="empty-text">Huna biashara bado</div></div>`;

  return `
  <div style="min-height:100vh;display:flex;flex-direction:column">
    <div class="topbar">
      <div class="topbar-logo">DADCARE</div>
      <span class="topbar-title" style="font-size:14px">Biashara Zangu</span>
      <button class="topbar-action" onclick="doLogout()" title="Toka">&#9873;</button>
    </div>
    <div class="form-section" style="padding-top:24px;flex:1">
      <p class="text-dim text-sm mb-16">Chagua biashara au unda mpya:</p>
      <div id="biz-list">${cards}</div>
      <div style="display:flex;flex-direction:column;gap:12px;margin-top:24px">
        <button class="btn btn-primary btn-block" style="padding:14px" onclick="Router.go('create-business')">
          + Unda Biashara Mpya
        </button>
        <button class="btn btn-ghost btn-block" onclick="showJoinBusiness()">
          &#128279; Jiunge na Biashara
        </button>
      </div>
    </div>
  </div>`;
});

document.addEventListener('page:ready', ({detail: {page}}) => {
  if (page === 'businesses') {
    document.querySelectorAll('[data-biz-id]').forEach(card => {
      card.onclick = () => selectBusiness(card.dataset.bizId);
    });
  }
});

async function selectBusiness(tenantId) {
  try {
    const data = await API.selectBusiness(tenantId);
    State.business = data.business;
    Toast.success(data.business.name);
    // Fetch shop settings for currency
    try {
      const settings = await API.getSettings();
      State.currency = settings.currency || 'TZS';
    } catch (e) {}
    setTimeout(() => Router.go('dashboard'), 400);
  } catch (e) {
    Toast.error(e.message);
  }
}

function showJoinBusiness() {
  Sheet.show('Jiunge na Biashara', `
    <div class="form-group">
      <label class="form-label">Nambari ya Mwaliko</label>
      <input id="join-code" type="text" style="text-transform:uppercase;letter-spacing:0.1em;font-size:18px;text-align:center" placeholder="XXXXXXXXXX" maxlength="10">
      <div class="form-hint">Omba nambari kutoka kwa mmiliki wa biashara</div>
    </div>`,
    `<button class="btn btn-primary btn-block" id="btn-join">Jiunge</button>`
  );
  document.getElementById('btn-join')?.addEventListener('click', async () => {
    const code = document.getElementById('join-code')?.value.trim().toUpperCase();
    if (!code) { Toast.error('Weka nambari ya mwaliko'); return; }
    try {
      const data = await API.joinBusiness(code);
      Toast.success('Umejiunga na ' + data.business.name);
      Sheet.hide();
      Router.go('businesses');
    } catch (e) { Toast.error(e.message); }
  });
}

// ── CREATE BUSINESS ────────────────────────────────────────
Router.register('create-business', () => `
<div style="min-height:100vh;display:flex;flex-direction:column">
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('businesses')">&#8592;</button>
    <span class="topbar-title">Unda Biashara</span>
  </div>
  <div class="form-section" style="padding-top:24px;flex:1">
    <div class="alert alert-info mb-16">Majaribio ya bure siku 90. Hakuna malipo ya awali.</div>
    <div class="form-group">
      <label class="form-label">Jina la Biashara *</label>
      <input id="cb-name" type="text" placeholder="Mfano: Duka la Hojey">
    </div>
    <div class="form-group">
      <label class="form-label">Mji</label>
      <input id="cb-city" type="text" placeholder="Dar es Salaam">
    </div>
    <div class="form-group">
      <label class="form-label">Namba ya WhatsApp</label>
      <input id="cb-wa" type="tel" inputmode="tel" placeholder="+255...">
    </div>
    <div class="form-group">
      <label class="form-label">Namba ya Simu</label>
      <input id="cb-phone" type="tel" inputmode="tel" placeholder="+255...">
    </div>
    <button class="btn btn-primary btn-block mt-20" id="btn-create-biz" style="padding:15px">
      Unda Biashara
    </button>
  </div>
</div>`);

document.addEventListener('page:ready', ({detail: {page}}) => {
  if (page === 'create-business') {
    document.getElementById('btn-create-biz')?.addEventListener('click', async () => {
      const name = document.getElementById('cb-name')?.value.trim();
      if (!name) { Toast.error('Jina la biashara linahitajika'); return; }
      try {
        const data = await API.createBusiness({
          name,
          mini_app_slug: 'shop',
          city: document.getElementById('cb-city')?.value.trim(),
          whatsapp: document.getElementById('cb-wa')?.value.trim(),
          phone: document.getElementById('cb-phone')?.value.trim(),
        });
        Toast.success('Biashara imeundwa!');
        // Auto-select the new business
        await selectBusiness(data.business.id);
      } catch (e) { Toast.error(e.message); }
    });
  }
});

// ── HELPERS ────────────────────────────────────────────────
function togglePass(id) {
  const inp = document.getElementById(id);
  if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
}

async function doLogout() {
  try { await API.logout(); } catch (e) {}
  State.user = null;
  State.business = null;
  State.cart = [];
  Router.go('welcome');
}
