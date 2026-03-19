// AutoFarm 前端邏輯

const PAGE_SIZE = 20;

const state = {
  articles: [],
  current: null,
  originalSummary: "",
  lastAIText: "",
  polishRound: 0,
  openEditorId: null,
  page: 0,
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const $listView    = document.getElementById("list-view");
const $publishView = document.getElementById("publish-view");
const $articleList  = document.getElementById("article-list");
const $filterTabs      = document.querySelectorAll("[data-filter]");
const $importanceTabs  = document.querySelectorAll("[data-importance]");
const $publishDraft = document.getElementById("publish-draft");
const $toast        = document.getElementById("toast");

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
function showView(view) {
  $listView.classList.toggle("active", view === "list");
  $publishView.classList.toggle("active", view === "publish");
  if (view !== "list") closeEditor();
}

// ---------------------------------------------------------------------------
// Archive (逐篇略過)
// ---------------------------------------------------------------------------
async function archiveArticle(pageId, articleEl) {
  // 淡出動畫
  articleEl.style.opacity = "0.3";
  articleEl.style.pointerEvents = "none";

  // 如果這篇正在編輯，先收合
  if (state.openEditorId === pageId) closeEditor();

  await fetch("/api/articles/batch-status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ page_ids: [pageId], status: "略過" }),
  });

  // 從列表移除
  const editor = articleEl.nextElementSibling;
  if (editor && editor.id === "inline-editor") editor.remove();
  articleEl.remove();

  state.articles = state.articles.filter(a => a.id !== pageId);
  if (!state.articles.length) {
    $articleList.innerHTML = '<p class="loading">沒有文章。</p>';
  }

  toast("已略過");
}

// ---------------------------------------------------------------------------
// Skip All Pending
// ---------------------------------------------------------------------------
async function skipAllPending() {
  if (!confirm("確定要將所有「待審閱」文章標記為略過嗎？")) return;

  const $btn = document.getElementById("skip-all-btn");
  $btn.disabled = true;
  $btn.textContent = "處理中...";

  // 先拉待審閱的文章 ID
  const res = await fetch("/api/articles?status=" + encodeURIComponent("待審閱"));
  const data = await res.json();
  const ids = data.articles.map(a => a.id);

  if (!ids.length) {
    toast("沒有待審閱的文章");
    $btn.disabled = false;
    $btn.textContent = "全部略過";
    return;
  }

  await fetch("/api/articles/batch-status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ page_ids: ids, status: "略過" }),
  });

  toast(`已將 ${ids.length} 篇標記為略過`);
  $btn.disabled = false;
  $btn.textContent = "全部略過";

  const activeFilter = document.querySelector("[data-filter].active");
  loadArticles(activeFilter?.dataset.filter || "");
}

// ---------------------------------------------------------------------------
// Articles list
// ---------------------------------------------------------------------------
async function loadArticles(status = "", importance = "") {
  closeEditor();
  state.page = 0;
  $articleList.innerHTML = '<p class="loading">載入中...</p>';
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (importance) params.set("importance", importance);
  const qs = params.toString();
  const url = qs ? `/api/articles?${qs}` : "/api/articles";
  const res = await fetch(url);
  const data = await res.json();
  state.articles = data.articles;
  renderArticles();
}

