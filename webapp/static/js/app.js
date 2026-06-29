/**
 * 考研英语真题词频统计 — 前端逻辑 v2
 */

const state = {
  filters: {},
  sortBy: 'freq',
  sortOrder: 'desc',
  page: 1,
  pageSize: 50,
  totalPages: 1,
  modalWord: null,
  modalPage: 1,
  modalTotalPages: 1,
  meta: null,
  debounceTimer: null,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
  statWordCount: $('#stat-word-count'),
  statFreqSum: $('#stat-freq-sum'),
  filterSearch: $('#filter-search'),
  filterFreqMin: $('#filter-freq-min'),
  filterFreqMax: $('#filter-freq-max'),
  freqTierGroup: $('#freq-tier-group'),
  ycTierGroup: $('#yc-tier-group'),
  filterFirstYear: $('#filter-first-year'),
  yearsGroup: $('#years-group'),
  typesGroup: $('#types-group'),
  toggleYears: $('#toggle-years'),
  toggleTypes: $('#toggle-types'),
  yearsQuick: $('#years-quick'),
  typesQuick: $('#types-quick'),
  activeFilters: $('#active-filters'),
  activeTags: $('#active-tags'),
  btnClearFilters: $('#btn-clear-filters'),
  tableBody: $('#word-table-body'),
  loading: $('#loading-indicator'),
  emptyState: $('#empty-state'),
  btnPrev: $('#btn-prev'),
  btnNext: $('#btn-next'),
  pageInfo: $('#page-info'),
  pageJumpInput: $('#page-jump-input'),
  btnJump: $('#btn-jump'),
  modalOverlay: $('#modal-overlay'),
  modalWord: $('#modal-word'),
  modalStats: $('#modal-stats'),
  modalBody: $('#modal-body'),
  modalBtnPrev: $('#modal-btn-prev'),
  modalBtnNext: $('#modal-btn-next'),
  modalPageInfo: $('#modal-page-info'),
  btnCloseModal: $('#btn-close-modal'),
  btnReset: $('#btn-reset'),
  btnExport: $('#btn-export'),
};

