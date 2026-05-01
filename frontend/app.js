/**
 * PaperMind Frontend — 论文深度分析 Agent
 * 功能: 单篇分析 | 批量并发 | 对比分析
 * 通信: SSE流式 + WebSocket进度推送
 */

const API = window.location.origin;  // 同源或可改为 http://localhost:8000
let currentMode = 'standard';
let currentInput = 'text';
let sessionId = crypto.randomUUID();
let ws = null;
let queue = [];        // 批量队列
let compareSlots = []; // 对比槽

// ═══════════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initInputTabs();
  initModeButtons();
  initAnalyzeButton();
  initPdfDrop();
  initBatch();
  initCompare();
  initResultActions();
  checkApiStatus();
  initWebSocket();
  addDefaultCompareSlots(2);
});

// ── API 状态检测 ───────────────────────────────────
async function checkApiStatus() {
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) setStatus(true);
    else setStatus(false);
  } catch { setStatus(false); }
}
function setStatus(ok) {
  const dot  = document.getElementById('apiStatus');
  const text = document.getElementById('apiStatusText');
  dot.className = `status-dot ${ok ? 'ok' : 'err'}`;
  text.textContent = ok ? '已连接' : '服务离线';
}

// ── WebSocket ──────────────────────────────────────
function initWebSocket() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  try {
    ws = new WebSocket(`${proto}//${location.host}/ws/${sessionId}`);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      handleWsMessage(data);
    };
    ws.onclose = () => { ws = null; };
    ws.onerror = () => { ws = null; };
  } catch (e) { ws = null; }
}
function handleWsMessage(data) {
  if (data.type === 'paper_start') updateBatchItemStatus(data.index, 'processing');
  if (data.type === 'paper_done')  updateBatchItemStatus(data.index, data.status, data.elapsed_s);
  if (data.type === 'batch_complete') renderBatchResults(data.results);
}

// ═══════════════════════════════════════════════════
// Tab 导航
// ═══════════════════════════════════════════════════
function initNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${tab}`).classList.add('active');
    });
  });
}

// ═══════════════════════════════════════════════════
// 单篇分析 — 输入控制
// ═══════════════════════════════════════════════════
function initInputTabs() {
  document.querySelectorAll('.itab').forEach(btn => {
    btn.addEventListener('click', () => {
      currentInput = btn.dataset.input;
      document.querySelectorAll('.itab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.input-area').forEach(a => a.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`input-${currentInput}`).classList.add('active');
    });
  });

  // 字符计数
  const ta = document.getElementById('paperText');
  ta.addEventListener('input', () => {
    document.getElementById('charCount').textContent = ta.value.length.toLocaleString();
  });
}

function initModeButtons() {
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentMode = btn.dataset.mode;
      document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      // 深度模式显示维度选择
      document.getElementById('dimensionGroup').style.display =
        currentMode === 'deep' ? '' : 'none';
    });
  });
}

// ── PDF Drop Zone ──────────────────────────────────
function initPdfDrop() {
  const zone = document.getElementById('dropZone');
  const input = document.getElementById('pdfFile');
  const info  = document.getElementById('fileInfo');

  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('over'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('over');
    const file = e.dataTransfer.files[0];
    if (file) showFileInfo(file, info);
  });
  input.addEventListener('change', () => {
    if (input.files[0]) showFileInfo(input.files[0], info);
  });
}
function showFileInfo(file, el) {
  el.textContent = `📄 ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
  el.style.display = '';
  document.getElementById('dropZone').querySelector('.drop-text').textContent = file.name;
}

// ═══════════════════════════════════════════════════
// 单篇分析 — 核心
// ═══════════════════════════════════════════════════
function initAnalyzeButton() {
  document.getElementById('analyzeBtn').addEventListener('click', startAnalysis);
}

