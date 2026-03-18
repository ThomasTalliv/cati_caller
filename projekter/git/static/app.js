/* James PM — Shared utilities */

// ─── Toast ──────────────────────────────────────────────────────────────────

function showToast(msg, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = (type === 'success' ? '✓ ' : '✗ ') + msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ─── API helpers ─────────────────────────────────────────────────────────────

async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

const GET  = (p)    => api('GET', p);
const PUT  = (p, b) => api('PUT', p, b);
const POST = (p, b) => api('POST', p, b);

// ─── Deadline badge ───────────────────────────────────────────────────────────

function deadlineClass(status) {
  if (status === 'critical') return 'deadline-critical';
  if (status === 'warning')  return 'deadline-warning';
  return '';
}

function statusBadge(progress, deadlineStatus) {
  if (deadlineStatus === 'critical') return '<span class="badge badge-critical">🔴 Critical</span>';
  if (deadlineStatus === 'warning')  return '<span class="badge badge-warning">🟡 Attention</span>';
  return '<span class="badge badge-ok">🟢 On track</span>';
}

// ─── Progress bar HTML ────────────────────────────────────────────────────────

function progressBar(pct) {
  const cls = pct === 100 ? 'done' : '';
  return `
    <div class="progress-bar">
      <div class="progress-fill ${cls}" style="width:${pct}%"></div>
    </div>
    <div class="text-xs text-muted">${pct}% complete</div>`;
}

// ─── Nav active state ──────────────────────────────────────────────────────────

function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active',
      a.getAttribute('href') === path ||
      (path.startsWith('/projekt/') && a.getAttribute('href') === '/'));
  });
}

// ─── Modal helpers ─────────────────────────────────────────────────────────────

function openModal(id) {
  document.getElementById(id).classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

// Close on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// Cmd+B = brainstorm modal
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
    e.preventDefault();
    const modal = document.getElementById('brainstorm-modal');
    if (modal) {
      modal.classList.toggle('open');
      if (modal.classList.contains('open')) {
        modal.querySelector('textarea')?.focus();
      }
    }
  }
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});

// ─── Shared nav HTML ────────────────────────────────────────────────────────────

function renderNav() {
  return `
  <header class="page-header">
    <div class="container page-header-inner">
      <span class="logo">James PM</span>
      <nav class="nav-links">
        <a class="nav-link" href="/">Dashboard</a>
        <a class="nav-link" href="/gtd">GTD Board</a>
      </nav>
      <div style="flex:1"></div>
      <button class="btn btn-ghost btn-sm" onclick="openModal('brainstorm-modal')">
        + Brainstorm
        <span class="text-xs text-muted" style="margin-left:4px">⌘B</span>
      </button>
    </div>
  </header>`;
}

// ─── Brainstorm modal HTML ──────────────────────────────────────────────────────

function renderBrainstormModal(projects) {
  const options = projects.map(p =>
    `<option value="${p.id}">${p.name}</option>`
  ).join('');
  return `
  <div class="modal-overlay" id="brainstorm-modal">
    <div class="modal">
      <div class="modal-title">Brainstorm</div>
      <div style="margin-bottom:12px">
        <label class="text-xs text-muted" style="display:block;margin-bottom:6px">Projekt</label>
        <select id="bs-project">${options}</select>
      </div>
      <div style="margin-bottom:12px">
        <label class="text-xs text-muted" style="display:block;margin-bottom:6px">Idé / handling</label>
        <textarea id="bs-text" placeholder="Skriv her..."></textarea>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost btn-sm" onclick="closeModal('brainstorm-modal')">Annuller</button>
        <button class="btn btn-ghost btn-sm" onclick="saveBrainstorm('inbox')">Gem til Inbox</button>
        <button class="btn btn-primary btn-sm" onclick="saveBrainstorm('next_actions')">Gem til Next Actions</button>
      </div>
    </div>
  </div>`;
}

async function saveBrainstorm(section) {
  const projectId = document.getElementById('bs-project').value;
  const text = document.getElementById('bs-text').value.trim();
  if (!text) return;
  try {
    await POST(`/api/projects/${projectId}/inbox`, { text, section });
    showToast('Gemt');
    document.getElementById('bs-text').value = '';
    closeModal('brainstorm-modal');
  } catch (e) {
    showToast(e.message, 'error');
  }
}
