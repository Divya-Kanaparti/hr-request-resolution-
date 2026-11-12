/**
 * Tickets Controller
 * Complete Workflow: Submission, AI Pre-check, Filtering, Detail Modal, Messaging, Resolution.
 */

let allTickets = [];
let activeTicketId = null;
let currentTicketDetail = null;

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("tickets-view")) {
    initTicketsPage();
  }
});

async function initTicketsPage() {
  await loadCategoriesDropdown();
  await loadTickets();

  // Search and filter listeners
  document.getElementById("ticket-search")?.addEventListener("input", filterAndRenderTickets);
  document.getElementById("filter-status")?.addEventListener("change", filterAndRenderTickets);
  document.getElementById("filter-category")?.addEventListener("change", filterAndRenderTickets);
  document.getElementById("filter-priority")?.addEventListener("change", filterAndRenderTickets);

  // Check URL params for ticket ID
  const urlParams = new URLSearchParams(window.location.search);
  const ticketIdParam = urlParams.get("id");
  if (ticketIdParam) {
    openTicketDetail(ticketIdParam);
  }

  // Pre-classification listener on create modal
  const titleInput = document.getElementById("create-title");
  const descInput = document.getElementById("create-desc");
  if (titleInput && descInput) {
    const runAIPrecheck = debounce(async () => {
      const t = titleInput.value.trim();
      const d = descInput.value.trim();
      if (t.length > 5 || d.length > 10) {
        try {
          const res = await api.post("/tickets/classify", { title: t, description: d });
          const badge = document.getElementById("ai-category-badge");
          if (badge) {
            badge.textContent = `AI Suggested: ${res.category_name} (${Math.round(res.confidence * 100)}% match)`;
            badge.style.display = "inline-block";
          }
          if (res.is_sensitive) {
            const sensBadge = document.getElementById("ai-sensitive-badge");
            if (sensBadge) sensBadge.style.display = "inline-block";
          }
        } catch (e) {
          // Silent fallback
        }
      }
    }, 400);

    titleInput.addEventListener("input", runAIPrecheck);
    descInput.addEventListener("input", runAIPrecheck);
  }
}

