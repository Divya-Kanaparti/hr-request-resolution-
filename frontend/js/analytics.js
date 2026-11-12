/**
 * Analytics and Anomaly Radar Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("analytics-view")) {
    initAnalyticsPage();
  }
});

async function initAnalyticsPage() {
  await loadSummaryStats();
  await loadCategoryTrends();
  await loadAgentWorkload();
  await loadAnomaliesList();
  await loadAuditLogs();

  document.getElementById("btn-run-anomaly-scan")?.addEventListener("click", triggerAnomalyScan);
}

async function loadSummaryStats() {
  try {
    const summary = await api.get("/analytics/summary");
    document.getElementById("an-total-tickets").textContent = summary.total_tickets;
    document.getElementById("an-resolved-tickets").textContent = summary.resolved_tickets;
    document.getElementById("an-sla-compliance").textContent = `${summary.sla_compliance_rate}%`;
    document.getElementById("an-avg-resolution").textContent = `${summary.avg_resolution_hours}h`;
    document.getElementById("an-total-anomalies").textContent = summary.total_anomalies;
  } catch (err) {
    console.error("Failed to load analytics summary:", err);
  }
}

async function loadCategoryTrends() {
  try {
    const trends = await api.get("/analytics/category-trends");
    const container = document.getElementById("category-trends-container");
    if (!container) return;

    container.innerHTML = trends.map(item => `
      <div style="margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:600; margin-bottom:4px;">
          <span>${escapeHtml(item.category_name)}</span>
          <span>${item.ticket_count} (${item.percentage}%)</span>
        </div>
        <div style="height:10px; background:var(--gray-200); border-radius:9999px; overflow:hidden;">
          <div style="width:${item.percentage}%; height:100%; background:linear-gradient(90deg, var(--primary), var(--accent));"></div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load category trends:", err);
  }
}

async function loadAgentWorkload() {
  try {
    const workload = await api.get("/analytics/agent-workload");
    const tbody = document.getElementById("agent-workload-tbody");
    if (!tbody) return;

    if (workload.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:16px;">No agent data available.</td></tr>`;
      return;
    }

    tbody.innerHTML = workload.map(ag => `
      <tr>
        <td><strong>${escapeHtml(ag.agent_name)}</strong></td>
        <td><span class="badge badge-medium">${ag.active_tickets} active</span></td>
        <td>${ag.resolved_tickets}</td>
        <td>${ag.avg_rating ? `&#9733; ${ag.avg_rating}` : 'N/A'}</td>
        <td>${ag.breached_count > 0 ? `<span class="badge" style="background:#fee2e2; color:#b91c1c;">${ag.breached_count}</span>` : '0'}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Failed to load agent workload:", err);
  }
}

async function loadAnomaliesList() {
  try {
    const anomalies = await api.get("/anomalies?limit=50");
    const tbody = document.getElementById("anomalies-tbody");
    if (!tbody) return;

    if (anomalies.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--gray-500);">No anomalies currently flagged. Click 'Run Anomaly Scan' to check.</td></tr>`;
      return;
    }

    tbody.innerHTML = anomalies.map(a => {
      const isResolved = a.status === "RESOLVED";
      const statusBadge = isResolved
        ? `<span class="badge badge-resolved">RESOLVED</span>`
        : `<span class="badge badge-urgent">${a.status}</span>`;

      return `
        <tr>
          <td><strong>${a.anomaly_id}</strong></td>
          <td><span class="badge badge-high">${a.anomaly_type.replace(/_/g, " ")}</span></td>
          <td><span class="badge badge-${a.severity.toLowerCase()}">${a.severity}</span></td>
          <td style="font-size:0.85rem;">${escapeHtml(a.description)}</td>
          <td>${statusBadge}</td>
          <td>
            ${!isResolved ? `<button class="btn btn-secondary btn-sm" onclick="resolveAnomalyPrompt('${a.anomaly_id}')">Resolve</button>` : '&mdash;'}
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load anomalies:", err);
  }
}

async function triggerAnomalyScan() {
  const btn = document.getElementById("btn-run-anomaly-scan");
  if (btn) btn.disabled = true;
  api.showToast("Running anomaly scan across all tickets...", "info");

  try {
    const scanned = await api.post("/anomalies/scan", {});
    api.showToast(`Anomaly scan completed! Flagged ${scanned.length} issues.`);
    await loadAnomaliesList();
    await loadSummaryStats();
  } catch (err) {
    console.error("Anomaly scan failed:", err);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function resolveAnomalyPrompt(anomalyId) {
  const comment = prompt("Enter resolution notes for this anomaly:");
  if (comment === null) return;

  try {
    await api.put(`/anomalies/${anomalyId}/resolve`, {
      status: "RESOLVED",
      resolution_comment: comment || "Resolved by Compliance Officer"
    });
    api.showToast("Anomaly marked as RESOLVED");
    await loadAnomaliesList();
  } catch (err) {
    console.error("Failed to resolve anomaly:", err);
  }
}
window.resolveAnomalyPrompt = resolveAnomalyPrompt;

async function loadAuditLogs() {
  try {
    const logs = await api.get("/audit?limit=20");
    const tbody = document.getElementById("audit-tbody");
    if (!tbody) return;

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:16px;">No audit logs recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => `
      <tr>
        <td><strong>${l.audit_id}</strong></td>
        <td>${escapeHtml(l.entity_type)} &bull; ${escapeHtml(l.action)}</td>
        <td>${escapeHtml(l.actor_name || "System")}</td>
        <td style="font-size:0.8rem; font-family:monospace;">${escapeHtml(JSON.stringify(l.details_json || {}))}</td>
        <td>${new Date(l.created_at).toLocaleString()}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