async function startAnalysis() {
  const btn  = document.getElementById('analyzeBtn');
  const body = document.getElementById('resultBody');
  const footer = document.getElementById('resultFooter');
  const actions = document.getElementById('resultActions');

  let fetchPromise;

  if (currentInput === 'text') {
    const text = document.getElementById('paperText').value.trim();
    if (!text) { toast('请输入论文内容'); return; }
    fetchPromise = fetchSSE(`${API}/api/analyze/text`, {
      text, mode: currentMode, dimensions: getSelectedDimensions(), session_id: sessionId
    });
  } else if (currentInput === 'url') {
    const url = document.getElementById('paperUrl').value.trim();
    if (!url) { toast('请输入论文URL'); return; }
    fetchPromise = fetchSSE(`${API}/api/analyze/url`, {
      url, mode: currentMode, dimensions: getSelectedDimensions(), session_id: sessionId
    });
  } else {
    const file = document.getElementById('pdfFile').files[0];
    if (!file) { toast('请选择PDF文件'); return; }
    fetchPromise = fetchSSEFile(`${API}/api/analyze/pdf`, file, currentMode);
  }

  // UI 状态
  btn.disabled = true;
  btn.classList.add('loading');
  btn.querySelector('.btn-text').textContent = '分析中...';
  body.innerHTML = '<div class="md-content"><span class="cursor"></span></div>';
  actions.style.display = 'none';
  footer.style.display = 'none';

  const startTime = Date.now();
  let fullText = '';

  try {
    await fetchPromise(
      (delta) => {
        fullText += delta;
        const el = body.querySelector('.md-content');
        if (el) el.innerHTML = renderMarkdown(fullText) + '<span class="cursor"></span>';
        body.scrollTop = body.scrollHeight;
      },
      () => {
        // Done
        const el = body.querySelector('.md-content');
        if (el) el.innerHTML = renderMarkdown(fullText);
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        document.getElementById('timeInfo').textContent = `⏱ ${elapsed}s`;
        document.getElementById('tokenInfo').textContent = `📝 ${fullText.length.toLocaleString()} chars`;
        footer.style.display = '';
        actions.style.display = '';
        window._lastResult = fullText;
      },
      (err) => {
        body.innerHTML = `<div style="color:var(--red);padding:20px">❌ ${err}</div>`;
      }
    );
  } finally {
    btn.disabled = false;
    btn.classList.remove('loading');
    btn.querySelector('.btn-text').textContent = '开始分析';
  }
}

function getSelectedDimensions() {
  return [...document.querySelectorAll('.dim-check input:checked')].map(el => el.value);
}

// ── SSE 流处理 ─────────────────────────────────────
function fetchSSE(url, body) {
  return (onDelta, onDone, onErr) => streamSSE(
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
    onDelta, onDone, onErr
  );
}

function fetchSSEFile(url, file, mode) {
  return (onDelta, onDone, onErr) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('mode', mode);
    return streamSSE(
      fetch(url, { method: 'POST', body: fd }),
      onDelta, onDone, onErr
    );
  };
}

async function streamSSE(fetchPromise, onDelta, onDone, onErr) {
  let resp;
  try { resp = await fetchPromise; } catch (e) { onErr(e.message); return; }
  if (!resp.ok) { onErr(`HTTP ${resp.status}: ${await resp.text()}`); return; }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split('\n\n');
    buf = parts.pop();
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith('data:')) continue;
      const raw = line.slice(5).trim();
      if (raw === '[DONE]') { onDone(); return; }
      try {
        const obj = JSON.parse(raw);
        if (obj.type === 'delta') onDelta(obj.content);
        if (obj.type === 'error') { onErr(obj.content); return; }
        if (obj.type === 'done')  { onDone(); return; }
      } catch {}
    }
  }
  onDone();
}

// ═══════════════════════════════════════════════════
// 结果操作按钮
// ═══════════════════════════════════════════════════
function initResultActions() {
  document.getElementById('copyBtn').addEventListener('click', () => {
    if (window._lastResult) {
      navigator.clipboard.writeText(window._lastResult).then(() => toast('已复制到剪贴板'));
    }
  });
  document.getElementById('exportMdBtn').addEventListener('click', () => {
    if (window._lastResult) downloadText(window._lastResult, 'paper-analysis.md');
  });
  document.getElementById('clearBtn').addEventListener('click', () => {
    document.getElementById('resultBody').innerHTML = `
      <div class="placeholder">
        <div class="placeholder-icon">◈</div>
        <div class="placeholder-title">等待分析</div>
        <div class="placeholder-desc">输入论文内容，选择分析深度，点击开始</div>
      </div>`;
    document.getElementById('resultActions').style.display = 'none';
    document.getElementById('resultFooter').style.display = 'none';
    window._lastResult = null;
  });
}

