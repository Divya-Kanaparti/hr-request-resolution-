/**
 * Centralized API Client Module
 * Manages Base URL, Authentication Tokens, Requests, and Toast Alerts.
 */

const API_CONFIG = {
  // Auto-detect base URL
  getBaseUrl() {
    const custom = localStorage.getItem("API_BASE_URL");
    if (custom) return custom;
    if (window.location.port === "8000") {
      return "/api/v1";
    }
    return "http://localhost:8000/api/v1";
  }
};

class ApiClient {
  constructor() {
    this.baseUrl = API_CONFIG.getBaseUrl();
  }

  getToken() {
    return localStorage.getItem("hr_access_token");
  }

  setToken(token) {
    localStorage.setItem("hr_access_token", token);
  }

  clearToken() {
    localStorage.removeItem("hr_access_token");
    localStorage.removeItem("hr_user");
  }

  getCurrentUser() {
    const userStr = localStorage.getItem("hr_user");
    return userStr ? JSON.parse(userStr) : null;
  }

  setCurrentUser(user) {
    localStorage.setItem("hr_user", JSON.stringify(user));
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });

      if (response.status === 401) {
        this.clearToken();
        if (!window.location.pathname.includes("login.html") && !window.location.pathname.endsWith("/")) {
          window.location.href = "login.html";
        }
        throw new Error("Session expired. Please log in again.");
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.detail || (typeof data === "string" ? data : "Request failed");
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      this.showToast(err.message || "Network Error: Is backend running on localhost:8000?", "error");
      throw err;
    }
  }

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  }

  post(endpoint, body) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body)
    });
  }

  put(endpoint, body) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body)
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }

  showToast(message, type = "success") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

const api = new ApiClient();
window.api = api;

