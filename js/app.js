/**
 * SupermarketIQ — Global Retail Intelligence Platform
 * Professional SaaS Dashboard Frontend Logic
 */

// ===== State =====
const state = {
    data: [],
    filtered: [],
    currentView: 'dashboard',
    sortField: null,
    sortDir: 'asc',
    currentPage: 1,
    pageSize: 15,
    theme: localStorage.getItem('theme') || 'light',
};

// ===== Spider definitions (for automation status page) =====
const SPIDERS = [
    { name: 'walmart', label: 'Walmart', country: 'United States', status: 'success', lastRun: '2026-09-01 02:15', records: 1, duration: '12s' },
    { name: 'costco', label: 'Costco', country: 'United States', status: 'success', lastRun: '2026-09-01 02:16', records: 1, duration: '8s' },
    { name: 'carrefour', label: 'Carrefour', country: 'France', status: 'success', lastRun: '2026-09-01 02:17', records: 2, duration: '15s' },
    { name: 'tesco', label: 'Tesco', country: 'United Kingdom', status: 'success', lastRun: '2026-09-01 02:18', records: 2, duration: '11s' },
    { name: 'aldi', label: 'Aldi', country: 'Germany', status: 'success', lastRun: '2026-09-01 02:19', records: 1, duration: '9s' },
    { name: 'auto_discover', label: 'Auto Discover', country: 'Global', status: 'running', lastRun: '进行中', records: '—', duration: '—' },
    { name: 'data_manager', label: 'Data Manager', country: '—', status: 'idle', lastRun: '2026-09-01 02:20', records: 25, duration: '3s' },
];

// ===== Init =====
document.addEventListener('DOMContentLoaded', () => {
    applyTheme();
    bindEvents();
    loadData();
});

function bindEvents() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(item.dataset.view);
        });
    });
    document.querySelectorAll('[data-view]').forEach(el => {
        if (!el.classList.contains('nav-item')) {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                switchView(el.dataset.view);
            });
        }
    });

    // Sidebar toggle
    document.getElementById('sidebarToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
    });

    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);

    // Global search
    document.getElementById('globalSearch').addEventListener('input', debounce(handleGlobalSearch, 250));

    // Filters
    document.getElementById('filterCountry').addEventListener('change', applyTableFilters);
    document.getElementById('filterQuality').addEventListener('change', applyTableFilters);
    document.getElementById('filterContact').addEventListener('change', applyTableFilters);

    // Table sorting
    document.querySelectorAll('.data-table th[data-sort]').forEach(th => {
        th.addEventListener('click', () => handleSort(th.dataset.sort));
    });

    // Buttons
    document.getElementById('refreshBtn').addEventListener('click', loadData);
    document.getElementById('exportBtn').addEventListener('click', exportCSV);

    // Drawer
    document.getElementById('drawerClose').addEventListener('click', closeDrawer);
    document.getElementById('drawerOverlay').addEventListener('click', closeDrawer);

    // Keyboard
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeDrawer();
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('globalSearch').focus();
        }
    });
}

// ===== Data Loading =====
async function loadData() {
    try {
        const resp = await fetch('data/clients.json', { cache: 'no-cache' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        state.data = await resp.json();
        state.filtered = [...state.data];

        document.getElementById('navCount').textContent = state.data.length;
        document.getElementById('lastRunTime').textContent = state.data[0]?.scraped_at
            ? new Date(state.data[0].scraped_at).toLocaleDateString('zh-CN')
            : '—';

        renderDashboard();
        renderTable();
        renderSpiders();
        renderQuality();
        populateCountryFilter();

        showToast('数据加载完成', 'success');
    } catch (err) {
        console.error('加载失败:', err);
        showToast('数据加载失败: ' + err.message, 'error');
    }
}

// ===== View Switching =====
function switchView(view) {
    state.currentView = view;
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === view);
    });
    document.querySelectorAll('.view').forEach(v => {
        v.classList.toggle('active', v.id === `view-${view}`);
    });
    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('mobile-open');
}

// ===== Theme =====
function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
}
function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', state.theme);
    applyTheme();
    showToast(`已切换到${state.theme === 'dark' ? '深色' : '浅色'}模式`);
}