// ═══════════════════════════════════════════════════
// 批量分析
// ═══════════════════════════════════════════════════
function initBatch() {
  document.getElementById('addPaperBtn').addEventListener('click', addToQueue);
  document.getElementById('batchAnalyzeBtn').addEventListener('click', startBatchAnalysis);
}

function addToQueue() {
  const text  = document.getElementById('batchText').value.trim();
  const title = document.getElementById('batchTitle').value.trim() || `论文 ${queue.length + 1}`;
  if (!text) { toast('请输入论文内容'); return; }
  queue.push({ text, title });
  document.getElementById('batchText').value = '';
  document.getElementById('batchTitle').value = '';
  renderQueue();
}

function renderQueue() {
  const list = document.getElementById('queueList');
  const count = document.getElementById('queueCount');
  const btn   = document.getElementById('batchAnalyzeBtn');

  count.textContent = queue.length;
  btn.disabled = queue.length === 0;

  if (!queue.length) {
    list.innerHTML = '<div class="queue-empty">队列为空，请先添加论文</div>';
    return;
  }
  list.innerHTML = queue.map((p, i) => `
    <div class="queue-item" data-idx="${i}">
      <div>
        <div class="queue-item-title">${esc(p.title)}</div>
        <div class="queue-item-meta">${p.text.length.toLocaleString()} 字符</div>
      </div>
      <button class="queue-item-del" onclick="removeFromQueue(${i})">✕</button>
    </div>
  `).join('');
}

function removeFromQueue(i) {
  queue.splice(i, 1);
  renderQueue();
}

