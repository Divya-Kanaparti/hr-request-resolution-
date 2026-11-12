/**
 * Policies & AI Policy Assistant Controller
 * Explores version-controlled documents and executes RAG questions with exact citations.
 */

let allPolicies = [];

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("policies-view")) {
    initPoliciesPage();
  }
});

async function initPoliciesPage() {
  await loadPolicies();
  document.getElementById("policy-search")?.addEventListener("input", filterPolicies);

  // Quick RAG question chips
  document.querySelectorAll(".quick-rag-query").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById("rag-query-input");
      if (input) {
        input.value = btn.textContent.replace(/[“"]/g, "").trim();
        handleAskRAG();
      }
    });
  });
}

async function loadPolicies() {
  try {
    allPolicies = await api.get("/policies");
    renderPoliciesList(allPolicies);
  } catch (err) {
    console.error("Failed to load policies:", err);
  }
}

function filterPolicies() {
  const term = (document.getElementById("policy-search")?.value || "").toLowerCase();
  const filtered = allPolicies.filter(p => {
    return p.title.toLowerCase().includes(term) ||
      p.doc_code.toLowerCase().includes(term) ||
      (p.category_name && p.category_name.toLowerCase().includes(term));
  });
  renderPoliciesList(filtered);
}

function renderPoliciesList(policies) {
  const container = document.getElementById("policies-container");
  if (!container) return;

  if (policies.length === 0) {
    container.innerHTML = `<div style="padding:32px; text-align:center; color:var(--gray-500);">No corporate policies found.</div>`;
    return;
  }

  container.innerHTML = policies.map(p => {
    const activeVersion = p.versions?.find(v => v.status === "ACTIVE") || p.versions?.[0];
    const versionBadges = (p.versions || []).map(v => `
      <span class="badge ${v.status === 'ACTIVE' ? 'badge-resolved' : 'badge-low'}" style="margin-right:4px;">
        v${v.version_number} (${v.status})
      </span>
    `).join("");

    const articlesCount = (p.versions || []).reduce((acc, v) => acc + (v.articles?.length || 0), 0);

    return `
      <div class="card" style="margin-bottom:20px;">
        <div class="card-header">
          <div>
            <div style="font-size:0.78rem; font-weight:700; color:var(--accent); text-transform:uppercase;">
              ${escapeHtml(p.doc_code)} &bull; ${escapeHtml(p.category_name || "General")}
            </div>
            <h3 style="font-size:1.15rem; font-weight:700; color:var(--gray-900); margin-top:2px;">
              ${escapeHtml(p.title)}
            </h3>
          </div>
          <div>${versionBadges}</div>
        </div>
        <div class="card-body">
          <p style="color:var(--gray-600); font-size:0.92rem; margin-bottom:16px;">
            ${escapeHtml(activeVersion?.summary || "Policy documentation summary")}
          </p>
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div style="font-size:0.8rem; color:var(--gray-500);">
              Audience: <strong>${escapeHtml(p.audience)}</strong> &bull; Articles: <strong>${articlesCount}</strong>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="viewPolicyArticles('${p.policy_id}')">
              Browse Articles & History
            </button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// Interactive Policy Q&A with Exact Citations (RAG)
async function handleAskRAG() {
  const input = document.getElementById("rag-query-input");
  const query = input?.value.trim();
  if (!query) return;

  const resultContainer = document.getElementById("rag-result-container");
  const answerEl = document.getElementById("rag-answer-text");
  const citationsEl = document.getElementById("rag-citations-list");
  const modelEl = document.getElementById("rag-model-badge");

  if (!resultContainer) return;

  resultContainer.style.display = "block";
  answerEl.innerHTML = `<span style="color:var(--gray-500);">Searching active policy versions and knowledge articles...</span>`;
  citationsEl.innerHTML = "";

  try {
    const res = await api.post("/rag/ask", { query, top_k: 3 });

    answerEl.innerHTML = escapeHtml(res.answer).replace(/\n/g, "<br>");
    if (modelEl) modelEl.textContent = `Engine: ${res.model_used} (Confidence: ${Math.round(res.confidence_score * 100)}%)`;

    if (res.citations && res.citations.length > 0) {
      citationsEl.innerHTML = res.citations.map(c => `
        <div style="padding:12px; background:var(--gray-50); border-left:3px solid var(--accent); border-radius:var(--radius-sm); margin-bottom:8px;">
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-weight:700; color:var(--primary); margin-bottom:4px;">
            <span>${escapeHtml(c.policy_doc_code)} (v${c.version_number}) - ${escapeHtml(c.section_number)}: ${escapeHtml(c.article_title)}</span>
            <span>Match: ${Math.round(c.relevance_score * 100)}%</span>
          </div>
          <div style="font-size:0.85rem; color:var(--gray-700); font-style:italic;">
            "${escapeHtml(c.quote)}"
          </div>
        </div>
      `).join("");
    } else {
      citationsEl.innerHTML = `<div style="font-size:0.82rem; color:var(--gray-500);">No specific citation excerpts found.</div>`;
    }
  } catch (err) {
    answerEl.textContent = "Failed to retrieve policy answer. Please verify backend connectivity.";
  }
}
window.handleAskRAG = handleAskRAG;

// View articles modal
function viewPolicyArticles(policyId) {
  const p = allPolicies.find(item => item.policy_id === policyId);
  if (!p) return;

  document.getElementById("modal-policy-title").textContent = `${p.doc_code}: ${p.title}`;
  const listEl = document.getElementById("modal-articles-list");

  const activeV = p.versions?.find(v => v.status === "ACTIVE") || p.versions?.[0];
  if (!activeV || !activeV.articles || activeV.articles.length === 0) {
    listEl.innerHTML = `<p style="color:var(--gray-500); padding:16px;">No articles attached to active version.</p>`;
  } else {
    listEl.innerHTML = activeV.articles.map(a => `
      <div style="padding:16px; border:1px solid var(--gray-200); border-radius:var(--radius-sm); margin-bottom:12px;">
        <div style="font-weight:700; color:var(--gray-900); margin-bottom:4px;">
          ${escapeHtml(a.section_number)}: ${escapeHtml(a.title)}
        </div>
        <p style="font-size:0.9rem; color:var(--gray-700); line-height:1.5;">
          ${escapeHtml(a.content)}
        </p>
        <div style="font-size:0.75rem; color:var(--gray-500); margin-top:8px;">
          Keywords: ${escapeHtml(a.keywords || "None")}
        </div>
      </div>
    `).join("");
  }

  const modal = document.getElementById("modal-view-articles");
  if (modal) modal.classList.add("active");
}
window.viewPolicyArticles = viewPolicyArticles;

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

