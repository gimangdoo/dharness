/* CM Dashboard — vanilla JS controller
 * Endpoints:
 *   GET /api/projects
 *   GET /api/projects/{name}/sessions
 *   GET /api/projects/{name}/clusters
 *   GET /api/projects/{name}/compression
 *   GET /api/projects/{name}/pending
 *   GET /api/projects/{name}/tool-timeline
 *   GET /api/projects/{name}/inventory
 *   GET /api/projects/{name}/roadmap
 */
(() => {
  'use strict';

  const API = 'http://127.0.0.1:8765';
  const REFRESH_MS = 60_000;
  const TABS = ['overview', 'sessions', 'tools', 'memory', 'roadmap'];
  const CAT_VARS = ['--cat-1','--cat-2','--cat-3','--cat-4','--cat-5','--cat-6','--cat-7','--cat-8','--cat-9','--cat-10'];

  /* ─── state ─── */
  const state = {
    tab: 'overview',
    projects: [],            // /api/projects
    selectedProject: null,   // name
    compareMode: false,
    compareSet: new Set(),   // names in compare mode
    cache: {},               // cache[name] = { sessions, clusters, compression, pending, timeline, inventory, roadmap }
    lastUpdated: null,
    online: null,            // boolean once known
    bannerDismissed: false,
    sessionFilters: { digest: false, pending: false, warn: false },
    toolSearch: '',
    toolSections: { skills: true, agents: true, commands: true, hooks: true, mcp: true },
    activeSession: null,
    projFilter: '',
  };

  /* ─── DOM ─── */
  const $ = (id) => document.getElementById(id);
  const el = $('app');
  const projList = $('proj-list');
  const projCount = $('proj-count');
  const mainTitle = $('main-title');
  const mainPath = $('main-path');
  const lastUpdated = $('last-updated');
  const connDot = $('conn-dot');
  const connText = $('conn-text');
  const reloadBtn = $('reload-btn');
  const tabsEl = $('tabs');
  const panel = $('panel');
  const banner = $('offline-banner');
  const compareToggle = $('compare-toggle');
  const compareHint = $('compare-hint');
  const editLink = $('edit-projects-link');
  const projFilterInput = $('proj-filter');

  /* ─── tooltip singleton ─── */
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip';
  document.body.appendChild(tooltip);
  const showTip = (html, x, y) => {
    tooltip.innerHTML = html;
    tooltip.classList.add('on');
    const r = tooltip.getBoundingClientRect();
    let tx = x + 14, ty = y + 12;
    if (tx + r.width > window.innerWidth) tx = x - r.width - 14;
    if (ty + r.height > window.innerHeight) ty = y - r.height - 12;
    tooltip.style.left = tx + 'px';
    tooltip.style.top = ty + 'px';
  };
  const hideTip = () => tooltip.classList.remove('on');

  /* ─── formatters ─── */
  const NB = '\u202F'; // narrow no-break space
  const fmtNum = (n) => {
    if (n == null) return '—';
    const s = String(Math.round(n));
    if (s.length <= 3) return s;
    let out = '', i = s.length;
    while (i > 3) { out = NB + s.slice(i - 3, i) + out; i -= 3; }
    return s.slice(0, i) + out;
  };
  const fmtDuration = (mins) => {
    if (mins == null) return '—';
    if (mins < 60) return `${Math.round(mins)}m`;
    const h = Math.floor(mins / 60);
    const m = Math.round(mins - h * 60);
    return m ? `${h}h ${m}m` : `${h}h`;
  };
  const parseDate = (s) => {
    if (!s) return null;
    // Accept "YYYY-MM-DD" or full ISO
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return new Date(s + 'T00:00:00');
    return new Date(s);
  };
  const daysBetween = (a, b) => Math.floor((b - a) / 86400000);
  const fmtDateRel = (s) => {
    if (!s) return '—';
    const d = parseDate(s);
    if (!d || isNaN(+d)) return s;
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const that = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diff = daysBetween(that, today);
    if (diff === 0) return 'today';
    if (diff === 1) return 'yesterday';
    if (diff > 0 && diff <= 7) return `${diff}d ago`;
    if (diff < 0 && diff >= -7) return `in ${-diff}d`;
    return s.slice(0, 10);
  };
  const fmtDateAbs = (s) => s ? s.slice(0, 10) : '—';
  const fmtTime = (s) => s ? s.slice(11, 16) : '—';
  const safeJson = (s) => {
    if (!s) return [];
    try { const v = JSON.parse(s); return Array.isArray(v) ? v : []; } catch { return []; }
  };

  /* ─── color helpers ─── */
  const toolColor = new Map();
  const colorForTool = (name) => {
    if (!toolColor.has(name)) {
      toolColor.set(name, `var(${CAT_VARS[toolColor.size % CAT_VARS.length]})`);
    }
    return toolColor.get(name);
  };
  const colorForProject = (name) => {
    // hash to a category color
    let h = 0;
    for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) | 0;
    return `var(${CAT_VARS[Math.abs(h) % CAT_VARS.length]})`;
  };

  /* ─── fetch ─── */
  const apiFetch = async (path) => {
    const res = await fetch(API + path, { cache: 'no-store' });
    if (res.status === 503) {
      const err = new Error('no_db');
      err.code = 503;
      throw err;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  };

  const loadProjects = async () => {
    try {
      const list = await apiFetch('/api/projects');
      state.online = true;
      state.projects = list || [];
      return true;
    } catch (e) {
      state.online = false;
      // Fallback: sample data
      state.projects = (window.SAMPLE && window.SAMPLE.projects) || [];
      return false;
    }
  };

  const loadProjectData = async (name) => {
    if (!name) return;
    if (!state.cache[name]) state.cache[name] = {};
    const c = state.cache[name];

    if (state.online) {
      const endpoints = [
        ['sessions',    `/api/projects/${name}/sessions`],
        ['clusters',    `/api/projects/${name}/clusters`],
        ['compression', `/api/projects/${name}/compression`],
        ['pending',     `/api/projects/${name}/pending`],
        ['timeline',    `/api/projects/${name}/tool-timeline`],
        ['inventory',   `/api/projects/${name}/inventory`],
        ['roadmap',     `/api/projects/${name}/roadmap`],
      ];
      await Promise.all(endpoints.map(async ([k, p]) => {
        try { c[k] = await apiFetch(p); c[k + '__err'] = null; }
        catch (e) { c[k + '__err'] = e.code === 503 ? 'no_db' : 'error'; c[k] = null; }
      }));
    } else {
      const sample = window.SAMPLE && window.SAMPLE.perProject && window.SAMPLE.perProject[name];
      if (sample) {
        Object.assign(c, sample);
      } else {
        // For projects with no sample, mark no_db
        ['sessions','clusters','compression','pending','timeline','inventory','roadmap'].forEach(k => {
          c[k] = null; c[k + '__err'] = 'no_db';
        });
      }
    }
  };

  /* ─── render: sidebar ─── */
  const renderSidebar = () => {
    const filter = state.projFilter.trim().toLowerCase();
    const list = state.projects.filter(p => !filter || p.name.toLowerCase().includes(filter));
    projCount.textContent = state.projects.length;
    projList.innerHTML = '';
    if (list.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.style.padding = '20px 12px';
      empty.innerHTML = `<div class="empty-title">No projects</div>
        <div class="empty-sub">Add entries to <code class="mono">projects.json</code> to populate this list.</div>`;
      projList.appendChild(empty);
      return;
    }
    for (const p of list) {
      const item = document.createElement('div');
      item.className = 'proj-item';
      item.setAttribute('role', 'button');
      const isActive = !state.compareMode && state.selectedProject === p.name;
      const inCompare = state.compareSet.has(p.name);
      if (isActive) item.setAttribute('aria-selected', 'true');
      if (inCompare) item.classList.add('selected-compare');
      item.innerHTML = `
        <span class="status-dot" data-state="${p.status}" title="${p.status}"></span>
        <div class="proj-item-body">
          <div class="proj-name">${escapeHTML(p.name)}</div>
          <div class="proj-meta">
            <span>${p.sessions != null ? fmtNum(p.sessions) + 's' : '—'}</span>
            <span class="sep">·</span>
            <span>${p.last_date ? fmtDateRel(p.last_date) : 'never'}</span>
          </div>
        </div>
        <span class="proj-checkbox"></span>
      `;
      item.addEventListener('click', () => {
        if (state.compareMode) {
          if (state.compareSet.has(p.name)) state.compareSet.delete(p.name);
          else if (state.compareSet.size < 5) state.compareSet.add(p.name);
          renderSidebar();
          renderMain();
        } else {
          if (p.status === 'missing') return;
          selectProject(p.name);
        }
      });
      projList.appendChild(item);
    }
  };

  /* ─── render: head ─── */
  const renderHead = () => {
    if (state.compareMode) {
      mainTitle.textContent = state.compareSet.size
        ? `Comparing ${state.compareSet.size} project${state.compareSet.size === 1 ? '' : 's'}`
        : 'Compare mode';
      mainPath.textContent = state.compareSet.size ? Array.from(state.compareSet).join(' · ') : 'Select projects in the sidebar';
    } else {
      const p = state.projects.find(x => x.name === state.selectedProject);
      mainTitle.textContent = p ? p.name : '—';
      mainPath.textContent = p ? p.path : '';
    }
    if (state.online === true) { connDot.dataset.state = 'ok'; connText.textContent = 'live'; }
    else if (state.online === false) { connDot.dataset.state = 'missing'; connText.textContent = 'offline'; }
    if (state.lastUpdated) {
      const ago = Math.round((Date.now() - state.lastUpdated) / 1000);
      lastUpdated.textContent = ago < 60 ? `updated ${ago}s ago` : `updated ${Math.round(ago/60)}m ago`;
    }
    banner.hidden = state.online !== false || state.bannerDismissed;
  };

  /* ─── tabs ─── */
  const setTab = (t) => {
    if (state.compareMode && t !== 'overview') return;
    state.tab = t;
    Array.from(tabsEl.children).forEach(b => b.setAttribute('aria-selected', b.dataset.tab === t ? 'true' : 'false'));
    renderMain();
  };

  /* ─── main render dispatch ─── */
  const renderMain = () => {
    renderHead();
    panel.innerHTML = '';
    if (state.compareMode) return renderCompareOverview();
    const name = state.selectedProject;
    if (!name) { return renderEmpty('Select a project', 'Pick a project in the sidebar to view its sessions, tools, memory, and roadmap.'); }
    const c = state.cache[name] || {};
    switch (state.tab) {
      case 'overview': return renderOverview(name, c);
      case 'sessions': return renderSessions(name, c);
      case 'tools':    return renderTools(name, c);
      case 'memory':   return renderMemory(name, c);
      case 'roadmap':  return renderRoadmap(name, c);
    }
  };

  const renderEmpty = (title, sub) => {
    const d = document.createElement('div');
    d.className = 'empty';
    d.innerHTML = `<div class="empty-title">${escapeHTML(title)}</div>${sub ? `<div class="empty-sub">${escapeHTML(sub)}</div>` : ''}`;
    panel.appendChild(d);
  };

  const renderNoDb = (what) => {
    const d = document.createElement('div');
    d.className = 'empty';
    d.innerHTML = `<div class="empty-title">No data yet</div>
      <div class="empty-sub">This project has no <code class="mono">observations.db</code>. ${escapeHTML(what)} will appear once the harness records its first session.</div>`;
    return d;
  };

  /* ─── OVERVIEW ─── */
  const renderOverview = (name, c) => {
    const proj = state.projects.find(x => x.name === name);
    if (!proj) return;

    // stats row
    const stats = document.createElement('div');
    stats.className = 'ov-stats';
    const cells = [
      { label: 'Sessions',     value: fmtNum(proj.sessions),       sub: proj.first_date ? `since ${fmtDateAbs(proj.first_date)}` : '' },
      { label: 'Total time',   value: fmtDuration(proj.total_minutes), sub: proj.sessions ? `${Math.round(proj.total_minutes / Math.max(proj.sessions,1))}m avg` : '' },
      { label: 'Last activity',value: fmtDateRel(proj.last_date),  sub: proj.last_date ? fmtDateAbs(proj.last_date) : '' },
      { label: 'Clusters',     value: fmtNum(proj.clusters),       sub: '' },
      { label: 'Pending Do',   value: fmtNum(proj.pending),        sub: proj.pending > 0 ? 'review in Memory' : 'caught up' },
    ];
    stats.innerHTML = cells.map(c => `
      <div class="ov-stat">
        <div class="ov-stat-label">${c.label}</div>
        <div class="ov-stat-value">${c.value}</div>
        <div class="ov-stat-sub">${c.sub}</div>
      </div>`).join('');
    panel.appendChild(stats);

    // chart
    const chartCard = document.createElement('div');
    chartCard.className = 'card';
    chartCard.style.marginTop = '16px';
    chartCard.innerHTML = `
      <div class="card-head">
        <h2 class="card-title">Tool calls — last 30 days</h2>
        <span class="card-sub" id="ov-chart-total"></span>
      </div>
      <div class="chart-wrap" id="ov-chart-wrap"></div>
      <div class="legend" id="ov-chart-legend"></div>`;
    panel.appendChild(chartCard);

    if (c.timeline__err === 'no_db' || !c.timeline) {
      $('ov-chart-wrap').appendChild(renderNoDb('Tool timeline'));
    } else {
      drawStackedBars($('ov-chart-wrap'), c.timeline, $('ov-chart-legend'), $('ov-chart-total'));
    }

    // two-col mini tables
    const two = document.createElement('div');
    two.className = 'ov-twocol';
    two.style.marginTop = '16px';

    // recent sessions
    const recentCard = document.createElement('div');
    recentCard.className = 'card';
    recentCard.innerHTML = `<div class="card-head"><h2 class="card-title">Recent sessions</h2><a class="card-sub" href="#" id="see-all-sessions" style="cursor:pointer">view all →</a></div>`;
    if (!c.sessions || c.sessions.length === 0) {
      recentCard.appendChild(renderNoDb('Sessions'));
    } else {
      const recent = c.sessions.slice(0, 5);
      const tbl = buildTable(
        ['Session', 'Date', 'Duration', 'Tools'],
        recent.map(s => [
          { html: `<span class="mono">${escapeHTML(s.session_id.slice(0,18))}…</span>` },
          { text: fmtDateRel(s.date), cls: 'faint' },
          { text: fmtDuration(s.duration_min), cls: 'num mono' },
          { text: String(safeJson(s.tools_used).length), cls: 'num mono' },
        ])
      );
      recentCard.appendChild(tbl);
    }
    two.appendChild(recentCard);

    // top clusters
    const clusterCard = document.createElement('div');
    clusterCard.className = 'card';
    clusterCard.innerHTML = `<div class="card-head"><h2 class="card-title">Top clusters by confidence</h2><a class="card-sub" href="#" id="see-all-clusters" style="cursor:pointer">view all →</a></div>`;
    if (!c.clusters || c.clusters.length === 0) {
      clusterCard.appendChild(renderNoDb('Clusters'));
    } else {
      const top = c.clusters.slice(0, 5);
      const tbl = buildTable(
        ['Theme', 'Members', 'Confidence'],
        top.map(cl => [
          { html: `${cl.promoted_path ? '<span class="pin" title="Promoted">📌</span>' : ''}${escapeHTML(cl.theme)}`, cls: 'truncate' },
          { text: String(cl.member_count), cls: 'num mono' },
          { html: confidenceCell(cl.confidence) },
        ])
      );
      clusterCard.appendChild(tbl);
    }
    two.appendChild(clusterCard);

    panel.appendChild(two);

    // wire mini-table links
    $('see-all-sessions')?.addEventListener('click', e => { e.preventDefault(); setTab('sessions'); });
    $('see-all-clusters')?.addEventListener('click', e => { e.preventDefault(); setTab('memory'); });
  };

  const renderCompareOverview = () => {
    const names = Array.from(state.compareSet);
    if (names.length === 0) {
      return renderEmpty('Compare mode', 'Select 2–5 projects in the sidebar. Other tabs are disabled while comparing.');
    }
    // ensure data
    Promise.all(names.map(n => loadProjectData(n))).then(() => {
      panel.innerHTML = '';
      // rollup stats
      const rows = names.map(n => state.projects.find(p => p.name === n)).filter(Boolean);
      const totals = rows.reduce((a,p) => ({
        sessions: a.sessions + (p.sessions||0),
        minutes:  a.minutes + (p.total_minutes||0),
        clusters: a.clusters + (p.clusters||0),
        pending:  a.pending + (p.pending||0),
      }), { sessions:0, minutes:0, clusters:0, pending:0 });

      const stats = document.createElement('div');
      stats.className = 'ov-stats';
      stats.innerHTML = [
        { l: 'Projects',  v: rows.length, s: 'compared' },
        { l: 'Sessions',  v: fmtNum(totals.sessions), s: '' },
        { l: 'Total time',v: fmtDuration(totals.minutes), s: '' },
        { l: 'Clusters',  v: fmtNum(totals.clusters), s: '' },
        { l: 'Pending',   v: fmtNum(totals.pending), s: '' },
      ].map(c => `<div class="ov-stat"><div class="ov-stat-label">${c.l}</div><div class="ov-stat-value">${c.v}</div><div class="ov-stat-sub">${c.s}</div></div>`).join('');
      panel.appendChild(stats);

      // overlay timeline: aggregate per project per day
      const overlayCard = document.createElement('div');
      overlayCard.className = 'card';
      overlayCard.style.marginTop = '16px';
      overlayCard.innerHTML = `<div class="card-head"><h2 class="card-title">Tool calls — last 30 days, by project</h2></div>
        <div class="chart-wrap" id="cmp-chart"></div>
        <div class="legend" id="cmp-legend"></div>`;
      panel.appendChild(overlayCard);

      // build a synthetic timeline where "tool" = project
      const aggregated = [];
      for (const n of names) {
        const tl = (state.cache[n] && state.cache[n].timeline) || [];
        const byDate = new Map();
        for (const r of tl) byDate.set(r.date, (byDate.get(r.date) || 0) + r.count);
        for (const [date, count] of byDate) aggregated.push({ date, tool: n, count });
      }
      drawStackedBars($('cmp-chart'), aggregated, $('cmp-legend'), null, /*projectColors*/ true);

      // per-project rollup table
      const tableCard = document.createElement('div');
      tableCard.className = 'card';
      tableCard.style.marginTop = '16px';
      tableCard.innerHTML = `<div class="card-head"><h2 class="card-title">Per-project rollup</h2></div>`;
      tableCard.appendChild(buildTable(
        ['Project', 'Sessions', 'Total time', 'Last activity', 'Clusters', 'Pending'],
        rows.map(p => [
          { html: `<span style="display:inline-flex;align-items:center;gap:8px"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${colorForProject(p.name)}"></span><span class="mono">${escapeHTML(p.name)}</span></span>` },
          { text: fmtNum(p.sessions), cls: 'num mono' },
          { text: fmtDuration(p.total_minutes), cls: 'num mono' },
          { text: fmtDateRel(p.last_date), cls: 'faint' },
          { text: fmtNum(p.clusters), cls: 'num mono' },
          { text: fmtNum(p.pending), cls: 'num mono' },
        ])
      ));
      panel.appendChild(tableCard);
    });
  };

  /* ─── stacked bars (SVG) ─── */
  const drawStackedBars = (mount, rows, legendEl, totalEl, projectColors = false) => {
    mount.innerHTML = '';
    if (!rows || rows.length === 0) {
      const e = document.createElement('div');
      e.className = 'empty';
      e.innerHTML = `<div class="empty-title">No tool calls yet</div><div class="empty-sub">Nothing recorded in the last 30 days.</div>`;
      mount.appendChild(e);
      return;
    }
    // group by date -> {tool: count}
    const byDate = new Map();
    const tools = new Set();
    for (const r of rows) {
      if (!byDate.has(r.date)) byDate.set(r.date, {});
      byDate.get(r.date)[r.tool] = (byDate.get(r.date)[r.tool] || 0) + r.count;
      tools.add(r.tool);
    }
    // build last-30-day axis
    const today = new Date();
    const dates = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date(today); d.setDate(d.getDate() - i);
      dates.push(d.toISOString().slice(0,10));
    }
    const toolOrder = Array.from(tools);

    // dimensions
    const W = mount.clientWidth || 800;
    const H = 220;
    const padL = 32, padR = 8, padT = 12, padB = 24;
    const innerW = W - padL - padR, innerH = H - padT - padB;
    const max = Math.max(1, ...dates.map(d => {
      const s = byDate.get(d); if (!s) return 0;
      return Object.values(s).reduce((a,b) => a+b, 0);
    }));
    const yScale = (v) => innerH - (v / max) * innerH;
    const barGap = 1;
    const barW = (innerW / dates.length) - barGap;

    let total = 0;
    rows.forEach(r => total += r.count);
    if (totalEl) totalEl.textContent = `${fmtNum(total)} calls`;

    const colorFor = projectColors ? colorForProject : colorForTool;

    // axis ticks (5 horizontal grid lines)
    const ticks = 4;
    let gridLines = '';
    for (let i = 0; i <= ticks; i++) {
      const v = (max / ticks) * i;
      const y = padT + yScale(v);
      gridLines += `<line class="chart-grid" x1="${padL}" x2="${W - padR}" y1="${y}" y2="${y}"/>`;
      gridLines += `<text class="chart-tick" x="${padL - 6}" y="${y + 3}" text-anchor="end">${Math.round(v)}</text>`;
    }
    // x ticks every 5 days
    let xTicks = '';
    dates.forEach((d, i) => {
      if (i % 5 === 0 || i === dates.length - 1) {
        const x = padL + i * (barW + barGap) + barW/2;
        xTicks += `<text class="chart-tick" x="${x}" y="${H - 8}" text-anchor="middle">${d.slice(5)}</text>`;
      }
    });

    // bars
    let bars = '';
    dates.forEach((d, i) => {
      const stack = byDate.get(d) || {};
      const x = padL + i * (barW + barGap);
      let yAcc = innerH;
      let dayTotal = 0;
      for (const t of toolOrder) {
        const v = stack[t] || 0;
        if (v <= 0) continue;
        const h = (v / max) * innerH;
        yAcc -= h;
        dayTotal += v;
        bars += `<rect class="chart-bar"
          x="${x}" y="${padT + yAcc}" width="${Math.max(1, barW)}" height="${h}"
          fill="${colorFor(t)}"
          data-date="${d}" data-tool="${escapeHTML(t)}" data-val="${v}"/>`;
      }
      // invisible hover region for full bar
      bars += `<rect x="${x - barGap/2}" y="${padT}" width="${barW + barGap}" height="${innerH}" fill="transparent"
                 data-day="${d}" data-day-total="${dayTotal}"/>`;
    });

    const svg = `<svg class="chart-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
      ${gridLines}
      ${bars}
      ${xTicks}
      <line class="chart-axis" x1="${padL}" x2="${W - padR}" y1="${padT + innerH}" y2="${padT + innerH}"/>
    </svg>`;
    mount.innerHTML = svg;

    // legend
    legendEl.innerHTML = toolOrder.map(t =>
      `<span class="legend-item"><span class="legend-swatch" style="background:${colorFor(t)}"></span>${escapeHTML(t)}</span>`
    ).join('');

    // tooltip wiring on bars
    mount.querySelectorAll('rect[data-tool]').forEach(b => {
      b.addEventListener('mousemove', (e) => {
        const t = b.dataset.tool, v = b.dataset.val, d = b.dataset.date;
        showTip(`<div class="tt-head">${escapeHTML(d)}</div>
          <div class="tt-row"><span class="k"><span class="legend-swatch" style="background:${colorFor(t)}"></span>${escapeHTML(t)}</span><span class="v">${fmtNum(v)}</span></div>`,
          e.clientX, e.clientY);
      });
      b.addEventListener('mouseleave', hideTip);
    });
    mount.querySelectorAll('rect[data-day]').forEach(b => {
      b.addEventListener('mousemove', (e) => {
        const total = b.dataset.dayTotal;
        if (+total === 0) {
          showTip(`<div class="tt-head">${escapeHTML(b.dataset.day)}</div><div class="tt-row"><span class="k">no activity</span></div>`, e.clientX, e.clientY);
        }
      });
      b.addEventListener('mouseleave', hideTip);
    });
  };

  /* ─── SESSIONS ─── */
  const renderSessions = (name, c) => {
    if (c.sessions__err === 'no_db' || !c.sessions) {
      panel.appendChild(renderNoDb('Sessions'));
      return;
    }
    if (c.sessions.length === 0) {
      return renderEmpty('No sessions recorded', 'Start a Claude Code session in this project to see it appear here.');
    }

    // filter bar
    const fb = document.createElement('div');
    fb.className = 'filter-bar';
    fb.innerHTML = `
      <span class="label">Filter</span>
      <button class="chip" data-f="digest"  aria-pressed="${state.sessionFilters.digest}">has digest</button>
      <button class="chip" data-f="pending" aria-pressed="${state.sessionFilters.pending}">has pending</button>
      <button class="chip" data-f="warn"    aria-pressed="${state.sessionFilters.warn}">has warnings</button>
      <span style="flex:1"></span>
      <span class="label" style="font-family:var(--font-mono);text-transform:none;letter-spacing:0">${c.sessions.length} total</span>
    `;
    panel.appendChild(fb);
    fb.querySelectorAll('.chip').forEach(b => {
      b.addEventListener('click', () => {
        const k = b.dataset.f;
        state.sessionFilters[k] = !state.sessionFilters[k];
        renderMain();
      });
    });

    const filtered = c.sessions.filter(s => {
      if (state.sessionFilters.digest  && !s.has_digest) return false;
      if (state.sessionFilters.pending && !s.pending_count) return false;
      if (state.sessionFilters.warn    && !s.warn_count) return false;
      return true;
    });

    if (filtered.length === 0) {
      const d = document.createElement('div');
      d.className = 'tl-empty';
      d.textContent = 'No sessions match the active filters.';
      panel.appendChild(d);
      return;
    }

    // group by date
    const byDate = new Map();
    for (const s of filtered) {
      if (!byDate.has(s.date)) byDate.set(s.date, []);
      byDate.get(s.date).push(s);
    }
    const tl = document.createElement('div');
    tl.className = 'timeline';
    for (const [date, items] of byDate) {
      const day = document.createElement('div');
      day.className = 'tl-day';
      day.innerHTML = `<div class="tl-day-label">${escapeHTML(date)}<span class="rel">${fmtDateRel(date)}</span></div>
        <div class="tl-sessions"></div>`;
      const wrap = day.querySelector('.tl-sessions');
      for (const s of items) {
        const used = safeJson(s.tools_used);
        const card = document.createElement('div');
        card.className = 'tl-card';
        if (state.activeSession === s.session_id) card.classList.add('active');
        card.innerHTML = `
          <div>
            <div class="tl-card-id">${escapeHTML(s.session_id)}</div>
            <div class="tl-card-meta">
              <span><span class="k">dur</span>${fmtDuration(s.duration_min)}</span>
              <span><span class="k">tools</span>${used.length}</span>
              <span><span class="k">start</span>${fmtTime(s.started_at)}</span>
              <span><span class="k">end</span>${fmtTime(s.ended_at)}</span>
            </div>
          </div>
          <div class="tl-card-badges">
            ${s.has_digest ? '<span class="badge ok" title="Digest written">✓ digest</span>' : ''}
            ${s.pending_count ? `<span class="badge accent">${s.pending_count} pending</span>` : ''}
            ${s.warn_count ? `<span class="badge warn">⚠ ${s.warn_count}</span>` : ''}
          </div>`;
        card.addEventListener('click', () => openSession(s));
        wrap.appendChild(card);
      }
      tl.appendChild(day);
    }
    panel.appendChild(tl);
  };

  const openSession = (s) => {
    state.activeSession = s.session_id;
    $('slideover-id').textContent = s.session_id;
    const used = safeJson(s.tools_used);
    const counts = new Map();
    used.forEach(t => counts.set(t, (counts.get(t) || 0) + 1));
    const sorted = Array.from(counts.entries()).sort((a,b) => b[1] - a[1]);

    $('slideover-body').innerHTML = `
      <div class="so-section">
        <h3 class="so-section-title">Metadata</h3>
        <dl class="so-kvs">
          <dt>Date</dt><dd>${escapeHTML(s.date)}</dd>
          <dt>Started</dt><dd>${escapeHTML(s.started_at || '—')}</dd>
          <dt>Ended</dt><dd>${escapeHTML(s.ended_at || '—')}</dd>
          <dt>Duration</dt><dd>${fmtDuration(s.duration_min)}</dd>
          <dt>Project</dt><dd>${escapeHTML(s.project)}</dd>
          <dt>Digest</dt><dd>${s.has_digest ? '✓ written' : '— not yet'}</dd>
          <dt>Pending</dt><dd>${s.pending_count || 0}</dd>
          <dt>Warnings</dt><dd>${s.warn_count || 0}</dd>
        </dl>
      </div>
      <div class="so-section">
        <h3 class="so-section-title">Tools used (${used.length})</h3>
        ${sorted.length === 0 ? '<div class="empty-sub">No tool usage recorded.</div>' :
          `<ul class="tools-used-list">${sorted.map(([t,n]) =>
            `<li><span class="swatch" style="background:${colorForTool(t)}"></span>${escapeHTML(t)}<span style="margin-left:auto;color:var(--text-3)">×${n}</span></li>`
          ).join('')}</ul>`}
      </div>`;
    $('slideover').hidden = false;
    $('slideover-scrim').hidden = false;
    renderMain();
  };
  const closeSession = () => {
    state.activeSession = null;
    $('slideover').hidden = true;
    $('slideover-scrim').hidden = true;
    renderMain();
  };

  /* ─── TOOLS ─── */
  const renderTools = (name, c) => {
    if (c.inventory__err === 'no_db' || !c.inventory) {
      panel.appendChild(renderNoDb('Inventory'));
      return;
    }
    const inv = c.inventory;

    const search = document.createElement('div');
    search.className = 'tools-search';
    search.style.position = 'relative';
    search.innerHTML = `<input id="tool-search-input" type="text" placeholder="Search skills, agents, commands, hooks, MCP…" value="${escapeAttr(state.toolSearch)}" />
      <kbd class="hint" style="position:absolute">/</kbd>`;
    panel.appendChild(search);
    const input = $('tool-search-input');
    input.addEventListener('input', () => {
      state.toolSearch = input.value;
      renderInventoryBody();
    });

    const body = document.createElement('div');
    body.id = 'inv-body';
    panel.appendChild(body);

    const renderInventoryBody = () => {
      body.innerHTML = '';
      const q = state.toolSearch.trim().toLowerCase();
      const match = (item) => {
        if (!q) return true;
        const blob = `${item.name||''} ${item.description||''} ${item.event||''} ${item.matcher||''} ${item.command||''}`.toLowerCase();
        return blob.includes(q);
      };

      const sections = [
        { key: 'skills',   label: 'Skills',   items: (inv.skills||[]).filter(match),   layout: 'r-default', total: inv.totals?.skills ?? (inv.skills||[]).length },
        { key: 'agents',   label: 'Agents',   items: (inv.agents||[]).filter(match),   layout: 'r-agent',   total: inv.totals?.agents ?? (inv.agents||[]).length },
        { key: 'commands', label: 'Commands', items: (inv.commands||[]).filter(match), layout: 'r-default', total: inv.totals?.commands ?? (inv.commands||[]).length },
        { key: 'hooks',    label: 'Hooks',    items: (inv.hooks||[]).filter(h => match({ name: `${h.event} ${h.matcher}`, description: h.command })), layout: 'r-hook', total: inv.totals?.hooks ?? (inv.hooks||[]).length },
        { key: 'mcp',      label: 'MCP servers', items: (inv.mcp||[]).filter(m => match({ name: m.name, description: (m.args||[]).join(' ') })), layout: 'r-mcp', total: inv.totals?.mcp ?? (inv.mcp||[]).length },
      ];

      for (const sec of sections) {
        const sect = document.createElement('div');
        sect.className = 'inv-section';
        sect.dataset.open = String(state.toolSections[sec.key]);
        sect.innerHTML = `
          <div class="inv-section-head">
            <svg class="chev" viewBox="0 0 10 10" stroke="currentColor" fill="none" stroke-width="1.5"><path d="M3 1l4 4-4 4"/></svg>
            <span class="inv-section-name">${sec.label}</span>
            <span class="inv-section-count">${sec.items.length}${q ? ` / ${sec.total}` : ''}</span>
          </div>
          <div class="inv-section-body"></div>`;
        const head = sect.querySelector('.inv-section-head');
        head.addEventListener('click', () => {
          state.toolSections[sec.key] = !state.toolSections[sec.key];
          sect.dataset.open = String(state.toolSections[sec.key]);
        });
        const inner = sect.querySelector('.inv-section-body');
        if (sec.items.length === 0) {
          inner.innerHTML = `<div class="empty" style="padding:18px"><div class="empty-sub">${q ? 'No matches in this section.' : 'None defined.'}</div></div>`;
        } else {
          for (const it of sec.items) inner.appendChild(invRow(sec.key, sec.layout, it));
        }
        body.appendChild(sect);
      }
    };

    const invRow = (kind, layout, it) => {
      const row = document.createElement('div');
      row.className = `inv-row ${layout}`;
      if (kind === 'agents') {
        row.innerHTML = `
          <div class="name">${escapeHTML(it.name)}</div>
          <div class="desc" title="${escapeAttr(it.description||'')}">${escapeHTML(it.description||'')}</div>
          <div class="meta">${escapeHTML(it.tools || '—')}</div>
          <div class="meta">${escapeHTML(it.model || '—')}</div>
          <div class="path" title="${escapeAttr(it.path||'')}">${escapeHTML(it.path||'')}</div>`;
      } else if (kind === 'hooks') {
        row.innerHTML = `
          <div class="name">${escapeHTML(it.event)}</div>
          <div class="meta">${escapeHTML(it.matcher || '*')}</div>
          <div class="meta">${escapeHTML(it.type)}</div>
          <div class="desc mono" style="font-size:11.5px;color:var(--text-2)">${escapeHTML(it.command||'')}</div>`;
      } else if (kind === 'mcp') {
        row.innerHTML = `
          <div class="name">${escapeHTML(it.name)}</div>
          <div class="meta">${escapeHTML(it.command || '')}</div>
          <div class="args-list">${(it.args||[]).map(a => `<span class="arg">${escapeHTML(a)}</span>`).join('')}</div>`;
      } else {
        row.innerHTML = `
          <div class="name">${escapeHTML(it.name)}</div>
          <div class="desc" title="${escapeAttr(it.description||'')}">${escapeHTML(it.description||'')}</div>
          <div class="path" title="${escapeAttr(it.path||'')}">${escapeHTML(it.path||'')}</div>`;
      }
      // expand description on click
      const d = row.querySelector('.desc');
      if (d) d.addEventListener('click', () => {
        d.dataset.expanded = d.dataset.expanded === 'true' ? 'false' : 'true';
      });
      return row;
    };

    renderInventoryBody();
  };

  /* ─── MEMORY ─── */
  const renderMemory = (name, c) => {
    const grid = document.createElement('div');
    grid.className = 'mem-grid';
    panel.appendChild(grid);

    // clusters card
    const clCard = document.createElement('div');
    clCard.className = 'card';
    clCard.innerHTML = `<div class="card-head"><h2 class="card-title">Clusters</h2><span class="card-sub" id="cl-count"></span></div>`;
    grid.appendChild(clCard);

    if (c.clusters__err === 'no_db' || !c.clusters) {
      clCard.appendChild(renderNoDb('Clusters'));
    } else if (c.clusters.length === 0) {
      const e = document.createElement('div'); e.className = 'empty';
      e.innerHTML = `<div class="empty-title">No clusters yet</div><div class="empty-sub">The harness builds clusters as observations accumulate.</div>`;
      clCard.appendChild(e);
    } else {
      $('cl-count') && ( $('cl-count').textContent = `${c.clusters.length} total · ${c.clusters.filter(x => x.promoted_path).length} promoted` );
      const tbl = buildTable(
        ['', 'Theme', 'Members', 'Confidence', 'Last accessed', 'Decay'],
        c.clusters.map(cl => [
          { html: cl.promoted_path ? `<span class="pin" title="Promoted: ${escapeAttr(cl.promoted_path)}">📌</span>` : '' },
          { html: `<span title="${escapeAttr(cl.cluster_id)}">${escapeHTML(cl.theme)}</span>`, cls: 'truncate' },
          { text: String(cl.member_count), cls: 'num mono' },
          { html: confidenceCell(cl.confidence) },
          { text: fmtDateRel(cl.last_accessed), cls: 'mono faint' },
          { html: cl.days_since_access > 14
              ? `<span class="badge warn">⚠ ${cl.days_since_access}d idle</span>`
              : `<span class="mono" style="color:var(--text-3)">${cl.days_since_access}d</span>` },
        ])
      );
      clCard.appendChild(tbl);
    }

    // pending card
    const peCard = document.createElement('div');
    peCard.className = 'card';
    peCard.innerHTML = `<div class="card-head"><h2 class="card-title">Pending Do queue</h2><span class="card-sub" id="pe-count"></span></div>`;
    grid.appendChild(peCard);

    if (c.pending__err === 'no_db' || !c.pending) {
      peCard.appendChild(renderNoDb('Pending items'));
    } else if (c.pending.length === 0) {
      const e = document.createElement('div'); e.className = 'empty';
      e.innerHTML = `<div class="empty-title">Caught up</div><div class="empty-sub">Nothing in the pending queue right now.</div>`;
      peCard.appendChild(e);
    } else {
      $('pe-count') && ( $('pe-count').textContent = `${c.pending.length} item${c.pending.length === 1 ? '' : 's'}` );
      // group by date
      const byDate = new Map();
      for (const p of c.pending) {
        if (!byDate.has(p.date)) byDate.set(p.date, []);
        byDate.get(p.date).push(p);
      }
      const list = document.createElement('div');
      for (const [date, items] of byDate) {
        const g = document.createElement('div');
        g.className = 'pending-group';
        g.innerHTML = `<div class="pending-group-head">
          <span class="pending-group-date">${escapeHTML(date)}</span>
          <span class="pending-group-rel">${fmtDateRel(date)}</span>
        </div><div class="pending-list"></div>`;
        const inner = g.querySelector('.pending-list');
        for (const p of items) {
          const tags = (p.tags || '').split(',').map(t => t.trim()).filter(Boolean);
          const it = document.createElement('div');
          it.className = 'pending-item';
          it.innerHTML = `
            <div>
              <div class="content">${escapeHTML(p.content)}</div>
              ${tags.length ? `<div class="tag-row">${tags.map(t => `<span class="tag">${escapeHTML(t)}</span>`).join('')}</div>` : ''}
            </div>
            <div class="meta">
              <span class="session-link" data-sid="${escapeAttr(p.session_id)}" title="Jump to session">${escapeHTML((p.session_id||'').slice(0,16))}…</span>
            </div>`;
          it.querySelector('.session-link')?.addEventListener('click', () => {
            const sid = p.session_id;
            setTab('sessions');
            // wait a tick for render, then find + open
            setTimeout(() => {
              const sess = (state.cache[name]?.sessions || []).find(s => s.session_id === sid);
              if (sess) openSession(sess);
            }, 0);
          });
          inner.appendChild(it);
        }
        list.appendChild(g);
      }
      peCard.appendChild(list);
    }
  };

  /* ─── ROADMAP ─── */
  const renderRoadmap = (name, c) => {
    if (c.roadmap__err === 'no_db' || !c.roadmap) {
      panel.appendChild(renderNoDb('Roadmap'));
      return;
    }
    if (c.roadmap.length === 0) {
      return renderEmpty('No roadmap tables found in CLAUDE.md',
        'Add a markdown table under any heading in CLAUDE.md and it will render here.');
    }
    const wrap = document.createElement('div');
    wrap.className = 'roadmap';
    for (const t of c.roadmap) {
      const card = document.createElement('div');
      card.className = 'rm-card';
      card.dataset.level = String(t.heading_level || 2);
      const head = `<div class="rm-head">
        <span class="rm-level">h${t.heading_level || 2}</span>
        <h3 class="rm-title">${escapeHTML(t.title || '(untitled)')}</h3>
        <span class="rm-rows">${t.row_count} row${t.row_count === 1 ? '' : 's'}</span>
      </div>`;
      const headerCells = (t.header || []).map(h => `<th>${escapeHTML(h)}</th>`).join('');
      const bodyRows = (t.rows || []).map(r => `<tr>${r.map(c => `<td>${renderCellMd(c)}</td>`).join('')}</tr>`).join('');
      card.innerHTML = head + `<div class="rm-table-wrap"><table class="rm-table">
        <thead><tr>${headerCells}</tr></thead>
        <tbody>${bodyRows}</tbody>
      </table></div>`;
      wrap.appendChild(card);
    }
    panel.appendChild(wrap);
  };
  const renderCellMd = (s) => {
    if (s == null) return '';
    let out = escapeHTML(String(s));
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return out;
  };

  /* ─── helpers ─── */
  const buildTable = (headers, rows) => {
    const tbl = document.createElement('table');
    tbl.className = 'tbl';
    const thead = `<thead><tr>${headers.map(h => `<th>${typeof h === 'string' ? escapeHTML(h) : (h.html || escapeHTML(h.text||''))}</th>`).join('')}</tr></thead>`;
    const tbody = `<tbody>${rows.map(r => `<tr>${r.map(c => {
      const cls = c.cls ? ` class="${c.cls}"` : '';
      const inner = c.html != null ? c.html : escapeHTML(c.text != null ? c.text : '');
      return `<td${cls}>${inner}</td>`;
    }).join('')}</tr>`).join('')}</tbody>`;
    tbl.innerHTML = thead + tbody;
    return tbl;
  };

  const confidenceCell = (v) => {
    const pct = Math.round(v * 100);
    return `<div class="confidence-cell">
      <div class="confidence-bar"><div class="confidence-fill" style="transform:scaleX(${v.toFixed(3)})"></div></div>
      <span class="confidence-num">${pct}%</span>
    </div>`;
  };

  const escapeHTML = (s) => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const escapeAttr = (s) => escapeHTML(s).replace(/"/g, '&quot;');

  /* ─── selection + refresh ─── */
  const selectProject = async (name) => {
    state.selectedProject = name;
    state.activeSession = null;
    closeSession();
    renderSidebar();
    renderHead();
    panel.innerHTML = `<div class="empty"><div class="empty-title">Loading ${escapeHTML(name)}…</div></div>`;
    await loadProjectData(name);
    state.lastUpdated = Date.now();
    renderMain();
  };

  const refresh = async () => {
    await loadProjects();
    if (state.selectedProject && !state.projects.find(p => p.name === state.selectedProject)) {
      state.selectedProject = state.projects[0]?.name || null;
    }
    if (!state.selectedProject) {
      const firstOk = state.projects.find(p => p.status === 'ok');
      if (firstOk) state.selectedProject = firstOk.name;
    }
    if (state.selectedProject) await loadProjectData(state.selectedProject);
    state.lastUpdated = Date.now();
    renderSidebar();
    renderMain();
  };

  /* ─── event wiring ─── */
  Array.from(tabsEl.children).forEach(b => {
    b.addEventListener('click', () => setTab(b.dataset.tab));
  });
  reloadBtn.addEventListener('click', () => { reloadBtn.classList.add('spinning'); refresh().finally(() => reloadBtn.classList.remove('spinning')); });
  $('banner-dismiss').addEventListener('click', () => { state.bannerDismissed = true; banner.hidden = true; });
  compareToggle.addEventListener('change', () => {
    state.compareMode = compareToggle.checked;
    document.body.classList.toggle('compare-mode', state.compareMode);
    compareHint.hidden = !state.compareMode;
    if (state.compareMode && state.selectedProject) state.compareSet.add(state.selectedProject);
    if (!state.compareMode) state.compareSet.clear();
    if (state.compareMode) state.tab = 'overview';
    Array.from(tabsEl.children).forEach(b => {
      b.disabled = state.compareMode && b.dataset.tab !== 'overview';
    });
    setTab('overview');
    renderSidebar();
  });
  projFilterInput.addEventListener('input', () => { state.projFilter = projFilterInput.value; renderSidebar(); });
  $('slideover-close').addEventListener('click', closeSession);
  $('slideover-scrim').addEventListener('click', closeSession);

  // edit projects.json link
  editLink.title = '/Users/dh/.cm/projects.json';
  editLink.addEventListener('click', (e) => e.preventDefault());

  // keyboard
  document.addEventListener('keydown', (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
      if (e.key === 'Escape') e.target.blur();
      return;
    }
    if (e.key === 'Escape') { closeSession(); return; }
    if (e.key === '/') {
      if (state.tab === 'tools') {
        const inp = $('tool-search-input');
        if (inp) { e.preventDefault(); inp.focus(); }
      }
      return;
    }
    const idx = TABS.indexOf(state.tab);
    if (e.key >= '1' && e.key <= '5') { e.preventDefault(); setTab(TABS[+e.key - 1]); }
    if (e.key === 'r' || e.key === 'R') { refresh(); }
  });

  /* ─── boot ─── */
  refresh();
  setInterval(refresh, REFRESH_MS);
  setInterval(renderHead, 10_000); // tick the "updated Ns ago"
})();
