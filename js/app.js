/* ============================================
   Cyrus AI — Application Logic
   Professional CRM platform
   ============================================ */

// ===== State =====
const state = {
    data: [],
    filtered: [],
    currentPage: 1,
    pageSize: 15,
    sortField: '',
    sortDir: 'asc',
    currentView: 'dashboard',
    theme: 'light',
    charts: {},
};

const VIEW_NAMES = {
    dashboard: '仪表盘',
    contacts: '客户名录',
    discovery: '潜客挖掘',
    acquisition: '获客中心',
    facebook: 'Facebook 获客',
    automation: '爬虫监控',
    quality: '数据质量',
    settings: '设置',
};

// ===== Init =====
document.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    initPreferences();
    initDiscovery();
    initFacebook();
    loadData();
    loadFacebookData();
});

// ===== Events =====
function bindEvents() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(item.dataset.view);
        });
    });

    // Sidebar collapse (desktop)
    document.getElementById('sidebarCollapse')?.addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
        setTimeout(() => { Object.values(state.charts).forEach(c => c?.resize()); }, 250);
    });

    // Mobile menu
    document.getElementById('mobileMenuBtn')?.addEventListener('click', () => {
        document.getElementById('sidebar').classList.add('mobile-open');
        document.getElementById('sidebarMask').classList.add('active');
    });
    document.getElementById('sidebarMask')?.addEventListener('click', closeMobileSidebar);

    // Theme toggle
    document.getElementById('themeToggle')?.addEventListener('click', () => {
        const next = state.theme === 'light' ? 'dark' : 'light';
        setTheme(next);
    });

    // Global search
    document.getElementById('globalSearch')?.addEventListener('input', debounce(handleGlobalSearch, 250));

    // Table filters
    ['filterIndustry', 'filterCountry', 'filterDepartment', 'filterPosition', 'filterQuality'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', applyTableFilters);
    });

    // Table sorting
    document.querySelectorAll('.data-table th[data-sort]').forEach(th => {
        th.addEventListener('click', () => handleSort(th.dataset.sort));
    });

    // Buttons
    document.getElementById('refreshBtn')?.addEventListener('click', loadData);
    document.getElementById('exportBtn')?.addEventListener('click', exportCSV);
    document.getElementById('updateBtn')?.addEventListener('click', openUpdateModal);
    document.getElementById('confirmUpdateBtn')?.addEventListener('click', triggerUpdate);

    // Drawer
    document.getElementById('drawerClose')?.addEventListener('click', closeDrawer);
    document.getElementById('drawerOverlay')?.addEventListener('click', closeDrawer);

    // Keyboard
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { closeDrawer(); closeUpdateModal(); closeMobileSidebar(); }
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            document.getElementById('globalSearch')?.focus();
        }
    });

    // Chart link navigation
    document.querySelectorAll('.chart-link[data-view]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(link.dataset.view);
        });
    });

    // Window resize for charts
    window.addEventListener('resize', debounce(() => {
        Object.values(state.charts).forEach(c => c?.resize());
    }, 200));
}

function closeMobileSidebar() {
    document.getElementById('sidebar')?.classList.remove('mobile-open');
    document.getElementById('sidebarMask')?.classList.remove('active');
}

// ===== View Switching =====
function switchView(view) {
    state.currentView = view;
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.toggle('active', item.dataset.view === view);
    });
    document.querySelectorAll('.page').forEach(p => {
        p.classList.toggle('active', p.id === `page-${view}`);
    });
    document.getElementById('breadcrumbCurrent').textContent = VIEW_NAMES[view] || view;
    closeMobileSidebar();
    if (view === 'discovery') renderDiscovery();
    if (view === 'facebook') renderFbTable();
    if (view === 'dashboard') setTimeout(() => Object.values(state.charts).forEach(c => c?.resize()), 100);
}

// ===== Data Loading =====
async function loadData() {
    try {
        const resp = await fetch('data/clients.json', { cache: 'no-cache' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        state.data = await resp.json();
        state.filtered = [...state.data];

        document.getElementById('navCount').textContent = state.data.length;
        document.getElementById('contactsSubtitle').textContent = `共 ${state.data.length} 家企业`;

        populateFilters();
        renderDashboard();
        renderTable();
        renderSpiders();
        renderQuality();
        showLastUpdateTime();
        renderDiscovery();

    } catch (e) {
        showToast('⚠️ 数据加载失败: ' + e.message);
    }
}

// ===== Dashboard =====
function renderDashboard() {
    const data = state.data;
    const total = data.length || 1;
    const emailCount = data.filter(d => d.email || d.procurement_email).length;
    const phoneCount = data.filter(d => d.phone).length;
    const linkedinCount = data.filter(d => d.linkedin).length;

    animateNumber('kpiTotal', data.length);
    document.getElementById('kpiEmail').textContent = Math.round(emailCount / total * 100) + '%';
    document.getElementById('kpiEmailCount').textContent = emailCount + ' 个邮箱';
    document.getElementById('kpiPhone').textContent = Math.round(phoneCount / total * 100) + '%';
    document.getElementById('kpiPhoneCount').textContent = phoneCount + ' 个电话';
    document.getElementById('kpiLinkedin').textContent = Math.round(linkedinCount / total * 100) + '%';
    document.getElementById('kpiLinkedinCount').textContent = linkedinCount + ' 个主页';

    renderCountryChart();
    renderCoverageChart(emailCount, phoneCount, linkedinCount, total);
    renderIndustryChart();
    renderRecentList();
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const start = parseInt(el.textContent) || 0;
    const duration = 600;
    const startTime = performance.now();
    function update(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(start + (target - start) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ===== ECharts: Country Distribution =====
function renderCountryChart() {
    const el = document.getElementById('countryChart');
    if (!el || typeof echarts === 'undefined') return;

    if (!state.charts.country) {
        state.charts.country = echarts.init(el);
    }
    const chart = state.charts.country;

    const counts = {};
    state.data.forEach(d => {
        const c = d.country || '未知';
        counts[c] = (counts[c] || 0) + 1;
    });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10);

    const colors = ['#3b82f6', '#60a5fa', '#8b5cf6', '#a78bfa', '#10b981', '#34d399', '#f59e0b', '#fbbf24', '#ef4444', '#f87171'];

    chart.setOption({
        grid: { left: 70, right: 30, top: 10, bottom: 20 },
        xAxis: {
            type: 'value',
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
            axisLabel: { color: '#94a3b8', fontSize: 11 },
        },
        yAxis: {
            type: 'category',
            data: sorted.map(s => s[0]).reverse(),
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#475569', fontSize: 12, fontWeight: 500 },
        },
        series: [{
            type: 'bar',
            data: sorted.map((s, i) => ({
                value: s[1],
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                        { offset: 0, color: colors[i % colors.length] + '99' },
                        { offset: 1, color: colors[i % colors.length] },
                    ]),
                    borderRadius: [0, 4, 4, 0],
                },
            })).reverse(),
            barWidth: 18,
            label: {
                show: true,
                position: 'right',
                color: '#475569',
                fontSize: 12,
                fontWeight: 600,
            },
        }],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#0f172a',
            borderColor: '#1e293b',
            textStyle: { color: '#fff', fontSize: 12 },
            formatter: (params) => `${params[0].name}: <strong>${params[0].value}</strong> 家`,
        },
    });
}