// ===== Dashboard Rendering =====
function renderDashboard() {
    const data = state.data;
    const total = data.length;
    const countries = new Set(data.map(d => d.country).filter(Boolean)).size;
    const emailCount = data.filter(d => d.email).length;
    const phoneCount = data.filter(d => d.phone).length;
    const linkedinCount = data.filter(d => d.linkedin).length;
    const avgQuality = Math.round(data.reduce((s, d) => s + (d.data_quality || 0), 0) / total);

    animateNumber('kpiTotal', total);
    animateNumber('kpiCountries', countries);
    document.getElementById('kpiEmail').textContent = Math.round(emailCount / total * 100) + '%';
    document.getElementById('kpiEmailCount').textContent = emailCount + ' 个邮箱';
    document.getElementById('kpiPhone').textContent = Math.round(phoneCount / total * 100) + '%';
    document.getElementById('kpiPhoneCount').textContent = phoneCount + ' 个电话';
    document.getElementById('kpiLinkedin').textContent = Math.round(linkedinCount / total * 100) + '%';
    document.getElementById('kpiLinkedinCount').textContent = linkedinCount + ' 个主页';
    animateNumber('kpiQuality', avgQuality);

    renderCountryChart();
    renderCoverageChart();
    renderRecentList();
    updatePipelineTimes();
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const duration = 500;
    const startTime = performance.now();
    function update(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(target * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function renderCountryChart() {
    const counts = {};
    state.data.forEach(d => { counts[d.country || 'Unknown'] = (counts[d.country || 'Unknown'] || 0) + 1; });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const max = sorted[0]?.[1] || 1;

    const html = '<div class="bar-chart">' + sorted.map(([country, count]) => `
        <div class="bar-row">
            <span class="bar-label" title="${esc(country)}">${esc(country)}</span>
            <div class="bar-track">
                <div class="bar-fill" style="width:${count / max * 100}%">
                    <span class="bar-value">${count}</span>
                </div>
            </div>
        </div>
    `).join('') + '</div>';
    document.getElementById('countryChart').innerHTML = html;
}

function renderCoverageChart() {
    const fields = [
        { name: '邮箱', key: 'email', color: '#8b5cf6' },
        { name: '电话', key: 'phone', color: '#f97316' },
        { name: 'LinkedIn', key: 'linkedin', color: '#06b6d4' },
        { name: '官网', key: 'website', color: '#3b82f6' },
        { name: '地址', key: 'address', color: '#10b981' },
        { name: 'WhatsApp', key: 'whatsapp', color: '#25d366' },
        { name: '微信', key: 'wechat', color: '#07c160' },
    ];
    const total = state.data.length;
    const html = '<div class="coverage-list">' + fields.map(f => {
        const count = state.data.filter(d => d[f.key]).length;
        const pct = Math.round(count / total * 100);
        return `<div class="coverage-item">
            <div class="coverage-header">
                <span class="coverage-name">${f.name}</span>
                <span class="coverage-pct">${pct}%</span>
            </div>
            <div class="coverage-track">
                <div class="coverage-fill" style="width:${pct}%;background:${f.color}"></div>
            </div>
        </div>`;
    }).join('') + '</div>';
    document.getElementById('coverageChart').innerHTML = html;
}

function renderRecentList() {
    const recent = [...state.data].sort((a, b) =>
        new Date(b.scraped_at || 0) - new Date(a.scraped_at || 0)
    ).slice(0, 6);

    const html = recent.map(d => {
        const q = d.data_quality || 0;
        const qClass = q >= 80 ? 'quality-high' : q >= 60 ? 'quality-mid' : 'quality-low';
        const initials = (d.company_name || '?').substring(0, 2).toUpperCase();
        return `<div class="recent-item" onclick="openDrawer('${esc(d.company_name)}')">
            <div class="recent-avatar">${esc(initials)}</div>
            <div class="recent-info">
                <div class="recent-name">${esc(d.company_name)}</div>
                <div class="recent-meta">${esc(d.country || '')} · ${esc(d.city || '')}</div>
            </div>
            <span class="recent-quality ${qClass}">${q}</span>
        </div>`;
    }).join('');
    document.getElementById('recentList').innerHTML = html;
}

function updatePipelineTimes() {
    const t = state.data[0]?.scraped_at;
    if (t) {
        const d = new Date(t);
        const timeStr = d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
        ['pipeDiscoverTime', 'pipeScrapeTime', 'pipeCleanTime', 'pipeValidateTime'].forEach(id => {
            document.getElementById(id).textContent = timeStr;
        });
    }
}

// ===== Data Table =====
function populateCountryFilter() {
    const select = document.getElementById('filterCountry');
    const countries = [...new Set(state.data.map(d => d.country).filter(Boolean))].sort();
    select.innerHTML = '<option value="">全部国家</option>' +
        countries.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('');
}

function handleGlobalSearch(e) {
    const keyword = e.target.value.trim().toLowerCase();
    if (state.currentView !== 'contacts') switchView('contacts');

    if (!keyword) {
        state.filtered = [...state.data];
    } else {
        state.filtered = state.data.filter(d => {
            return [d.company_name, d.country, d.city, d.email, d.phone, d.address]
                .filter(Boolean).join(' ').toLowerCase().includes(keyword);
        });
    }
    state.currentPage = 1;
    renderTable();
}

function applyTableFilters() {
    const country = document.getElementById('filterCountry').value;
    const minQuality = parseInt(document.getElementById('filterQuality').value) || 0;
    const contact = document.getElementById('filterContact').value;
    const keyword = document.getElementById('globalSearch').value.trim().toLowerCase();

    state.filtered = state.data.filter(d => {
        if (keyword && ![d.company_name, d.country, d.city, d.email, d.phone].filter(Boolean).join(' ').toLowerCase().includes(keyword)) return false;
        if (country && d.country !== country) return false;
        if (minQuality && (d.data_quality || 0) < minQuality) return false;
        if (contact && !d[contact]) return false;
        return true;
    });
    state.currentPage = 1;
    renderTable();
}

function handleSort(field) {
    if (state.sortField === field) {
        state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortField = field;
        state.sortDir = 'asc';
    }
    state.filtered.sort((a, b) => {
        let va = a[field] || '', vb = b[field] || '';
        if (typeof va === 'number') return state.sortDir === 'asc' ? va - vb : vb - va;
        return state.sortDir === 'asc' ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
    renderTable();
}

function renderTable() {
    const data = state.filtered;
    const total = data.length;
    const totalPages = Math.ceil(total / state.pageSize);
    const start = (state.currentPage - 1) * state.pageSize;
    const pageData = data.slice(start, start + state.pageSize);

    document.getElementById('contactsSubtitle').textContent = `共 ${total} 家企业`;

    const tbody = document.getElementById('tableBody');
    if (pageData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-tertiary)">未找到匹配的企业</td></tr>`;
    } else {
        tbody.innerHTML = pageData.map(d => {
            const q = d.data_quality || 0;
            const qClass = q >= 80 ? 'quality-high' : q >= 60 ? 'quality-mid' : 'quality-low';
            return `<tr onclick="openDrawer('${esc(d.company_name)}')">
                <td><span class="table-cell-name">${esc(d.company_name)}</span></td>
                <td>${esc(d.country || '—')}</td>
                <td>${esc(d.city || '—')}</td>
                <td>${d.email ? `<span class="table-cell-email">${esc(d.email)}</span>` : '<span style="color:var(--text-tertiary)">—</span>'}</td>
                <td>${d.phone ? `<span class="table-cell-phone">${esc(d.phone)}</span>` : '<span style="color:var(--text-tertiary)">—</span>'}</td>
                <td>${d.linkedin ? `<a href="${esc(d.linkedin)}" target="_blank" class="table-cell-link" onclick="event.stopPropagation()">LinkedIn ↗</a>` : '<span style="color:var(--text-tertiary)">—</span>'}</td>
                <td><span class="quality-badge ${qClass}">${q}</span></td>
                <td><button class="page-btn" onclick="event.stopPropagation();openDrawer('${esc(d.company_name)}')">详情</button></td>
            </tr>`;
        }).join('');
    }

    document.getElementById('tableInfo').textContent =
        total === 0 ? '显示 0 条' : `显示 ${start + 1}-${Math.min(start + state.pageSize, total)} / ${total} 条`;

    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    const container = document.getElementById('pagination');
    if (totalPages <= 1) { container.innerHTML = ''; return; }

    let html = `<button class="page-btn" ${state.currentPage === 1 ? 'disabled' : ''} onclick="goPage(${state.currentPage - 1})">‹</button>`;
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || Math.abs(i - state.currentPage) <= 1) {
            html += `<button class="page-btn ${i === state.currentPage ? 'active' : ''}" onclick="goPage(${i})">${i}</button>`;
        } else if (Math.abs(i - state.currentPage) === 2) {
            html += `<span style="padding:0 4px;color:var(--text-tertiary)">…</span>`;
        }
    }
    html += `<button class="page-btn" ${state.currentPage === totalPages ? 'disabled' : ''} onclick="goPage(${state.currentPage + 1})">›</button>`;
    container.innerHTML = html;
}

function goPage(page) {
    state.currentPage = page;
    renderTable();
}

// ===== Spider Status Page =====
function renderSpiders() {
    const html = SPIDERS.map(s => `
        <div class="spider-card">
            <div class="spider-header">
                <div>
                    <div class="spider-name">${esc(s.label)}</div>
                    <div class="spider-country">${esc(s.country)}</div>
                </div>
                <span class="spider-status ${s.status}">${s.status === 'success' ? '成功' : s.status === 'running' ? '运行中' : '待命'}</span>
            </div>
            <div class="spider-meta">
                <div class="spider-meta-item">
                    <span class="spider-meta-label">最近运行</span>
                    <span class="spider-meta-value">${esc(s.lastRun)}</span>
                </div>
                <div class="spider-meta-item">
                    <span class="spider-meta-label">抓取记录</span>
                    <span class="spider-meta-value">${s.records}</span>
                </div>
                <div class="spider-meta-item">
                    <span class="spider-meta-label">耗时</span>
                    <span class="spider-meta-value">${esc(s.duration)}</span>
                </div>
                <div class="spider-meta-item">
                    <span class="spider-meta-label">爬虫 ID</span>
                    <span class="spider-meta-value">${esc(s.name)}</span>
                </div>
            </div>
        </div>
    `).join('');
    document.getElementById('spiderGrid').innerHTML = html;
}

// ===== Quality Page =====
function renderQuality() {
    const fields = [
        { name: '企业名称', key: 'company_name', icon: '🏢', color: '#4f46e5' },
        { name: '国家/地区', key: 'country', icon: '🌍', color: '#10b981' },
        { name: '城市', key: 'city', icon: '🏙️', color: '#3b82f6' },
        { name: '地址', key: 'address', icon: '📍', color: '#f97316' },
        { name: '官网', key: 'website', icon: '🌐', color: '#8b5cf6' },
        { name: '邮箱', key: 'email', icon: '📧', color: '#ec4899' },
        { name: '电话', key: 'phone', icon: '📞', color: '#06b6d4' },
        { name: 'WhatsApp', key: 'whatsapp', icon: '💬', color: '#25d366' },
        { name: '微信', key: 'wechat', icon: '💚', color: '#07c160' },
        { name: 'LinkedIn', key: 'linkedin', icon: '💼', color: '#0077b5' },
    ];
    const total = state.data.length;
    const html = fields.map(f => {
        const count = state.data.filter(d => d[f.key]).length;
        const pct = Math.round(count / total * 100);
        return `<div class="quality-card">
            <div class="quality-card-header">
                <span class="quality-card-title">${f.icon} ${f.name}</span>
                <span class="quality-card-pct">${pct}%</span>
            </div>
            <div class="quality-bar">
                <div class="quality-bar-fill" style="width:${pct}%;background:${f.color}"></div>
            </div>
            <div class="quality-detail">${count} / ${total} 条记录已填充</div>
        </div>`;
    }).join('');
    document.getElementById('qualityGrid').innerHTML = html;
}

// ===== Detail Drawer =====
function openDrawer(companyName) {
    const d = state.data.find(x => x.company_name === companyName);
    if (!d) return;

    document.getElementById('drawerTitle').textContent = d.company_name;
    const q = d.data_quality || 0;

    const rows = [
        { icon: '🌐', label: '官网', value: d.website, href: d.website },
        { icon: '📧', label: '邮箱', value: d.email, href: d.email ? `mailto:${d.email}` : '' },
        { icon: '📞', label: '电话', value: d.phone, href: d.phone ? `tel:${d.phone}` : '' },
        { icon: '💬', label: 'WhatsApp', value: d.whatsapp, href: d.whatsapp ? `https://wa.me/${String(d.whatsapp).replace(/[^\d]/g, '')}` : '' },
        { icon: '💚', label: '微信', value: d.wechat },
        { icon: '💼', label: 'LinkedIn', value: d.linkedin, href: d.linkedin },
        { icon: '📘', label: 'Facebook', value: d.facebook, href: d.facebook },
        { icon: '🐦', label: 'Twitter/X', value: d.twitter, href: d.twitter },
        { icon: '📷', label: 'Instagram', value: d.instagram, href: d.instagram },
        { icon: '▶️', label: 'YouTube', value: d.youtube, href: d.youtube },
    ];

    const contactHtml = rows.map(r => `
        <div class="drawer-row">
            <div class="drawer-row-icon">${r.icon}</div>
            <div class="drawer-row-content">
                <div class="drawer-row-label">${r.label}</div>
                <div class="drawer-row-value ${r.value ? '' : 'missing'}">
                    ${r.value ? (r.href ? `<a href="${esc(r.href)}" target="_blank">${esc(r.value)}</a>` : esc(r.value)) : '待补充'}
                </div>
            </div>
            ${r.value ? `<button class="drawer-copy" onclick="copyText('${esc(r.value).replace(/'/g, "\\'")}')">复制</button>` : ''}
        </div>
    `).join('');

    document.getElementById('drawerBody').innerHTML = `
        <div class="drawer-quality" style="--score:${q}%">
            <div class="drawer-quality-score"><span>${q}</span></div>
            <div class="drawer-quality-info">
                <h4>数据质量评分</h4>
                <p>${q >= 80 ? '高质量数据，联系方式完整' : q >= 60 ? '中等质量，部分字段待补充' : '基础数据，建议手动完善'}</p>
            </div>
        </div>
        <div class="drawer-section">
            <h4>企业信息</h4>
            <div class="drawer-row"><div class="drawer-row-icon">🏢</div><div class="drawer-row-content"><div class="drawer-row-label">公司名称</div><div class="drawer-row-value">${esc(d.company_name)}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">🌍</div><div class="drawer-row-content"><div class="drawer-row-label">国家/地区</div><div class="drawer-row-value">${esc(d.country || '—')}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">🏙️</div><div class="drawer-row-content"><div class="drawer-row-label">城市</div><div class="drawer-row-value">${esc(d.city || '—')}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">📍</div><div class="drawer-row-content"><div class="drawer-row-label">地址</div><div class="drawer-row-value">${esc(d.address || '—')}</div></div></div>
        </div>
        <div class="drawer-section">
            <h4>联系方式</h4>
            ${contactHtml}
        </div>
        <div class="drawer-section">
            <h4>数据元信息</h4>
            <div class="drawer-row"><div class="drawer-row-icon">🔗</div><div class="drawer-row-content"><div class="drawer-row-label">来源页面</div><div class="drawer-row-value">${d.source_url ? `<a href="${esc(d.source_url)}" target="_blank">${esc(d.source_url)}</a>` : '—'}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">🕐</div><div class="drawer-row-content"><div class="drawer-row-label">抓取时间</div><div class="drawer-row-value">${d.scraped_at ? new Date(d.scraped_at).toLocaleString('zh-CN') : '—'}</div></div></div>
        </div>
    `;

    document.getElementById('detailDrawer').classList.add('active');
    document.getElementById('drawerOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeDrawer() {
    document.getElementById('detailDrawer').classList.remove('active');
    document.getElementById('drawerOverlay').classList.remove('active');
    document.body.style.overflow = '';
}

// ===== Utilities =====
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => showToast('复制失败', 'error'));
}

function showToast(message, type = '') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; setTimeout(() => toast.remove(), 300); }, 2500);
}

function exportCSV() {
    const headers = ['company_name', 'country', 'city', 'address', 'website', 'email', 'phone', 'whatsapp', 'wechat', 'linkedin', 'facebook', 'twitter', 'instagram', 'youtube', 'data_quality'];
    const csv = [headers.join(',')].concat(
        state.data.map(row => headers.map(h => `"${(row[h] || '').toString().replace(/"/g, '""')}"`).join(','))
    ).join('\n');

    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `supermarket-contacts-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV 导出成功', 'success');
}

function esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function debounce(fn, delay) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// Expose to global
window.openDrawer = openDrawer;
window.closeDrawer = closeDrawer;
window.goPage = goPage;
window.copyText = copyText;
