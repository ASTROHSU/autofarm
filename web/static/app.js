// AutoFarm 前端邏輯

const state = {
  articles: [],
  current: null,
  originalSummary: "",
  openEditorId: null,
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const $listView    = document.getElementById("list-view");
const $publishView = document.getElementById("publish-view");
const $articleList  = document.getElementById("article-list");
const $filterTabs   = document.querySelectorAll("[data-filter]");
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
// Articles list
// ---------------------------------------------------------------------------
async function loadArticles(status = "") {
  closeEditor();
  $articleList.innerHTML = '<p class="loading">載入中...</p>';
  const url = status ? `/api/articles?status=${encodeURIComponent(status)}` : "/api/articles";
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
  $articleList.innerHTML = state.articles.map(a => `
    <div class="article-item" data-id="${a.id}">
      <span class="article-title">${esc(a.title)}</span>
      <div class="article-meta">
        <span>${a.source}</span>
        <span>${a.processed}</span>
        <span class="status-badge ${a.status}">${a.status}</span>
        <button class="archive-btn" data-archive-id="${a.id}" title="略過">✕</button>
      </div>
    </div>
  `).join("");

  // 綁定點擊展開編輯器
  document.querySelectorAll(".article-item").forEach(el => {
    el.addEventListener("click", (e) => {
      // 點到 archive 按鈕時不開編輯器
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

      <div id="discussion-section" class="discussion-box" style="display:none">
        <h3>討論</h3>
        <div id="discussion-content"></div>
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
          <option value="已發布">已發布</option>
          <option value="略過">略過</option>
        </select>
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
  const $discussionBox = document.getElementById("discussion-content");
  const $discussionSection = document.getElementById("discussion-section");
  const $feedbackResult = document.getElementById("feedback-result");
  const $statusSelect  = document.getElementById("status-select");
  const $saveBtn       = document.getElementById("save-btn");

  document.getElementById("close-editor-btn").addEventListener("click", closeEditor);
  $saveBtn.addEventListener("click", () => saveArticle($editTextarea, $statusSelect, $saveBtn, $feedbackResult, document.getElementById("feedback-content")));

  $editorTitle.textContent = "載入中...";
  const res = await fetch(`/api/articles/${pageId}`);
  const article = await res.json();
  state.current = article;

  const summary = (article.summary || "").replace(/<br\s*\/?>/gi, "\n");
  state.originalSummary = summary;

  $editorTitle.textContent = article.title;
  $originalText.textContent = summary;
  $editTextarea.value = summary;
  $statusSelect.value = article.status || "待審閱";

  const discussion = (article.discussion || "").replace(/<br\s*\/?>/gi, "\n");
  if (discussion.trim()) {
    $discussionBox.textContent = discussion;
    $discussionSection.style.display = "block";
  } else {
    $discussionSection.style.display = "none";
  }

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
// Save + Feedback
// ---------------------------------------------------------------------------
async function saveArticle($textarea, $select, $btn, $feedbackResult, $feedbackContent) {
  if (!state.current) return;

  $btn.disabled = true;
  $btn.textContent = "儲存中...";

  const edited = $textarea.value;
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
  loadArticles();

  $filterTabs.forEach(btn => {
    btn.addEventListener("click", () => {
      $filterTabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadArticles(btn.dataset.filter);
    });
  });

  document.getElementById("publish-tab").addEventListener("click", loadPublish);
  document.getElementById("copy-btn")?.addEventListener("click", copyPublish);

  document.getElementById("publish-back-btn")?.addEventListener("click", () => {
    showView("list");
  });
});