// ===== ECharts: Coverage =====
function renderCoverageChart(email, phone, linkedin, total) {
    const el = document.getElementById('coverageChart');
    if (!el || typeof echarts === 'undefined') return;

    if (!state.charts.coverage) {
        state.charts.coverage = echarts.init(el);
    }
    const chart = state.charts.coverage;

    chart.setOption({
        series: [{
            type: 'gauge',
            startAngle: 200,
            endAngle: -20,
            min: 0,
            max: 100,
            splitNumber: 10,
            radius: '90%',
            center: ['50%', '58%'],
            axisLine: {
                lineStyle: {
                    width: 14,
                    color: [[0.3, '#ef4444'], [0.6, '#f59e0b'], [1, '#10b981']],
                },
            },
            pointer: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            detail: {
                valueAnimation: true,
                fontSize: 28,
                fontWeight: 800,
                color: '#0f172a',
                offsetCenter: [0, '5%'],
                formatter: '{value}%',
            },
            data: [{ value: Math.round((email + phone + linkedin) / 3 / total * 100) }],
        }],
        graphic: [
            {
                type: 'text',
                left: 'center',
                top: '72%',
                style: {
                    text: '综合覆盖率',
                    fill: '#94a3b8',
                    fontSize: 12,
                    fontWeight: 600,
                },
            },
        ],
    });
}

// ===== ECharts: Industry =====
function renderIndustryChart() {
    const el = document.getElementById('industryChart');
    if (!el || typeof echarts === 'undefined') return;

    if (!state.charts.industry) {
        state.charts.industry = echarts.init(el);
    }
    const chart = state.charts.industry;

    const counts = {};
    state.data.forEach(d => {
        const ind = d.industry || '未分类';
        counts[ind] = (counts[ind] || 0) + 1;
    });
    const data = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8);

    chart.setOption({
        tooltip: {
            trigger: 'item',
            backgroundColor: '#0f172a',
            borderColor: '#1e293b',
            textStyle: { color: '#fff', fontSize: 12 },
            formatter: '{b}: {c} 家 ({d}%)',
        },
        legend: {
            orient: 'vertical',
            right: 5,
            top: 'center',
            textStyle: { color: '#475569', fontSize: 11 },
            itemWidth: 10,
            itemHeight: 10,
        },
        series: [{
            type: 'pie',
            radius: ['45%', '70%'],
            center: ['35%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
            label: { show: false },
            data: data.map((d, i) => ({
                name: d[0],
                value: d[1],
                itemStyle: { color: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16'][i % 8] },
            })),
        }],
    });
}

// ===== Recent List =====
function renderRecentList() {
    const el = document.getElementById('recentList');
    if (!el) return;
    const sorted = [...state.data]
        .filter(d => d.scraped_at)
        .sort((a, b) => new Date(b.scraped_at) - new Date(a.scraped_at))
        .slice(0, 8);

    el.innerHTML = sorted.map(d => `
        <div class="recent-item" onclick="openDrawer('${esc(d.company_name)}')">
            <div>
                <div class="recent-name">${esc(d.company_name)}</div>
                <div class="recent-meta">${esc(d.country || '—')} · ${esc(d.industry || '—')}</div>
            </div>
            <span class="recent-badge">${d.data_quality || 0}分</span>
        </div>
    `).join('') || '<p style="color:var(--text-tertiary);font-size:13px;">暂无数据</p>';
}

// ===== Filters =====
function populateFilters() {
    const countries = [...new Set(state.data.map(d => d.country).filter(Boolean))].sort();
    const industries = [...new Set(state.data.map(d => d.industry).filter(Boolean))].sort();
    const departments = [...new Set(state.data.map(d => d.department).filter(Boolean))].sort();
    const positions = [...new Set(state.data.map(d => d.position).filter(Boolean))].sort();

    const setOpts = (id, list) => {
        const sel = document.getElementById(id);
        if (!sel) return;
        const first = sel.options[0];
        sel.innerHTML = '';
        sel.appendChild(first);
        list.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v; opt.textContent = v;
            sel.appendChild(opt);
        });
    };
    setOpts('filterCountry', countries);
    setOpts('filterIndustry', industries);
    setOpts('filterDepartment', departments);
    setOpts('filterPosition', positions);
}