// ============================================================
// API
// ============================================================
async function api(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

function buildWordsUrl() {
  const p = new URLSearchParams();
  p.set('page', state.page);
  p.set('page_size', state.pageSize);
  p.set('sort_by', state.sortBy);
  p.set('sort_order', state.sortOrder);
  const f = state.filters;
  if (f.search) p.set('search', f.search);
  if (f.freq_min) p.set('freq_min', f.freq_min);
  if (f.freq_max) p.set('freq_max', f.freq_max);
  if (f.years && f.years.length) p.set('years', f.years.join(','));
  if (f.year_count_min) p.set('year_count_min', f.year_count_min);
  if (f.year_count_max) p.set('year_count_max', f.year_count_max);
  if (f.first_year) p.set('first_year', f.first_year);
  if (f.types && f.types.length) p.set('exam_types', f.types.join(','));
  return `/api/words?${p.toString()}`;
}

function buildExportUrl() {
  const p = new URLSearchParams();
  p.set('sort_by', state.sortBy);
  p.set('sort_order', state.sortOrder);
  const f = state.filters;
  if (f.search) p.set('search', f.search);
  if (f.freq_min) p.set('freq_min', f.freq_min);
  if (f.freq_max) p.set('freq_max', f.freq_max);
  if (f.years && f.years.length) p.set('years', f.years.join(','));
  if (f.year_count_min) p.set('year_count_min', f.year_count_min);
  if (f.year_count_max) p.set('year_count_max', f.year_count_max);
  if (f.first_year) p.set('first_year', f.first_year);
  if (f.types && f.types.length) p.set('exam_types', f.types.join(','));
  return `/api/export?${p.toString()}`;
}

// ============================================================
// 初始化
// ============================================================
async function init() {
  state.meta = await api('/api/meta/filters');

  // 年份勾选框（2列网格）
  for (const y of state.meta.years) {
    dom.yearsGroup.appendChild(checkboxItem(y, y));
  }

  // 题型勾选框
  for (const t of state.meta.exam_types) {
    dom.typesGroup.appendChild(checkboxItem(t, t));
  }

  // 折叠切换
  dom.toggleYears.addEventListener('click', () => {
    dom.toggleYears.classList.toggle('collapsed');
    dom.yearsGroup.classList.toggle('collapsed');
  });
  dom.toggleTypes.addEventListener('click', () => {
    dom.toggleTypes.classList.toggle('collapsed');
    dom.typesGroup.classList.toggle('collapsed');
  });

  await loadWords();
  bindEvents();
}

function checkboxItem(value, label) {
  const el = document.createElement('label');
  el.className = 'checkbox-item';
  const cb = document.createElement('input');
  cb.type = 'checkbox';
  cb.value = value;
  cb.addEventListener('change', () => applyFilters());
  el.appendChild(cb);
  el.appendChild(document.createTextNode(label));
  return el;
}

// ============================================================
// 加载词频表格
// ============================================================
async function loadWords() {
  dom.loading.style.display = 'block';
  dom.emptyState.style.display = 'none';
  dom.tableBody.innerHTML = '';

  try {
    const data = await api(buildWordsUrl());
    state.totalPages = data.total_pages;
    state.page = data.page;

    if (data.words.length === 0) {
      dom.emptyState.style.display = 'block';
    } else {
      renderTable(data.words);
    }
    updatePagination();
    dom.statWordCount.textContent = data.total.toLocaleString();
    dom.statFreqSum.textContent = data.total_freq_sum.toLocaleString();
    updateActiveFilters();
  } catch (err) {
    console.error(err);
    dom.emptyState.textContent = '加载失败';
    dom.emptyState.style.display = 'block';
  } finally {
    dom.loading.style.display = 'none';
  }
}

function renderTable(words) {
  dom.tableBody.innerHTML = '';
  for (const w of words) {
    const tr = document.createElement('tr');
    tr.addEventListener('click', () => openWordModal(w.word));

    const tdWord = document.createElement('td');
    tdWord.className = 'word-cell';
    tdWord.textContent = w.word;
    tr.appendChild(tdWord);

    const tdFreq = document.createElement('td');
    tdFreq.textContent = w.total_freq.toLocaleString();
    tr.appendChild(tdFreq);

    const tdYc = document.createElement('td');
    tdYc.textContent = w.year_count;
    tr.appendChild(tdYc);

    const tdFy = document.createElement('td');
    tdFy.textContent = w.first_year;
    tr.appendChild(tdFy);

    const tdTypes = document.createElement('td');
    tdTypes.className = 'type-tags';
    const types = w.freq_by_type || {};
    for (const [t, c] of Object.entries(types)) {
      const tag = document.createElement('span');
      tag.className = 'type-tag';
      tag.textContent = `${t}:${c}`;
      tdTypes.appendChild(tag);
    }
    tr.appendChild(tdTypes);
    dom.tableBody.appendChild(tr);
  }
}

function updatePagination() {
  dom.pageInfo.textContent = `第 ${state.page} 页 / 共 ${state.totalPages} 页`;
  dom.btnPrev.disabled = state.page <= 1;
  dom.btnNext.disabled = state.page >= state.totalPages;
  dom.pageJumpInput.value = state.page;
  dom.pageJumpInput.max = state.totalPages;
}

// ============================================================
// 激活筛选标签
// ============================================================
function updateActiveFilters() {
  const tags = [];
  const f = state.filters;

  if (f.search) tags.push({label: `"${f.search}"`, key: 'search'});
  if (f.freq_min !== undefined || f.freq_max !== undefined) {
    const lo = f.freq_min || 1;
    const hi = f.freq_max || '∞';
    tags.push({label: `词频 ${lo}–${hi}`, key: 'freq'});
  }
  if (f.year_count_min !== undefined || f.year_count_max !== undefined) {
    const lo = f.year_count_min || 1;
    const hi = f.year_count_max || '∞';
    tags.push({label: `年份数 ${lo}–${hi}`, key: 'year_count'});
  }
  if (f.first_year) tags.push({label: `首次 ${f.first_year}`, key: 'first_year'});
  if (f.years && f.years.length) {
    if (f.years.length <= 3) {
      tags.push({label: `年份: ${f.years.join(', ')}`, key: 'years'});
    } else {
      tags.push({label: `年份: ${f.years.length}个`, key: 'years'});
    }
  }
  if (f.types && f.types.length) {
    if (f.types.length <= 2) {
      tags.push({label: `题型: ${f.types.join(', ')}`, key: 'types'});
    } else {
      tags.push({label: `题型: ${f.types.length}种`, key: 'types'});
    }
  }

  if (tags.length > 0) {
    dom.activeFilters.style.display = 'flex';
    dom.activeTags.innerHTML = tags.map(t =>
      `<span class="filter-tag" data-key="${t.key}">${t.label} <span class="tag-x">×</span></span>`
    ).join('');
    // 点击标签清除对应筛选
    dom.activeTags.querySelectorAll('.filter-tag').forEach(tag => {
      tag.addEventListener('click', () => clearFilterTag(tag.dataset.key));
    });
  } else {
    dom.activeFilters.style.display = 'none';
  }
}

function clearFilterTag(key) {
  switch (key) {
    case 'search': dom.filterSearch.value = ''; break;
    case 'freq': dom.freqTierGroup.querySelectorAll('input').forEach(cb => cb.checked = false); break;
    case 'year_count': dom.ycTierGroup.querySelectorAll('input').forEach(cb => cb.checked = false); break;
    case 'first_year': dom.filterFirstYear.value = ''; break;
    case 'years':
      dom.yearsGroup.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
      break;
    case 'types':
      dom.typesGroup.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
      break;
  }
  applyFilters();
}

// ============================================================
// 五级分级映射（多选）
// ============================================================
const FREQ_TIERS = {
  '1': { min: 1, max: 1 },
  '2': { min: 2, max: 5 },
  '3': { min: 6, max: 20 },
  '4': { min: 21, max: 100 },
  '5': { min: 101, max: Infinity },
};
const YC_TIERS = {
  '1': { min: 1, max: 1 },
  '2': { min: 2, max: 5 },
  '3': { min: 6, max: 10 },
  '4': { min: 11, max: 20 },
  '5': { min: 21, max: 27 },
};

function tiersToRange(group, tierMap) {
  const checked = [...group.querySelectorAll('input[type="checkbox"]:checked')].map(cb => cb.value);
  if (checked.length === 0) return { min: '', max: '' };
  let min = Infinity, max = -Infinity;
  for (const v of checked) {
    const t = tierMap[v];
    if (t) { min = Math.min(min, t.min); max = Math.max(max, t.max); }
  }
  return { min: min === Infinity ? '' : min, max: max === -Infinity ? '' : (max === Infinity ? '' : max) };
}

// ============================================================
// 筛选逻辑
// ============================================================
function getChecked(group) {
  return [...group.querySelectorAll('input[type="checkbox"]:checked')].map(cb => cb.value);
}

function collectFilters() {
  const f = {};
  const search = dom.filterSearch.value.trim();
  if (search) f.search = search;
  // 词频：分级多选优先，取并集的最小-最大范围
  const freqRange = tiersToRange(dom.freqTierGroup, FREQ_TIERS);
  if (freqRange.min !== '') { f.freq_min = freqRange.min; f.freq_max = freqRange.max; }
  const years = getChecked(dom.yearsGroup);
  if (years.length) f.years = years;
  // 年份数：分级多选优先
  const ycRange = tiersToRange(dom.ycTierGroup, YC_TIERS);
  if (ycRange.min !== '') { f.year_count_min = ycRange.min; f.year_count_max = ycRange.max; }
  const fy = parseInt(dom.filterFirstYear.value);
  if (!isNaN(fy) && fy >= 2000) f.first_year = fy;
  const types = getChecked(dom.typesGroup);
  if (types.length) f.types = types;
  return f;
}

function applyFilters() {
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => {
    state.filters = collectFilters();
    state.page = 1;
    loadWords();
  }, 200);
}