function renderArticles() {
  if (!state.articles.length) {
    $articleList.innerHTML = '<p class="loading">沒有文章。</p>';
    return;
  }

  const total = state.articles.length;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  if (state.page >= totalPages) state.page = totalPages - 1;
  if (state.page < 0) state.page = 0;

  const start = state.page * PAGE_SIZE;
  const pageItems = state.articles.slice(start, start + PAGE_SIZE);

  let html = pageItems.map(a => `
    <div class="article-item" data-id="${a.id}">
      <span class="article-title">${esc(a.title)}</span>
      <div class="article-meta">
        <span>${a.source}</span>
        <span>${a.processed}</span>
        ${a.importance ? `<span class="importance-badge ${a.importance}">${a.importance}</span>` : ''}
        <span class="status-badge ${a.status}">${a.status}</span>
        <button class="archive-btn" data-archive-id="${a.id}" title="略過">✕</button>
      </div>
    </div>
  `).join("");

  // 分頁控制列
  if (totalPages > 1) {
    html += `
      <div class="pagination">
        <button class="pagination-btn" id="prev-page" ${state.page === 0 ? "disabled" : ""}>← 上一頁</button>
        <span class="pagination-info">${state.page + 1} / ${totalPages}（共 ${total} 篇）</span>
        <button class="pagination-btn" id="next-page" ${state.page >= totalPages - 1 ? "disabled" : ""}>下一頁 →</button>
      </div>
    `;
  }

  $articleList.innerHTML = html;

  // 綁定點擊展開編輯器
  document.querySelectorAll(".article-item").forEach(el => {
    el.addEventListener("click", (e) => {
      if (e.target.closest(".archive-btn")) return;
      toggleEditor(el.dataset.id, el);
    });
  });

  // 綁定 archive 按鈕
  document.querySelectorAll(".archive-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const item = btn.closest(".article-item");
      archiveArticle(btn.dataset.archiveId, item);
    });
  });

  // 綁定分頁按鈕
  document.getElementById("prev-page")?.addEventListener("click", () => {
    state.page--;
    closeEditor();
    renderArticles();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  document.getElementById("next-page")?.addEventListener("click", () => {
    state.page++;
    closeEditor();
    renderArticles();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// ---------------------------------------------------------------------------
// Inline Editor
// ---------------------------------------------------------------------------
function editorHTML() {
  return `
    <div class="inline-editor" id="inline-editor">
      <div class="editor-header">
        <h2 id="editor-title"></h2>
        <button class="back-btn" id="close-editor-btn">✕ 收合</button>
      </div>

      <div class="editor-columns">
        <div class="editor-col">
          <h3>AI 原稿</h3>
          <div class="original-text" id="original-text"></div>
        </div>
        <div class="editor-col">
          <h3>你的版本</h3>
          <textarea class="edit-textarea" id="edit-textarea"></textarea>
        </div>
      </div>

      <div class="actions">
        <button id="save-btn" class="btn btn-primary">儲存並學習</button>
        <select id="status-select" class="status-select">
          <option value="待審閱">待審閱</option>
          <option value="待發布">待發布</option>
          <option value="略過">略過</option>
        </select>
        <div class="actions-right">
          <span id="polish-round" class="polish-round"></span>
          <button id="polish-btn" class="btn btn-polish">AI 潤稿</button>
        </div>
      </div>

      <div class="feedback-result" id="feedback-result">
        <h3>Feedback 分析</h3>
        <div id="feedback-content"></div>
      </div>
    </div>
  `;
}

function closeEditor() {
  const existing = document.getElementById("inline-editor");
  if (existing) existing.remove();
  state.openEditorId = null;
  state.current = null;
}

async function toggleEditor(pageId, articleEl) {
  if (state.openEditorId === pageId) {
    closeEditor();
    return;
  }

  closeEditor();
  state.openEditorId = pageId;

  articleEl.insertAdjacentHTML("afterend", editorHTML());

  const $editor       = document.getElementById("inline-editor");
  const $editorTitle   = document.getElementById("editor-title");
  const $originalText  = document.getElementById("original-text");
  const $editTextarea  = document.getElementById("edit-textarea");
  const $feedbackResult = document.getElementById("feedback-result");
  const $statusSelect  = document.getElementById("status-select");
  const $saveBtn       = document.getElementById("save-btn");

  const $polishBtn   = document.getElementById("polish-btn");
  const $polishRound = document.getElementById("polish-round");

  document.getElementById("close-editor-btn").addEventListener("click", closeEditor);
  $saveBtn.addEventListener("click", () => saveArticle($editTextarea, $statusSelect, $saveBtn, $feedbackResult, document.getElementById("feedback-content")));
  $polishBtn.addEventListener("click", () => polishArticle($editTextarea, $polishBtn, $polishRound, $feedbackResult, document.getElementById("feedback-content")));

  $editorTitle.textContent = "載入中...";
  const res = await fetch(`/api/articles/${pageId}`);
  const article = await res.json();
  state.current = article;

  const summary = (article.summary || "").replace(/<br\s*\/?>/gi, "\n");
  state.originalSummary = summary;
  state.lastAIText = summary;
  state.polishRound = 0;

  $editorTitle.textContent = article.title;
  $originalText.textContent = summary;
  $editTextarea.value = summary;
  $statusSelect.value = article.status || "待審閱";

  syncHeight($originalText, $editTextarea);
  $editor.scrollIntoView({ behavior: "smooth", block: "start" });
}

function syncHeight($original, $textarea) {
  requestAnimationFrame(() => {
    const h = $original.offsetHeight;
    if (h > 0) {
      $textarea.style.height = h + "px";
    }
  });
}

// ---------------------------------------------------------------------------
// AI 潤稿
// ---------------------------------------------------------------------------
async function polishArticle($textarea, $btn, $roundLabel, $feedbackResult, $feedbackContent) {
  if (!state.current) return;

  $btn.disabled = true;
  $btn.textContent = "潤稿中...";

  const userText = $textarea.value;

  const res = await fetch(`/api/articles/${state.current.id}/polish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: userText,
      previous_ai_text: state.lastAIText,
    }),
  });
  const data = await res.json();

  state.polishRound++;
  state.lastAIText = data.polished;

  // 更新左邊：顯示 AI 潤稿結果 + 輪次標記
  const $originalText = document.getElementById("original-text");
  const $originalLabel = document.querySelector(".editor-col:first-child h3");
  $originalText.textContent = data.polished;
  $originalLabel.textContent = `第 ${state.polishRound} 輪 AI 潤稿`;

  // 右邊也放入潤稿結果，讓使用者繼續修改
  $textarea.value = data.polished;

  $roundLabel.textContent = `第 ${state.polishRound} 輪`;

  // Feedback 累加顯示（每輪追加，不覆蓋）
  if (data.feedback) {
    const roundHeader = `\n──── 第 ${state.polishRound} 輪 feedback ────\n\n`;
    const existing = $feedbackContent.textContent;
    $feedbackContent.textContent = existing + roundHeader + data.feedback;
    $feedbackResult.classList.add("visible");
    toast(`潤稿完成（第 ${state.polishRound} 輪），已學習你的修改`);
  } else {
    toast(`潤稿完成（第 ${state.polishRound} 輪）`);
  }

  // 同步高度
  syncHeight($originalText, $textarea);

  $btn.disabled = false;
  $btn.textContent = "AI 潤稿";
}

// ---------------------------------------------------------------------------
// Save + Feedback
// ---------------------------------------------------------------------------
async function saveArticle($textarea, $select, $btn, $feedbackResult, $feedbackContent) {
  if (!state.current) return;

  $btn.disabled = true;
  $btn.textContent = "儲存中...";

  const edited = $textarea.value;
  $select.value = "待發布";
  const status = $select.value;

  const res = await fetch(`/api/articles/${state.current.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ summary: edited, status }),
  });
  const data = await res.json();

  if (data.feedback) {
    $feedbackContent.textContent = data.feedback;
    $feedbackResult.classList.add("visible");
    toast("已儲存，feedback 已更新 draft-lessons.md");
  } else {
    toast("已儲存（摘要無變動，跳過 feedback）");
  }

  $btn.disabled = false;
  $btn.textContent = "儲存並學習";
}

// ---------------------------------------------------------------------------
// Publish
// ---------------------------------------------------------------------------
async function loadPublish() {
  showView("publish");
  $publishDraft.textContent = "載入中...";
  const res = await fetch("/api/publish", { method: "POST" });
  const data = await res.json();
  $publishDraft.textContent = data.draft;
}

async function copyPublish() {
  const text = $publishDraft.textContent;
  await navigator.clipboard.writeText(text);
  toast("已複製到剪貼簿");
}

// ---------------------------------------------------------------------------
// Utils
// ---------------------------------------------------------------------------
function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function toast(msg) {
  $toast.textContent = msg;
  $toast.classList.add("visible");
  setTimeout(() => $toast.classList.remove("visible"), 2500);
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  // 預設載入「待審閱」
  const defaultTab = document.querySelector('[data-filter="待審閱"]');
  $filterTabs.forEach(b => b.classList.remove("active"));
  if (defaultTab) defaultTab.classList.add("active");
  loadArticles("待審閱");

  $filterTabs.forEach(btn => {
    btn.addEventListener("click", () => {
      showView("list");
      $filterTabs.forEach(b => b.classList.remove("active"));
      $importanceTabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadArticles(btn.dataset.filter, "");
    });
  });

  $importanceTabs.forEach(btn => {
    btn.addEventListener("click", () => {
      showView("list");
      $filterTabs.forEach(b => b.classList.remove("active"));
      $importanceTabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadArticles("", btn.dataset.importance);
    });
  });

  document.getElementById("skip-all-btn").addEventListener("click", skipAllPending);

  document.getElementById("publish-tab").addEventListener("click", loadPublish);
  document.getElementById("copy-btn")?.addEventListener("click", copyPublish);

  document.getElementById("publish-back-btn")?.addEventListener("click", () => {
    showView("list");
  });
});