function handleGlobalSearch(e) {
    state.currentPage = 1;
    applyTableFilters();
}

function applyTableFilters() {
    const industry = document.getElementById('filterIndustry')?.value || '';
    const country = document.getElementById('filterCountry')?.value || '';
    const dept = document.getElementById('filterDepartment')?.value || '';
    const pos = document.getElementById('filterPosition')?.value || '';
    const minQ = parseInt(document.getElementById('filterQuality')?.value) || 0;
    const kw = document.getElementById('globalSearch')?.value?.trim().toLowerCase() || '';

    state.filtered = state.data.filter(d => {
        if (industry && d.industry !== industry) return false;
        if (country && d.country !== country) return false;
        if (dept && d.department !== dept) return false;
        if (pos && d.position !== pos) return false;
        if ((d.data_quality || 0) < minQ) return false;
        if (kw) {
            const hay = `${d.company_name} ${d.industry} ${d.country} ${d.city} ${d.product_categories || ''}`.toLowerCase();
            if (!hay.includes(kw)) return false;
        }
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

// ===== Table =====
function renderTable() {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;
    const total = state.filtered.length;
    const totalPages = Math.ceil(total / state.pageSize);
    const start = (state.currentPage - 1) * state.pageSize;
    const pageData = state.filtered.slice(start, start + state.pageSize);

    document.getElementById('tableInfo').textContent = `显示 ${total === 0 ? 0 : start + 1}-${Math.min(start + state.pageSize, total)} / ${total} 条`;

    tbody.innerHTML = pageData.map(d => {
        const q = d.data_quality || 0;
        const qClass = q >= 80 ? 'quality-high' : q >= 60 ? 'quality-mid' : 'quality-low';
        const isHigh = isHighValuePosition(d.position);
        return `<tr onclick="openDrawer('${esc(d.company_name)}')">
            <td><span class="cell-name">${esc(d.company_name)}</span></td>
            <td>${d.industry ? `<span class="industry-tag">${esc(d.industry)}</span>` : '—'}</td>
            <td><span class="cell-country">${esc(d.country || '—')}</span></td>
            <td>${d.contact_person ? esc(d.contact_person) : '—'}</td>
            <td>${d.position ? `<span class="cell-position ${isHigh ? 'high' : ''}">${esc(d.position)}</span>` : '—'}</td>
            <td>${d.procurement_email ? `<span class="proc-email">${esc(d.procurement_email)}</span>` : (d.email ? `<span class="cell-email">${esc(d.email)}</span>` : '—')}</td>
            <td>${d.phone ? `<span class="cell-phone">${esc(d.phone)}</span>` : '—'}</td>
            <td><span class="quality-tag ${qClass}">${q}</span></td>
            <td><button class="action-btn" onclick="event.stopPropagation();openDrawer('${esc(d.company_name)}')">详情</button></td>
        </tr>`;
    }).join('') || `<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--text-tertiary);">暂无匹配数据</td></tr>`;

    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    const container = document.getElementById('pagination');
    if (!container || totalPages <= 1) { container.innerHTML = ''; return; }
    let html = `<button class="page-link" onclick="goPage(${state.currentPage - 1})" ${state.currentPage === 1 ? 'disabled' : ''}>‹</button>`;
    for (let i = 1; i <= Math.min(totalPages, 7); i++) {
        html += `<button class="page-link ${i === state.currentPage ? 'active' : ''}" onclick="goPage(${i})">${i}</button>`;
    }
    html += `<button class="page-link" onclick="goPage(${state.currentPage + 1})" ${state.currentPage === totalPages ? 'disabled' : ''}>›</button>`;
    container.innerHTML = html;
}

function goPage(page) {
    const total = Math.ceil(state.filtered.length / state.pageSize);
    if (page < 1 || page > total) return;
    state.currentPage = page;
    renderTable();
}

// ===== Spiders =====
function renderSpiders() {
    const el = document.getElementById('spiderGrid');
    if (!el) return;
    const spiders = [
        { name: '品牌官网爬虫', status: 'success', desc: '14个品牌官网联系方式抓取', time: '运行中' },
        { name: '维基百科目录', status: 'success', desc: '11个行业分类，发达国家优先', time: '运行中' },
        { name: 'EuroPages 目录', status: 'running', desc: '欧洲企业目录数据', time: '运行中' },
        { name: '联系方式提取', status: 'success', desc: '邮箱、电话、社交链接提取', time: '运行中' },
        { name: '数据清洗去重', status: 'success', desc: '标准化、去重、质量评分', time: '运行中' },
        { name: '自动部署', status: 'success', desc: 'GitHub Pages 自动发布', time: '运行中' },
    ];
    el.innerHTML = spiders.map(s => `
        <div class="spider-card">
            <div class="spider-name">${s.name}</div>
            <span class="spider-status ${s.status}">${s.status === 'success' ? '● 正常' : s.status === 'running' ? '● 运行中' : '● 失败'}</span>
            <div class="spider-meta">${s.desc}</div>
        </div>
    `).join('');
}

// ===== Quality =====
function renderQuality() {
    const el = document.getElementById('qualityGrid');
    if (!el) return;
    const fields = [
        { name: '公司名称', key: 'company_name', color: '#3b82f6' },
        { name: '国家/地区', key: 'country', color: '#8b5cf6' },
        { name: '邮箱地址', key: 'email', color: '#10b981' },
        { name: '采购邮箱', key: 'procurement_email', color: '#f59e0b' },
        { name: '联系电话', key: 'phone', color: '#ef4444' },
        { name: 'LinkedIn', key: 'linkedin', color: '#06b6d4' },
        { name: '行业分类', key: 'industry', color: '#ec4899' },
        { name: '职位信息', key: 'position', color: '#84cc16' },
    ];
    const total = state.data.length || 1;
    el.innerHTML = fields.map(f => {
        const count = state.data.filter(d => d[f.key]).length;
        const pct = Math.round(count / total * 100);
        return `<div class="quality-card">
            <div class="quality-field">${f.name}</div>
            <div class="quality-bar"><div class="quality-fill" style="width:${pct}%;background:${f.color}"></div></div>
            <div class="quality-percent">${pct}% (${count}/${total})</div>
        </div>`;
    }).join('');
}

// ===== Drawer =====
function openDrawer(companyName) {
    const d = state.data.find(x => x.company_name === companyName);
    if (!d) return;
    document.getElementById('drawerTitle').textContent = d.company_name;
    const q = d.data_quality || 0;

    const contactRows = [
        { icon: '🌐', label: '官网', value: d.website, href: d.website },
        { icon: '🛒', label: '采购部邮箱', value: d.procurement_email, href: d.procurement_email ? `mailto:${d.procurement_email}` : '', highlight: true },
        { icon: '📧', label: '公司邮箱', value: d.email, href: d.email ? `mailto:${d.email}` : '' },
        { icon: '📞', label: '电话', value: d.phone, href: d.phone ? `tel:${d.phone}` : '' },
        { icon: '💼', label: 'LinkedIn', value: d.linkedin, href: d.linkedin },
        { icon: '📘', label: 'Facebook', value: d.facebook, href: d.facebook },
        { icon: '📷', label: 'Instagram', value: d.instagram, href: d.instagram },
    ];

    const contactHtml = contactRows.map(r => `
        <div class="drawer-row">
            <div class="drawer-row-icon">${r.icon}</div>
            <div class="drawer-row-info">
                <div class="drawer-row-label">${r.label}</div>
                <div class="drawer-row-value ${r.value ? '' : 'missing'} ${r.highlight && r.value ? 'proc-email' : ''}">
                    ${r.value ? (r.href ? `<a href="${esc(r.href)}" target="_blank">${esc(r.value)}</a>` : esc(r.value)) : '待补充'}
                </div>
            </div>
            ${r.value ? `<button class="drawer-copy" onclick="copyText('${esc(r.value).replace(/'/g, "\\'")}')">复制</button>` : ''}
        </div>
    `).join('');

    const companySearch = encodeURIComponent(d.company_name);

    document.getElementById('drawerBody').innerHTML = `
        <div class="drawer-score">
            <div class="drawer-score-ring" style="--score:${q}%"><div class="drawer-score-inner">${q}</div></div>
            <div>
                <div style="font-size:14px;font-weight:700;">数据质量评分</div>
                <div style="font-size:12px;color:var(--text-tertiary);margin-top:2px;">${q >= 80 ? '高质量，联系方式完整' : q >= 60 ? '中等质量，部分待补充' : '基础数据，建议完善'}</div>
            </div>
        </div>

        <div class="drawer-section">
            <h4>企业信息</h4>
            <div class="drawer-row"><div class="drawer-row-icon">🏢</div><div class="drawer-row-info"><div class="drawer-row-label">公司名称</div><div class="drawer-row-value">${esc(d.company_name)}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">🌍</div><div class="drawer-row-info"><div class="drawer-row-label">国家/地区</div><div class="drawer-row-value">${esc(d.country || '—')}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">🏭</div><div class="drawer-row-info"><div class="drawer-row-label">行业</div><div class="drawer-row-value">${d.industry ? `<span class="industry-tag">${esc(d.industry)}</span>` : '—'}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">👥</div><div class="drawer-row-info"><div class="drawer-row-label">企业规模</div><div class="drawer-row-value">${esc(d.company_size || '—')}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">🏪</div><div class="drawer-row-info"><div class="drawer-row-label">门店数量</div><div class="drawer-row-value">${esc(d.store_count || '—')}</div></div></div>
        </div>

        <div class="drawer-section">
            <h4>采购决策链</h4>
            <div class="drawer-row"><div class="drawer-row-icon">👤</div><div class="drawer-row-info"><div class="drawer-row-label">联系人</div><div class="drawer-row-value ${d.contact_person ? '' : 'missing'}">${esc(d.contact_person) || '待补充'}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">💼</div><div class="drawer-row-info"><div class="drawer-row-label">职位</div><div class="drawer-row-value ${d.position ? '' : 'missing'}">${d.position ? `<span class="cell-position high">${esc(d.position)}</span>` : '待补充'}</div></div></div>
            <div class="drawer-row"><div class="drawer-row-icon">🏢</div><div class="drawer-row-info"><div class="drawer-row-label">部门</div><div class="drawer-row-value ${d.department ? '' : 'missing'}">${esc(d.department) || '待补充'}</div></div></div>
        </div>

        <div class="drawer-section">
            <h4>联系方式</h4>
            ${contactHtml}
        </div>

        <div class="drawer-section">
            <h4>🔍 找采购人员 & 海关数据</h4>
            <div class="social-bar">
                <a class="social-btn linkedin" href="https://www.linkedin.com/search/results/people/?keywords=${companySearch}%20buyer" target="_blank">LinkedIn 找 Buyer</a>
                <a class="social-btn linkedin" href="https://www.linkedin.com/search/results/people/?keywords=${companySearch}%20procurement" target="_blank">LinkedIn 找采购</a>
                <a class="social-btn facebook" href="https://www.facebook.com/search/top?q=${companySearch}" target="_blank">Facebook</a>
            </div>
            <div class="customs-box">
                📦 <strong>海关数据：</strong><a href="https://importyeti.com/search?q=${companySearch}" target="_blank" style="color:inherit;font-weight:600;text-decoration:underline;">点此在 ImportYeti 免费查询美国进口记录 →</a>
            </div>
        </div>
    `;

    document.getElementById('detailDrawer').classList.add('active');
    document.getElementById('drawerOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeDrawer() {
    document.getElementById('detailDrawer')?.classList.remove('active');
    document.getElementById('drawerOverlay')?.classList.remove('active');
    document.body.style.overflow = '';
}

// ===== Discovery (Lead Generation) =====
function extractDomain(url) {
    if (!url) return '';
    try {
        if (url.includes('@')) return url.split('@')[1];
        const u = new URL(url.startsWith('http') ? url : 'https://' + url);
        return u.hostname.replace('www.', '');
    } catch { return ''; }
}

function calculateLeadScore(company) {
    let score = 0;
    if (company.email) score += 20;
    if (company.procurement_email) score += 25;
    if (company.phone) score += 15;
    if (company.linkedin) score += 15;
    if (company.website) score += 10;
    if (company.position) score += 10;
    return Math.min(score, 100);
}

function renderDiscovery() {
    const filtered = applyDiscoveryFilters(state.data);
    document.getElementById('discoveryCount').textContent = filtered.length;

    // 统计真实邮箱和电话
    const emailCount = filtered.filter(d => d.email && d.email.includes('@')).length;
    const phoneCount = filtered.filter(d => d.phone).length;
    document.getElementById('discoveryEmailCount').textContent = emailCount;
    document.getElementById('discoveryPhoneCount').textContent = phoneCount;

    // 公司表格
    const cBody = document.getElementById('discoveryCompanyBody');
    if (cBody) {
        cBody.innerHTML = filtered.slice(0, 100).map(d => {
            const score = calculateLeadScore(d);
            const color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';
            const realEmail = (d.email && d.email.includes('@')) ? d.email : '';
            const website = d.website || '';
            const websiteDisplay = website ? website.replace(/^https?:\/\//, '').replace(/\/$/, '') : '';

            // 邮箱列：有真实邮箱则显示可点击的mailto链接，否则显示"官网联系"
            let emailCell = '—';
            if (realEmail) {
                emailCell = `<a href="mailto:${esc(realEmail)}?subject=${encodeURIComponent('Supplier Inquiry - ' + d.company_name)}" class="email-link" title="点击发送邮件">✉️ ${esc(realEmail)}</a>`;
            } else if (website) {
                emailCell = `<a href="${esc(website)}" target="_blank" class="website-contact-link" title="访问官网找联系方式">🌐 官网联系页</a>`;
            }

            // 电话列
            let phoneCell = '—';
            if (d.phone) {
                phoneCell = `<a href="tel:${esc(d.phone.replace(/[^0-9+]/g, ''))}" class="phone-link" title="点击拨打">📞 ${esc(d.phone)}</a>`;
            }

            // 官网列
            let webCell = '—';
            if (website) {
                webCell = `<a href="${esc(website)}" target="_blank" class="website-link">${esc(websiteDisplay)}</a>`;
            }

            // 操作列
            let actions = '';
            if (realEmail) {
                actions += `<button class="action-btn action-btn--email" onclick="event.stopPropagation();sendEmail('${esc(realEmail)}','${esc(d.company_name)}')">发送邮件</button>`;
            }
            if (website) {
                actions += `<button class="action-btn" onclick="event.stopPropagation();window.open('${esc(website)}','_blank')">官网</button>`;
            }
            actions += `<button class="action-btn" onclick="event.stopPropagation();openDrawer('${esc(d.company_name)}')">详情</button>`;

            return `<tr>
                <td><span class="cell-name">${esc(d.company_name)}</span></td>
                <td>${d.industry ? `<span class="industry-tag">${esc(d.industry)}</span>` : '—'}</td>
                <td><span class="cell-country">${esc(d.country || '—')}${d.city ? ' / ' + esc(d.city) : ''}</span></td>
                <td>${emailCell}</td>
                <td>${phoneCell}</td>
                <td>${webCell}</td>
                <td><div class="lead-score"><div class="lead-score-bar"><div class="lead-score-fill" style="width:${score}%;background:${color}"></div></div><span class="lead-score-num" style="color:${color}">${score}</span></div></td>
                <td class="action-cell">${actions}</td>
            </tr>`;
        }).join('') || `<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-tertiary);">暂无匹配数据</td></tr>`;
    }
}

function sendEmail(email, company) {
    const subject = encodeURIComponent('Supplier Inquiry - ' + company);
    const body = encodeURIComponent(`Dear ${company} Team,\n\nI hope this email finds you well. We are a manufacturer/supplier specializing in [your product category]. We would like to explore potential business opportunities with your company.\n\nCould you please direct me to the appropriate person in your procurement/purchasing department?\n\nBest regards,\n[Your Name]\n[Your Company]`);
    window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
}

function applyDiscoveryFilters(data) {
    const kw = document.getElementById('filterKeyword')?.value?.toLowerCase() || '';
    const industry = document.getElementById('filterIndustryDisc')?.value || '';
    const country = document.getElementById('filterCountryDisc')?.value || '';
    const hasEmail = document.getElementById('filterHasEmail')?.checked;
    const hasPhone = document.getElementById('filterHasPhone')?.checked;
    const hasLi = document.getElementById('filterHasLinkedIn')?.checked;

    return data.filter(d => {
        if (kw && !(d.company_name?.toLowerCase().includes(kw) || d.industry?.toLowerCase().includes(kw) || d.product_categories?.toLowerCase().includes(kw))) return false;
        if (industry && d.industry !== industry) return false;
        if (country && d.country !== country) return false;
        if (hasEmail && !(d.email && d.email.includes('@'))) return false;
        if (hasPhone && !d.phone) return false;
        if (hasLi && !d.linkedin) return false;
        return true;
    });
}

function initDiscovery() {
    // 筛选按钮
    document.getElementById('applyDiscoveryFilters')?.addEventListener('click', renderDiscovery);

    // 实时筛选
    ['filterKeyword', 'filterIndustryDisc', 'filterCountryDisc', 'filterHasEmail', 'filterHasPhone', 'filterHasLinkedIn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.addEventListener('input', renderDiscovery); el.addEventListener('change', renderDiscovery); }
    });

    // 重置
    document.getElementById('resetFiltersBtn')?.addEventListener('click', () => {
        document.getElementById('filterKeyword').value = '';
        document.getElementById('filterIndustryDisc').value = '';
        document.getElementById('filterCountryDisc').value = '';
        document.querySelectorAll('.checks-inline input').forEach(cb => cb.checked = false);
        renderDiscovery();
    });

    // 导出
    document.getElementById('discoveryExportBtn')?.addEventListener('click', () => {
        exportCSV(applyDiscoveryFilters(state.data));
    });
}