function resetFilters() {
  dom.filterSearch.value = '';
  dom.filterFreqMin.value = '';
  dom.filterFreqMax.value = '';
  dom.yearsGroup.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
  dom.filterYcMin.value = '';
  dom.filterYcMax.value = '';
  dom.filterFirstYear.value = '';
  dom.typesGroup.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
  applyFilters();
}

// Quick actions for year/type groups
function setupQuickActions(container, group, type) {
  container.querySelectorAll('.btn-mini').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const action = btn.dataset.action;
      const cbs = group.querySelectorAll('input[type="checkbox"]');

      if (action === 'all') {
        cbs.forEach(cb => cb.checked = true);
      } else if (action === 'none') {
        cbs.forEach(cb => cb.checked = false);
      } else if (action === '00s') {
        cbs.forEach(cb => { cb.checked = parseInt(cb.value) >= 2000 && parseInt(cb.value) <= 2009; });
      } else if (action === '10s') {
        cbs.forEach(cb => { cb.checked = parseInt(cb.value) >= 2010 && parseInt(cb.value) <= 2019; });
      } else if (action === '20s') {
        cbs.forEach(cb => { cb.checked = parseInt(cb.value) >= 2020; });
      }
      applyFilters();
    });
  });
}

// ============================================================
// 单词详情弹窗
// ============================================================
async function openWordModal(word) {
  state.modalWord = word;
  state.modalPage = 1;
  const stats = await api(`/api/words/${encodeURIComponent(word)}`);
  dom.modalWord.textContent = word;
  dom.modalStats.textContent =
    `总词频: ${stats.total_freq} | 出现年份: ${stats.year_count} | 首次: ${stats.first_year} | 最后: ${stats.last_year}`;
  await loadModalCards();
  dom.modalOverlay.style.display = 'flex';
}

