'use strict';

Router.register('staff', async () => {
  let members = [];
  try {
    const data = await API.getMembers();
    members = data.members || [];
  } catch (e) {}

  const role = State.business?.role;
  const isOwner = role === 'owner';

  const rows = members.length
    ? members.map(m => `
    <div class="list-item" onclick="${isOwner ? `showMemberDetail(${JSON.stringify(m).replace(/"/g,'&quot;')})` : ''}">
      <div class="biz-avatar" style="width:44px;height:44px;border-radius:10px">
        ${m.name.charAt(0).toUpperCase()}
      </div>
      <div class="list-item-body">
        <div class="list-item-title">${m.name}</div>
        <div class="list-item-sub">${m.email} ${!m.is_active ? '• Amefutwa' : ''}</div>
      </div>
      <div class="list-item-right">
        ${statusBadge(m.role)}
        ${!m.is_active ? '<div class="text-xs text-muted mt-4">Amefutwa</div>' : ''}
      </div>
    </div>`).join('')
    : '<div class="empty"><div class="empty-icon">&#128101;</div><div class="empty-text">Hakuna wafanyakazi wengine</div></div>';

  return `
  <div class="topbar">
    <button class="topbar-back" onclick="Router.go('more')">&#8592;</button>
    <span class="topbar-title">Wafanyakazi</span>
    ${isOwner ? '<button class="topbar-action text-brand" onclick="showInviteStaff()">+</button>' : ''}
  </div>
  <div class="page">
    ${isOwner ? `
    <div class="section">
      <button class="btn btn-primary btn-block" onclick="showInviteStaff()">
        + Mwaliko Mfanyakazi Mpya
      </button>
    </div>` : ''}
    <div class="card mx-16">${rows}</div>
  </div>`;
});

function showInviteStaff() {
  const permissions = [
    {key:'can_change_prices', label:'Kubadilisha Bei'},
    {key:'can_give_discounts', label:'Kutoa Punguzo'},
    {key:'can_void_sales', label:'Kubatilisha Mauzo'},
    {key:'can_view_profit', label:'Kuona Faida'},
    {key:'can_adjust_stock', label:'Kurekebisha Stoo'},
    {key:'can_view_financial_reports', label:'Kuona Ripoti za Fedha'},
    {key:'can_approve_orders', label:'Kuthibitisha Maagizo'},
  ];

  Sheet.show('Mwaliko Mfanyakazi', `
    <div class="form-group">
      <label class="form-label">Jukumu</label>
      <select id="inv-role">
        <option value="manager">Meneja</option>
        <option value="cashier">Mhesabu</option>
        <option value="staff">Mfanyakazi</option>
        <option value="viewer">Mtazamaji tu</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Matumizi Maalum (si lazima)</label>
      ${permissions.map(p => `
      <div class="permission-row">
        <div>
          <div class="permission-label">${p.label}</div>
        </div>
        <div class="toggle" id="perm-${p.key}" onclick="togglePermission('${p.key}')"></div>
      </div>`).join('')}
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-create-invite">Tengeneza Mwaliko</button>
    </div>`
  );

  document.getElementById('btn-create-invite')?.addEventListener('click', async () => {
    const role = document.getElementById('inv-role')?.value;
    const perms = {};
    document.querySelectorAll('.toggle.on').forEach(t => {
      const key = t.id.replace('perm-', '');
      perms[key] = true;
    });
    try {
      const data = await API.createInvite({role, custom_permissions: perms});
      Sheet.hide();
      showInviteCode(data.invite.code, data.invite.role, data.invite.expires_at);
    } catch (e) { Toast.error(e.message); }
  });
}

function togglePermission(key) {
  const el = document.getElementById('perm-' + key);
  if (el) el.classList.toggle('on');
}

function showInviteCode(code, role, expiresAt) {
  Sheet.show('Nambari ya Mwaliko', `
    <div class="text-center" style="padding:24px 0">
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px">Shiriki nambari hii na mfanyakazi wako:</div>
      <div style="font-size:36px;font-weight:900;letter-spacing:0.15em;color:var(--brand);background:var(--brand-glow);padding:20px;border-radius:12px;margin-bottom:16px">${code}</div>
      <div style="font-size:13px;color:var(--text-muted)">Jukumu: ${statusBadge(role)}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:8px">Inaisha: ${fmtDate(expiresAt)}</div>
    </div>`,
    `<div class="flex gap-10">
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Funga</button>
      <button class="btn btn-primary flex-1" onclick="copyInviteCode('${code}')">Nakili Nambari</button>
    </div>`
  );
}

function copyInviteCode(code) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(code).then(() => Toast.success('Nambari imenakiliwa!'));
  } else {
    const el = document.createElement('input');
    el.value = code;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    Toast.success('Nambari imenakiliwa!');
  }
}

function showMemberDetail(member) {
  const permissions = [
    {key:'can_change_prices', label:'Kubadilisha Bei'},
    {key:'can_give_discounts', label:'Kutoa Punguzo'},
    {key:'can_void_sales', label:'Kubatilisha Mauzo'},
    {key:'can_view_profit', label:'Kuona Faida'},
    {key:'can_adjust_stock', label:'Kurekebisha Stoo'},
    {key:'can_view_financial_reports', label:'Kuona Ripoti za Fedha'},
    {key:'can_approve_orders', label:'Kuthibitisha Maagizo'},
  ];

  Sheet.show(member.name, `
    <div class="flex items-center gap-14 mb-20">
      <div class="biz-avatar" style="width:56px;height:56px;border-radius:50%">${member.name.charAt(0)}</div>
      <div>
        <div style="font-size:16px;font-weight:700">${member.name}</div>
        <div style="font-size:13px;color:var(--text-muted)">${member.email}</div>
        <div style="margin-top:6px">${statusBadge(member.role)}</div>
      </div>
    </div>
    ${member.role !== 'owner' ? `
    <div class="form-label mb-8">Ruhusa</div>
    ${permissions.map(p => `
    <div class="permission-row">
      <div class="permission-label">${p.label}</div>
      <div class="toggle ${member.permissions?.[p.key] ? 'on' : ''}" id="eperm-${p.key}" onclick="toggleEditPermission('${p.key}')"></div>
    </div>`).join('')}` : '<div class="alert alert-info">Mmiliki ana ruhusa zote</div>'}`,

    member.role !== 'owner' ? `
    <div class="flex gap-10">
      <button class="btn btn-danger" onclick="confirmRemoveMember('${member.id}','${member.name}')">Ondoa</button>
      <button class="btn btn-ghost flex-1" onclick="Sheet.hide()">Ghairi</button>
      <button class="btn btn-primary flex-1" id="btn-update-perms">Hifadhi Ruhusa</button>
    </div>` : `<button class="btn btn-ghost btn-block" onclick="Sheet.hide()">Funga</button>`
  );

  document.getElementById('btn-update-perms')?.addEventListener('click', async () => {
    const perms = {};
    document.querySelectorAll('[id^="eperm-"]').forEach(el => {
      const key = el.id.replace('eperm-', '');
      perms[key] = el.classList.contains('on');
    });
    try {
      await API.updatePermissions(member.id, {custom_permissions: perms});
      Toast.success('Ruhusa zimehifadhiwa');
      Sheet.hide();
    } catch (e) { Toast.error(e.message); }
  });
}

function toggleEditPermission(key) {
  const el = document.getElementById('eperm-' + key);
  if (el) el.classList.toggle('on');
}

async function confirmRemoveMember(id, name) {
  const confirmed = await Confirm(`Una uhakika unataka kumfuta "${name}" kutoka biashara hii?`, 'Ondoa Mfanyakazi');
  if (!confirmed) return;
  try {
    await API.removeMember(id);
    Toast.warning(name + ' ameondolewa');
    Sheet.hide();
    Router.go('staff');
  } catch (e) { Toast.error(e.message); }
}