// ===== Facebook Leads =====
let fbState = { contacts: [], companies: [], all: [], filtered: [] };

async function loadFacebookData() {
    try {
        const [cResp, pResp] = await Promise.all([
            fetch('data/facebook_leads.json', { cache: 'no-cache' }),
            fetch('data/facebook_companies.json', { cache: 'no-cache' })
        ]);
        fbState.contacts = await cResp.json();
        fbState.companies = await pResp.json();

        // 合并为统一列表
        fbState.all = [
            ...fbState.contacts.map(c => ({ ...c, type: 'contact', typeLabel: '联系人' })),
            ...fbState.companies.map(c => ({ ...c, type: 'company', typeLabel: '公司', name: c.company_name, title: c.industry }))
        ];
        fbState.filtered = [...fbState.all];

        // 更新 KPI
        document.getElementById('fbContacts').textContent = fbState.contacts.length;
        document.getElementById('fbCompanies').textContent = fbState.companies.length;
        const countries = new Set(fbState.all.map(d => d.country).filter(Boolean));
        document.getElementById('fbCountries').textContent = countries.size;
        document.getElementById('fbTotal').textContent = fbState.all.length;

        // 填充国家和行业下拉
        populateFbFilters();
        renderFbTable();
    } catch (e) {
        console.error('Facebook data load error:', e);
    }
}