async function loadModalCards() {
  dom.modalBody.innerHTML = '<div class="loading">加载中…</div>';
  try {
    const data = await api(
      `/api/words/${encodeURIComponent(state.modalWord)}/occurrences?page=${state.modalPage}&page_size=10`
    );
    state.modalTotalPages = data.total_pages;
    dom.modalBody.innerHTML = '';
    for (const card of data.cards) dom.modalBody.appendChild(renderCard(card));
    dom.modalPageInfo.textContent = `第 ${data.page} 页 / 共 ${data.total_pages} 页`;
    dom.modalBtnPrev.disabled = data.page <= 1;
    dom.modalBtnNext.disabled = data.page >= data.total_pages;
  } catch (err) {
    dom.modalBody.innerHTML = '<div class="empty-state">加载失败</div>';
  }
}

function renderCard(card) {
  const container = document.createElement('div');
  container.className = 'card';

  const header = document.createElement('div');
  header.className = 'card-header';
  for (const [cls, text] of [['year', card.year], ['type', card.exam_type], ['section', card.section]]) {
    const badge = document.createElement('span');
    badge.className = `card-badge ${cls}`;
    badge.textContent = text;
    header.appendChild(badge);
  }
  container.appendChild(header);

  const sd = document.createElement('div');
  sd.className = 'card-sentence';
  const escaped = card.surface.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  sd.innerHTML = card.sentence.replace(new RegExp(`\\b${escaped}\\b`, 'gi'),
    m => `<span class="highlight">${m}</span>`);
  container.appendChild(sd);

  return container;
}

function closeModal() {
  dom.modalOverlay.style.display = 'none';
  state.modalWord = null;
}

// ============================================================
// 事件绑定
// ============================================================
function bindEvents() {
  // 快捷按钮
  setupQuickActions(dom.yearsQuick, dom.yearsGroup, 'years');
  setupQuickActions(dom.typesQuick, dom.typesGroup, 'types');

  // 输入框自动应用
  [dom.filterSearch, dom.filterFirstYear].forEach(input => {
    input.addEventListener('input', () => applyFilters());
  });

  // 分级勾选框：选/取消 → 自动应用
  [dom.freqTierGroup, dom.ycTierGroup].forEach(group => {
    group.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.addEventListener('change', () => applyFilters());
    });
  });

  // 清空按钮
  $$('.btn-clear-inline').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const key = btn.dataset.clear;
      if (key === 'freq') { dom.freqTierGroup.querySelectorAll('input').forEach(cb => cb.checked = false); }
      if (key === 'year_count') { dom.ycTierGroup.querySelectorAll('input').forEach(cb => cb.checked = false); }
      if (key === 'first_year') { dom.filterFirstYear.value = ''; }
      applyFilters();
    });
  });

  // 重置
  dom.btnReset.addEventListener('click', resetFilters);
  dom.btnClearFilters.addEventListener('click', resetFilters);

  // 排序
  $$('.word-table th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const sortBy = th.dataset.sort;
      if (state.sortBy === sortBy) {
        state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortBy = sortBy;
        state.sortOrder = 'desc';
      }
      $$('.word-table th.sortable').forEach(t => t.classList.remove('sort-asc', 'sort-desc', 'active'));
      th.classList.add('active', `sort-${state.sortOrder}`);
      state.page = 1;
      loadWords();
    });
  });

  // 分页
  dom.btnPrev.addEventListener('click', () => { if (state.page > 1) { state.page--; loadWords(); } });
  dom.btnNext.addEventListener('click', () => { if (state.page < state.totalPages) { state.page++; loadWords(); } });
  dom.btnJump.addEventListener('click', () => {
    const target = parseInt(dom.pageJumpInput.value);
    if (target >= 1 && target <= state.totalPages) { state.page = target; loadWords(); }
  });
  dom.pageJumpInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') dom.btnJump.click(); });

  // 弹窗
  dom.btnCloseModal.addEventListener('click', closeModal);
  dom.modalOverlay.addEventListener('click', (e) => { if (e.target === dom.modalOverlay) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
  dom.modalBtnPrev.addEventListener('click', () => { if (state.modalPage > 1) { state.modalPage--; loadModalCards(); } });
  dom.modalBtnNext.addEventListener('click', () => { if (state.modalPage < state.modalTotalPages) { state.modalPage++; loadModalCards(); } });

  // 导出
  dom.btnExport.addEventListener('click', () => { window.open(buildExportUrl(), '_blank'); });
}

document.addEventListener('DOMContentLoaded', init);