async function startBatchAnalysis() {
  if (!queue.length) return;
  const mode = document.getElementById('batchMode').value;

  // 显示进度
  document.getElementById('batchProgress').style.display = '';
  document.getElementById('progressBar').style.width = '0%';
  document.getElementById('progressText').textContent = `正在分析 0 / ${queue.length}…`;

  // 渲染占位卡片
  const list = document.getElementById('batchResultList');
  list.innerHTML = queue.map((p, i) => `
    <div class="batch-result-item" id="bri-${i}">
      <div class="batch-result-header" onclick="toggleBatchItem(${i})">
        <div class="batch-result-status processing" id="brs-${i}"></div>
        <div class="batch-result-title">${esc(p.title)}</div>
        <div class="batch-result-time" id="brt-${i}">处理中...</div>
      </div>
      <div class="batch-result-body" id="brb-${i}"></div>
    </div>
  `).join('');

  // 前端并发处理（最多5个）
  const sem = new Semaphore(5);
  let done = 0;

  const tasks = queue.map((paper, i) =>
    sem.run(async () => {
      updateBatchItemStatus(i, 'processing');
      let content = '';
      const start = Date.now();

      await streamSSE(
        fetch(`${API}/api/analyze/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: paper.text, mode, session_id: sessionId }),
        }),
        (delta) => { content += delta; },
        () => {},
        (err) => { content = `错误: ${err}`; }
      );

      const elapsed = ((Date.now() - start) / 1000).toFixed(1);
      updateBatchItemStatus(i, 'done', elapsed);
      document.getElementById(`brb-${i}`).innerHTML = `<div class="md-content">${renderMarkdown(content)}</div>`;

      done++;
      const pct = Math.round((done / queue.length) * 100);
      document.getElementById('progressBar').style.width = `${pct}%`;
      document.getElementById('progressText').textContent = `已完成 ${done} / ${queue.length}`;
    })
  );

  await Promise.all(tasks);
  document.getElementById('progressText').textContent = `全部完成 ✓  共 ${queue.length} 篇`;
}

function updateBatchItemStatus(i, status, elapsed) {
  const dot  = document.getElementById(`brs-${i}`);
  const time = document.getElementById(`brt-${i}`);
  if (dot)  dot.className = `batch-result-status ${status}`;
  if (time) time.textContent = elapsed ? `${elapsed}s` : (status === 'processing' ? '分析中...' : '');
}

function toggleBatchItem(i) {
  const body = document.getElementById(`brb-${i}`);
  if (body) body.classList.toggle('open');
}

// 简易信号量
class Semaphore {
  constructor(n) { this.n = n; this.q = []; }
  async run(fn) {
    if (this.n > 0) { this.n--; }
    else await new Promise(r => this.q.push(r));
    try { return await fn(); }
    finally {
      if (this.q.length) { this.q.shift()(); }
      else { this.n++; }
    }
  }
}

// ═══════════════════════════════════════════════════
// 对比分析
// ═══════════════════════════════════════════════════
function initCompare() {
  document.getElementById('addSlotBtn').addEventListener('click', () => {
    addCompareSlot();
    renderCompareSlots();
  });
  document.getElementById('compareAnalyzeBtn').addEventListener('click', startCompare);
}

function addDefaultCompareSlots(n) {
  for (let i = 0; i < n; i++) addCompareSlot();
  renderCompareSlots();
}

function addCompareSlot() {
  compareSlots.push({ title: '', text: '' });
}

function renderCompareSlots() {
  const container = document.getElementById('compareSlots');
  container.innerHTML = compareSlots.map((s, i) => `
    <div class="compare-slot">
      <div class="compare-slot-header">
        <span class="compare-slot-label">论文 ${i + 1}</span>
        ${i >= 2 ? `<button class="compare-slot-del" onclick="removeCompareSlot(${i})">✕</button>` : ''}
      </div>
      <textarea placeholder="粘贴第${i+1}篇论文文本…"
        oninput="compareSlots[${i}].text=this.value">${esc(s.text)}</textarea>
      <input type="text" placeholder="标题（选填）"
        value="${esc(s.title)}"
        oninput="compareSlots[${i}].title=this.value">
    </div>
  `).join('');
}

function removeCompareSlot(i) {
  compareSlots.splice(i, 1);
  renderCompareSlots();
}

async function startCompare() {
  const papers = compareSlots.filter(s => s.text.trim());
  if (papers.length < 2) { toast('至少需要2篇论文'); return; }

  const body = document.getElementById('compareResultBody');
  body.innerHTML = '<div class="md-content"><span class="cursor"></span></div>';

  let fullText = '';
  await streamSSE(
    fetch(`${API}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ papers }),
    }),
    (delta) => {
      fullText += delta;
      const el = body.querySelector('.md-content');
      if (el) el.innerHTML = renderMarkdown(fullText) + '<span class="cursor"></span>';
      body.scrollTop = body.scrollHeight;
    },
    () => {
      const el = body.querySelector('.md-content');
      if (el) el.innerHTML = renderMarkdown(fullText);
    },
    (err) => {
      body.innerHTML = `<div style="color:var(--red);padding:20px">❌ ${err}</div>`;
    }
  );
}

// ═══════════════════════════════════════════════════
// Markdown 渲染
// ═══════════════════════════════════════════════════
function renderMarkdown(md) {
  if (!md) return '';
  let html = md
    // Headers
    .replace(/^#{1} (.+)$/gm, '<h1>$1</h1>')
    .replace(/^#{2} (.+)$/gm, '<h2>$1</h2>')
    .replace(/^#{3} (.+)$/gm, '<h3>$1</h3>')
    // Bold & Italic
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Code
    .replace(/```[\w]*\n?([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // HR
    .replace(/^---+$/gm, '<hr>')
    // Blockquote
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    // Tables (basic)
    .replace(/^\|(.+)\|$/gm, (m) => {
      const cells = m.slice(1,-1).split('|').map(c => c.trim());
      return '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
    })
    // Lists
    .replace(/^[\*\-] (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Paragraphs
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  // Wrap li groups
  html = html.replace(/(<li>.*?<\/li>(\s*<br>)*)+/g, m => `<ul>${m}</ul>`);
  // Wrap table rows
  html = html.replace(/(<tr>.*?<\/tr>(\s*<br>)*)+/g, m => `<table>${m}</table>`);

  return `<p>${html}</p>`;
}

// ═══════════════════════════════════════════════════
// 工具函数
// ═══════════════════════════════════════════════════
function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function toast(msg, dur = 2500) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), dur);
}

function downloadText(content, filename) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function renderBatchResults(results) {
  // Handled by per-paper streaming
}
