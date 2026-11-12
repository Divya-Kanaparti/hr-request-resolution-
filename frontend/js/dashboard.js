/**
 * Dashboard Controller
 * Loads KPIs, SLA Status, and Recent Tickets.
 */

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("dashboard-view")) {
    loadDashboard();
  }
});

async function loadDashboard() {
  const user = api.getCurrentUser();
  if (!user) return;

  const isHr = ["HR_AGENT", "HR_MANAGER", "ADMIN", "COMPLIANCE_OFFICER"].includes(user.role);

  try {
    // 1. Load KPI metrics
    if (isHr) {
      const summary = await api.get("/analytics/summary");
      document.getElementById("stat-total-tickets").textContent = summary.total_tickets;
      document.getElementById("stat-open-tickets").textContent = summary.open_tickets;
      document.getElementById("stat-sla-rate").textContent = `${summary.sla_compliance_rate}%`;
      document.getElementById("stat-avg-hours").textContent = `${summary.avg_resolution_hours}h`;

      const anomEl = document.getElementById("stat-anomalies");
      if (anomEl) anomEl.textContent = summary.total_anomalies;
    } else {
      // Employee specific counts
      const tickets = await api.get("/tickets");
      const openCount = tickets.filter(t => !["RESOLVED", "CLOSED"].includes(t.status)).length;
      const resolvedCount = tickets.filter(t => ["RESOLVED", "CLOSED"].includes(t.status)).length;

      document.getElementById("stat-total-tickets").textContent = tickets.length;
      document.getElementById("stat-open-tickets").textContent = openCount;
      document.getElementById("stat-sla-rate").textContent = `${tickets.length ? Math.round((resolvedCount/tickets.length)*100) : 100}%`;
      document.getElementById("stat-avg-hours").textContent = "N/A";
    }

    // 2. Load Recent Tickets
    const recentTickets = await api.get("/tickets?limit=8");
    renderRecentTicketsTable(recentTickets);

  } catch (err) {
    console.error("Failed to load dashboard data:", err);
  }
}

function renderRecentTicketsTable(tickets) {
  const tbody = document.getElementById("recent-tickets-tbody");
  if (!tbody) return;

  if (tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 24px; color: var(--gray-500);">No requests found. Click 'Submit HR Request' to get started.</td></tr>`;
    return;
  }

  tbody.innerHTML = tickets.map(t => {
    const isBreached = t.sla_status === "BREACHED";
    const slaBadge = isBreached
      ? `<span class="badge" style="background:#fee2e2; color:#b91c1c;">BREACHED</span>`
      : `<span class="badge" style="background:#ecfdf5; color:#047857;">ON TRACK</span>`;

    const sensitiveBadge = t.is_sensitive
      ? `<span class="badge badge-sensitive" title="Confidential Request">SENSITIVE</span>`
      : "";

    return `
      <tr>
        <td><strong>${t.tracking_number}</strong></td>
        <td>
          <a href="tickets.html?id=${t.ticket_id}" style="color:var(--primary); font-weight:600; text-decoration:none;">
            ${escapeHtml(t.title)}
          </a>
          ${sensitiveBadge}
        </td>
        <td>${escapeHtml(t.category_name || "General")}</td>
        <td><span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span></td>
        <td><span class="badge badge-${t.status.toLowerCase()}">${t.status.replace("_", " ")}</span></td>
        <td>${slaBadge}</td>
        <td>
          <a href="tickets.html?id=${t.ticket_id}" class="btn btn-secondary btn-sm">View</a>
        </td>
      </tr>
    `;
  }).join("");
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