function populateFbFilters() {
    const countrySelect = document.getElementById('fbCountry');
    const industrySelect = document.getElementById('fbIndustry');
    const countries = [...new Set(fbState.all.map(d => d.country).filter(Boolean))].sort();
    const industries = [...new Set(fbState.all.map(d => d.industry).filter(Boolean))].sort();

    countrySelect.innerHTML = '<option value="">全部国家</option>' + countries.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('');
    industrySelect.innerHTML = '<option value="">全部行业</option>' + industries.map(i => `<option value="${esc(i)}">${esc(i)}</option>`).join('');
}

function renderFbTable() {
    const tbody = document.getElementById('fbTableBody');
    if (!tbody) return;

    tbody.innerHTML = fbState.filtered.map(d => {
        const typeColor = d.type === 'contact' ? '#3b82f6' : '#f59e0b';
        const quality = d.data_quality || 50;
        const qColor = quality >= 70 ? '#10b981' : quality >= 50 ? '#f59e0b' : '#ef4444';
        const name = d.name || d.company_name || '—';
        const phone = d.phone ? `<a href="tel:${esc(d.phone)}" style="color:#10b981;text-decoration:none;font-weight:600;">${esc(d.phone)}</a>` : '<span style="color:var(--text-tertiary);">—</span>';
        const email = d.email ? `<a href="mailto:${esc(d.email)}" style="color:#3b82f6;text-decoration:none;font-weight:600;">${esc(d.email)}</a>` : '<span style="color:var(--text-tertiary);">—</span>';
        const whatsapp = d.whatsapp ? `<a href="https://wa.me/${esc(d.whatsapp.replace(/[^0-9]/g,''))}" target="_blank" style="color:#25D366;text-decoration:none;font-weight:600;">💬 ${esc(d.whatsapp)}</a>` : '<span style="color:var(--text-tertiary);">—</span>';

        let actions = '';
        if (d.type === 'contact') {
            actions += `<button class="action-btn" onclick="searchFbProfile('${esc(name)}')">FB搜索</button>`;
        } else {
            actions += `<button class="action-btn" onclick="searchFbPage('${esc(name)}')">访问主页</button>`;
        }
        if (d.website) actions += `<a href="https://${esc(d.website.replace(/^https?:\/\//,''))}" target="_blank" class="action-btn" style="text-decoration:none;">🌐官网</a>`;

        return `<tr>
            <td><span class="cell-name">${esc(name)}</span></td>
            <td><span class="industry-tag" style="background:${typeColor}15;color:${typeColor};">${d.typeLabel}</span></td>
            <td>${esc(d.title || d.industry || '—')}</td>
            <td>${esc(d.company || '—')}</td>
            <td><span class="cell-country">${esc(d.country || '—')}${d.city ? ' / ' + esc(d.city) : ''}</span></td>
            <td>${phone}</td>
            <td>${email}</td>
            <td>${whatsapp}</td>
            <td><span style="color:${qColor};font-weight:700;">${quality}</span></td>
            <td class="action-cell">${actions}</td>
        </tr>`;
    }).join('') || `<tr><td colspan="10" style="text-align:center;padding:40px;color:var(--text-tertiary);">暂无数据</td></tr>`;
}