async function loadCategoriesDropdown() {
  try {
    const categories = await api.get("/categories");
    const dropdown = document.getElementById("create-category");
    const filterDropdown = document.getElementById("filter-category");

    if (dropdown) {
      dropdown.innerHTML = categories.map(c => `<option value="${c.category_id}">${c.name}</option>`).join("");
    }
    if (filterDropdown) {
      filterDropdown.innerHTML = `<option value="">All Categories</option>` +
        categories.map(c => `<option value="${c.category_id}">${c.name}</option>`).join("");
    }
  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

async function loadTickets() {
  try {
    allTickets = await api.get("/tickets?limit=500");
    filterAndRenderTickets();
  } catch (err) {
    console.error("Failed to load tickets:", err);
  }
}

function filterAndRenderTickets() {
  const searchTerm = (document.getElementById("ticket-search")?.value || "").toLowerCase();
  const statusFilter = document.getElementById("filter-status")?.value || "";
  const catFilter = document.getElementById("filter-category")?.value || "";
  const prioFilter = document.getElementById("filter-priority")?.value || "";

  const filtered = allTickets.filter(t => {
    const matchesSearch = !searchTerm ||
      t.title.toLowerCase().includes(searchTerm) ||
      t.tracking_number.toLowerCase().includes(searchTerm) ||
      t.description.toLowerCase().includes(searchTerm);

    const matchesStatus = !statusFilter || t.status === statusFilter;
    const matchesCat = !catFilter || t.category_id === catFilter;
    const matchesPrio = !prioFilter || t.priority === prioFilter;

    return matchesSearch && matchesStatus && matchesCat && matchesPrio;
  });

  renderTicketsTable(filtered);
}

function renderTicketsTable(tickets) {
  const tbody = document.getElementById("tickets-tbody");
  if (!tbody) return;

  if (tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 32px; color: var(--gray-500);">No requests match your current filters.</td></tr>`;
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
          <a href="javascript:void(0)" onclick="openTicketDetail('${t.ticket_id}')" style="color:var(--primary); font-weight:600; text-decoration:none;">
            ${escapeHtml(t.title)}
          </a>
          ${sensitiveBadge}
        </td>
        <td>${escapeHtml(t.employee_name || "Employee")}</td>
        <td>${escapeHtml(t.category_name || "General")}</td>
        <td><span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span></td>
        <td><span class="badge badge-${t.status.toLowerCase()}">${t.status.replace("_", " ")}</span></td>
        <td>${slaBadge}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openTicketDetail('${t.ticket_id}')">Open</button>
        </td>
      </tr>
    `;
  }).join("");
}

// Open Detail Modal & Load Full Thread
async function openTicketDetail(ticketId) {
  activeTicketId = ticketId;
  try {
    const ticket = await api.get(`/tickets/${ticketId}`);
    currentTicketDetail = ticket;

    document.getElementById("detail-tracking").textContent = ticket.tracking_number;
    document.getElementById("detail-title").textContent = ticket.title;
    document.getElementById("detail-status").textContent = ticket.status.replace("_", " ");
    document.getElementById("detail-status").className = `badge badge-${ticket.status.toLowerCase()}`;
    document.getElementById("detail-priority").textContent = ticket.priority;
    document.getElementById("detail-priority").className = `badge badge-${ticket.priority.toLowerCase()}`;
    document.getElementById("detail-category").textContent = ticket.category_name || "General";
    document.getElementById("detail-employee").textContent = ticket.employee_name || "Employee";
    document.getElementById("detail-assigned").textContent = ticket.assigned_agent_name || "Unassigned";

    // Sensitive badge
    const sensEl = document.getElementById("detail-sensitive-tag");
    if (sensEl) sensEl.style.display = ticket.is_sensitive ? "inline-block" : "none";

    // SLA display
    const slaDueEl = document.getElementById("detail-sla-due");
    if (slaDueEl && ticket.resolution_due_at) {
      slaDueEl.textContent = new Date(ticket.resolution_due_at).toLocaleString();
    }

    // Render Conversation
    renderConversationThread(ticket.messages);

    // Show/hide action buttons based on status & role
    const user = api.getCurrentUser();
    const isHr = ["HR_AGENT", "HR_MANAGER", "ADMIN", "COMPLIANCE_OFFICER"].includes(user?.role);
    const isResolved = ["RESOLVED", "CLOSED"].includes(ticket.status);

    document.getElementById("btn-open-assign")?.style.setProperty("display", isHr && !isResolved ? "inline-flex" : "none");
    document.getElementById("btn-open-escalate")?.style.setProperty("display", isHr && !isResolved ? "inline-flex" : "none");
    document.getElementById("btn-open-resolve")?.style.setProperty("display", isHr && !isResolved ? "inline-flex" : "none");
    document.getElementById("btn-open-rate")?.style.setProperty("display", isResolved && user?.emp_id === ticket.employee_id ? "inline-flex" : "none");

    openModal("modal-ticket-detail");
  } catch (err) {
    console.error("Failed to load ticket details:", err);
  }
}
window.openTicketDetail = openTicketDetail;

function renderConversationThread(messages) {
  const container = document.getElementById("conversation-container");
  if (!container) return;

  if (!messages || messages.length === 0) {
    container.innerHTML = `<div style="color:var(--gray-500); padding:16px;">No messages in this thread yet.</div>`;
    return;
  }

  container.innerHTML = messages.map(m => {
    let bubbleClass = "chat-bubble employee";
    if (m.is_internal) bubbleClass = "chat-bubble internal";
    else if (["AGENT_REPLY", "SYSTEM_EVENT"].includes(m.message_type)) bubbleClass = "chat-bubble agent";

    const senderDisplay = m.is_internal ? "INTERNAL NOTE" : (m.sender_name || "User");
    const dateDisplay = new Date(m.created_at).toLocaleString();

    return `
      <div class="${bubbleClass}">
        <div class="chat-meta">
          <strong>${escapeHtml(senderDisplay)}</strong>
          <span>${dateDisplay}</span>
        </div>
        <div>${escapeHtml(m.content).replace(/\n/g, "<br>")}</div>
      </div>
    `;
  }).join("");
}

// Post New Message to Ticket Thread
async function handlePostMessage(event) {
  event.preventDefault();
  if (!activeTicketId) return;

  const contentInput = document.getElementById("message-content");
  const isInternalCheck = document.getElementById("message-is-internal");
  const content = contentInput.value.trim();
  if (!content) return;

  try {
    await api.post(`/tickets/${activeTicketId}/messages`, {
      content: content,
      is_internal: isInternalCheck ? isInternalCheck.checked : False
    });

    contentInput.value = "";
    api.showToast("Message posted");
    // Reload ticket detail
    await openTicketDetail(activeTicketId);
    await loadTickets();
  } catch (err) {
    console.error("Failed to post message:", err);
  }
}
window.handlePostMessage = handlePostMessage;

// Submit New Ticket
async function handleCreateTicket(event) {
  event.preventDefault();
  const title = document.getElementById("create-title").value.trim();
  const desc = document.getElementById("create-desc").value.trim();
  const categoryId = document.getElementById("create-category").value;
  const priority = document.getElementById("create-priority").value;
  const isSensitive = document.getElementById("create-sensitive").checked;

  if (!title || !desc) {
    api.showToast("Please provide both a title and description.", "error");
    return;
  }

  try {
    const res = await api.post("/tickets", {
      title,
      description: desc,
      category_id: categoryId,
      priority,
      is_sensitive: isSensitive
    });

    closeModal("modal-create-ticket");
    document.getElementById("create-ticket-form").reset();
    api.showToast(`Request ${res.tracking_number} submitted successfully!`);
    await loadTickets();

    if (res.status === "CLARIFICATION_NEEDED") {
      api.showToast("Additional clarification may be needed for this request.", "info");
    }
  } catch (err) {
    console.error("Failed to create ticket:", err);
  }
}
window.handleCreateTicket = handleCreateTicket;

// Resolve Ticket
async function handleResolveTicket(event) {
  event.preventDefault();
  if (!activeTicketId) return;

  const resType = document.getElementById("resolve-type").value;
  const notes = document.getElementById("resolve-notes").value.trim();
  const rootCause = document.getElementById("resolve-root-cause").value.trim();
  const policyVersion = document.getElementById("resolve-policy-version").value.trim();

  if (!notes) {
    api.showToast("Resolution notes are required.", "error");
    return;
  }

  try {
    await api.post(`/tickets/${activeTicketId}/resolve`, {
      resolution_type: resType,
      resolution_notes: notes,
      root_cause: rootCause || "Standard policy explanation",
      policy_version_used_id: policyVersion || null
    });

    closeModal("modal-resolve-ticket");
    api.showToast("Ticket successfully resolved!");
    await openTicketDetail(activeTicketId);
    await loadTickets();
  } catch (err) {
    console.error("Failed to resolve ticket:", err);
  }
}
window.handleResolveTicket = handleResolveTicket;

// Escalate Ticket
async function handleEscalateTicket(event) {
  event.preventDefault();
  if (!activeTicketId) return;

  const targetTier = document.getElementById("escalate-tier").value;
  const reason = document.getElementById("escalate-reason").value.trim();

  if (!reason) {
    api.showToast("Escalation reason is required.", "error");
    return;
  }

  try {
    await api.post(`/tickets/${activeTicketId}/escalate`, {
      target_tier: targetTier,
      escalation_reason: reason
    });

    closeModal("modal-escalate-ticket");
    api.showToast(`Ticket escalated to ${targetTier}!`);
    await openTicketDetail(activeTicketId);
    await loadTickets();
  } catch (err) {
    console.error("Failed to escalate ticket:", err);
  }
}
window.handleEscalateTicket = handleEscalateTicket;

// Rate Ticket
async function handleRateTicket(event) {
  event.preventDefault();
  if (!activeTicketId) return;

  const rating = parseInt(document.getElementById("rate-stars").value, 10);
  const feedback = document.getElementById("rate-feedback").value.trim();

  try {
    await api.post(`/tickets/${activeTicketId}/rate`, {
      employee_rating: rating,
      employee_feedback: feedback
    });

    closeModal("modal-rate-ticket");
    api.showToast("Thank you for your rating!");
    await openTicketDetail(activeTicketId);
  } catch (err) {
    console.error("Failed to submit rating:", err);
  }
}
window.handleRateTicket = handleRateTicket;

// Modal Helpers
function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add("active");
}
window.openModal = openModal;

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove("active");
}
window.closeModal = closeModal;

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