function applyFbFilters() {
    const kw = document.getElementById('fbKeyword')?.value?.toLowerCase() || '';
    const type = document.getElementById('fbType')?.value || '';
    const country = document.getElementById('fbCountry')?.value || '';
    const industry = document.getElementById('fbIndustry')?.value || '';

    fbState.filtered = fbState.all.filter(d => {
        if (kw && !(d.name?.toLowerCase().includes(kw) || d.company?.toLowerCase().includes(kw) || d.industry?.toLowerCase().includes(kw) || d.title?.toLowerCase().includes(kw))) return false;
        if (type && d.type !== type) return false;
        if (country && d.country !== country) return false;
        if (industry && d.industry !== industry) return false;
        return true;
    });
    renderFbTable();
}

function searchFbProfile(name) {
    window.open(`https://www.facebook.com/search/people/?q=${encodeURIComponent(name)}`, '_blank');
}

function searchFbPage(name) {
    window.open(`https://www.facebook.com/search/pages/?q=${encodeURIComponent(name)}`, '_blank');
}

function initFacebook() {
    ['fbKeyword', 'fbType', 'fbCountry', 'fbIndustry'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.addEventListener('input', applyFbFilters); el.addEventListener('change', applyFbFilters); }
    });
    document.getElementById('fbFilterBtn')?.addEventListener('click', applyFbFilters);
    document.getElementById('fbResetBtn')?.addEventListener('click', () => {
        document.getElementById('fbKeyword').value = '';
        document.getElementById('fbType').value = '';
        document.getElementById('fbCountry').value = '';
        document.getElementById('fbIndustry').value = '';
        applyFbFilters();
    });
    document.getElementById('fbExportBtn')?.addEventListener('click', () => {
        exportCSV(fbState.filtered.map(d => ({
            名称: d.name || d.company_name,
            类型: d.typeLabel,
            职位: d.title,
            行业: d.industry,
            公司: d.company,
            国家: d.country,
            城市: d.city,
            地址: d.address,
            电话: d.phone || '',
            粉丝数: d.facebook_fans || '',
            质量分: d.data_quality
        })));
    });
}

// ===== Theme & Font =====
function setTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute('data-theme', theme === 'dark' ? 'dark' : 'light');
    document.body.className = document.body.className.replace(/theme-\w+/g, '').trim();
    if (theme !== 'light' && theme !== 'dark') {
        document.body.classList.add('theme-' + theme);
    }
    document.querySelectorAll('.seg-btn[data-theme]').forEach(el => {
        el.classList.toggle('active', el.dataset.theme === theme);
    });
    localStorage.setItem('siq_theme', theme);
    setTimeout(() => Object.values(state.charts).forEach(c => c?.resize()), 100);
}

function setFontSize(size) {
    document.body.className = document.body.className.replace(/font-\w+/g, '').trim();
    document.body.classList.add('font-' + size);
    document.querySelectorAll('.seg-btn[data-size]').forEach(el => {
        el.classList.toggle('active', el.dataset.size === size);
    });
    localStorage.setItem('siq_fontsize', size);
}

function initPreferences() {
    const theme = localStorage.getItem('siq_theme') || 'light';
    setTheme(theme);
    const font = localStorage.getItem('siq_fontsize') || 'md';
    setFontSize(font);

    document.querySelectorAll('.seg-btn[data-theme]').forEach(el => {
        el.addEventListener('click', () => setTheme(el.dataset.theme));
    });
    document.querySelectorAll('.seg-btn[data-size]').forEach(el => {
        el.addEventListener('click', () => setFontSize(el.dataset.size));
    });
}

// ===== Last Update =====
function showLastUpdateTime() {
    const data = state.data;
    if (!data.length) return;
    const times = data.map(d => d.scraped_at).filter(Boolean).sort();
    const latest = times[times.length - 1];
    if (latest) {
        const date = new Date(latest);
        const formatted = date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
        document.getElementById('settingsLastUpdate').textContent = formatted;
        document.getElementById('lastRunTime').textContent = formatted;
    }
}

// ===== Update Modal =====
function openUpdateModal() {
    const token = localStorage.getItem('github_token');
    if (token) document.getElementById('githubTokenInput').value = token;
    document.getElementById('updateModal').classList.add('active');
}
function closeUpdateModal() {
    document.getElementById('updateModal').classList.remove('active');
}
async function triggerUpdate() {
    const token = document.getElementById('githubTokenInput').value.trim();
    if (!token) { alert('请输入 GitHub Token'); return; }
    localStorage.setItem('github_token', token);

    const btn = document.getElementById('confirmUpdateBtn');
    btn.disabled = true; btn.textContent = '触发中...';

    try {
        const resp = await fetch('https://api.github.com/repos/nebulaspider/supermarket-contacts/actions/workflows/update-data.yml/dispatches', {
            method: 'POST',
            headers: { 'Accept': 'application/vnd.github.v3+json', 'Authorization': `token ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ ref: 'main', inputs: { industries: 'general,retail,electronics,furniture,cosmetics,food,fashion', directory_max: '150' } }),
        });
        if (resp.status === 204) {
            closeUpdateModal();
            showToast('✅ 已触发数据更新！预计 3-8 分钟后完成。');
        } else if (resp.status === 401) {
            localStorage.removeItem('github_token');
            alert('Token 无效或已过期，请重新输入。');
        } else {
            alert('触发失败: HTTP ' + resp.status);
        }
    } catch (e) {
        alert('网络错误: ' + e.message);
    }
    btn.disabled = false; btn.textContent = '立即更新';
}

// ===== Utilities =====
function isHighValuePosition(pos) {
    if (!pos) return false;
    const lower = pos.toLowerCase();
    return ['ceo', 'director', '总监', '经理', 'manager', 'head', 'chief', 'vp', '采购', 'sourcing', 'buyer', 'senior'].some(kw => lower.includes(kw));
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => showToast('📋 已复制: ' + text)).catch(() => {
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); document.body.removeChild(ta);
        showToast('📋 已复制');
    });
}

function showToast(message) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(16px)'; setTimeout(() => toast.remove(), 300); }, 3500);
}

function exportCSV(data) {
    const rows = data || state.filtered;
    if (!rows.length) { showToast('⚠️ 没有可导出的数据'); return; }
    const headers = ['公司名称', '国家', '城市', '行业', '职位', '部门', '邮箱', '采购邮箱', '电话', 'LinkedIn', '官网'];
    const keys = ['company_name', 'country', 'city', 'industry', 'position', 'department', 'email', 'procurement_email', 'phone', 'linkedin', 'website'];
    let csv = '\uFEFF' + headers.join(',') + '\n';
    rows.forEach(d => {
        csv += keys.map(k => `"${(d[k] || '').toString().replace(/"/g, '""')}"`).join(',') + '\n';
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'cyrus-ai-clients.csv';
    link.click();
    showToast('✅ 已导出 ' + rows.length + ' 条数据');
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

// Global exports
window.openDrawer = openDrawer;
window.closeDrawer = closeDrawer;
window.copyText = copyText;
window.goPage = goPage;
window.exportCSV = exportCSV;
window.openUpdateModal = openUpdateModal;
window.closeUpdateModal = closeUpdateModal;

// ============================================
// 获客中心 Acquisition Hub
// ============================================
function initAcquisition() {
    const searchBtn = document.getElementById('acqSearchBtn');
    if (!searchBtn) return;

    const updateLinks = () => {
        const kw = document.getElementById('acqKeyword')?.value?.trim() || 'product';
        const country = document.getElementById('acqCountry')?.value || '';
        const countryName = { USA:'United States', UK:'United Kingdom', Germany:'Germany', France:'France', Japan:'Japan', Australia:'Australia', Canada:'Canada', UAE:'UAE', Brazil:'Brazil', India:'India' }[country] || '';
        const kwEnc = encodeURIComponent(kw);

        // LinkedIn
        setLink('li-buyer', `https://www.linkedin.com/search/results/people/?keywords=${kwEnc}%20procurement%20manager${country ? '%20' + encodeURIComponent(countryName) : ''}`);
        setLink('li-sourcing', `https://www.linkedin.com/search/results/people/?keywords=${kwEnc}%20sourcing%20manager${country ? '%20' + encodeURIComponent(countryName) : ''}`);
        setLink('li-company', `https://www.linkedin.com/search/results/companies/?keywords=${kwEnc}`);

        // Facebook
        setLink('fb-group', `https://www.facebook.com/search/groups/?q=${kwEnc}%20sourcing%20buying`);
        setLink('fb-page', `https://www.facebook.com/search/pages/?q=${kwEnc}%20importer%20distributor`);

        // Instagram
        setLink('ig-tag', `https://www.instagram.com/explore/tags/${kw.replace(/\s+/g, '')}/`);
        setLink('ig-account', `https://www.instagram.com/${kw.replace(/\s+/g, '')}/`);

        // X / Twitter
        setLink('x-looking', `https://x.com/search?q=${kwEnc}%20looking%20for%20supplier&src=typed_query`);
        setLink('x-sourcing', `https://x.com/search?q=${kwEnc}%20sourcing%20agent&src=typed_query`);

        // TikTok
        setLink('tt-hashtag', `https://www.tiktok.com/tag/${kw.replace(/\s+/g, '')}`);
        setLink('tt-creator', `https://www.tiktok.com/search?q=${kwEnc}%20manufacturer`);

        // B2B Platforms
        setLink('alibaba-search', `https://www.alibaba.com/trade/search?SearchText=${kwEnc}`);
        setLink('mic-search', `https://www.made-in-china.com/productdirectory.do?subaction=hunt&style=b&code=0&word=${kwEnc}`);
        setLink('gs-search', `https://www.globalsources.com/search/${kwEnc}.htm`);
        setLink('indiamart-search', `https://dir.indiamart.com/search.mp?ss=${kwEnc}`);
        setLink('ml-search', `https://www.mercadolibre.com/jobs/search?q=${kwEnc}`);
        setLink('ep-search', `https://www.europages.co.uk/companies/${kwEnc}.html`);

        // Google
        setLink('google-buyer', `https://www.google.com/search?q=${kwEnc}+importer+distributor+buyer${country ? '+' + encodeURIComponent(countryName) : ''}`);
        setLink('google-distributor', `https://www.google.com/search?q=${kwEnc}+wholesale+distributor${country ? '+' + encodeURIComponent(countryName) : ''}`);
        setLink('google-wholesaler', `https://www.google.com/search?q=${kwEnc}+wholesaler+supplier${country ? '+' + encodeURIComponent(countryName) : ''}`);
    };

    searchBtn.addEventListener('click', () => {
        updateLinks();
        showToast('🔍 已更新所有渠道搜索链接，点击任意链接开始获客！');
    });

    document.getElementById('acqKeyword')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { updateLinks(); searchBtn.click(); }
    });

    // Customs search
    document.getElementById('customsSearchBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        const kw = document.getElementById('customsKeyword')?.value?.trim() || 'product';
        window.open(`https://importyeti.com/search?q=${encodeURIComponent(kw)}`, '_blank');
    });

    // Copy email template
    document.getElementById('copyEmailBtn')?.addEventListener('click', () => {
        const text = document.getElementById('emailTemplate')?.textContent || '';
        copyText(text.trim());
    });

    updateLinks();
}

function setLink(id, url) {
    const el = document.getElementById(id);
    if (el) { el.href = url; el.target = '_blank'; el.rel = 'noopener'; }
}

// Init on load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initAcquisition, 300);
});
