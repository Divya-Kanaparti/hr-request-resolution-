/**
 * Authentication and User Session Management
 */

document.addEventListener("DOMContentLoaded", () => {
  initAuthUI();
});

function initAuthUI() {
  const user = api.getCurrentUser();
  const isLoginPage = window.location.pathname.includes("login.html") || (window.location.pathname.endsWith("/") && !api.getToken());

  // Protect internal pages
  if (!user && !isLoginPage && !window.location.pathname.includes("index.html")) {
    window.location.href = "login.html";
    return;
  }

  // Update UI if logged in
  if (user) {
    const nameEls = document.querySelectorAll(".current-user-name");
    const roleEls = document.querySelectorAll(".current-user-role");
    const avatarEls = document.querySelectorAll(".current-user-avatar");

    nameEls.forEach(el => el.textContent = user.full_name);
    roleEls.forEach(el => el.textContent = user.role.replace("_", " "));
    avatarEls.forEach(el => {
      const initials = user.full_name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
      el.textContent = initials || "HR";
    });

    // Role-based visibility
    const isHrStaff = ["HR_AGENT", "HR_MANAGER", "ADMIN", "COMPLIANCE_OFFICER"].includes(user.role);
    const isComplianceAdmin = ["ADMIN", "COMPLIANCE_OFFICER", "HR_MANAGER"].includes(user.role);

    document.querySelectorAll(".hr-only").forEach(el => {
      el.style.display = isHrStaff ? "" : "none";
    });
    document.querySelectorAll(".compliance-only").forEach(el => {
      el.style.display = isComplianceAdmin ? "" : "none";
    });
  }

  // Attach logout handler
  const logoutBtns = document.querySelectorAll(".btn-logout, #logout-btn");
  logoutBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      api.clearToken();
      api.showToast("Logged out successfully", "info");
      setTimeout(() => window.location.href = "login.html", 400);
    });
  });
}

// Quick Fill Demo Credentials
function fillDemoCredentials(email, roleName) {
  const emailInput = document.getElementById("login-email");
  const pwdInput = document.getElementById("login-password");
  if (emailInput && pwdInput) {
    emailInput.value = email;
    pwdInput.value = "Password123!";
    api.showToast(`Selected Demo: ${roleName}`, "info");
  }
}
window.fillDemoCredentials = fillDemoCredentials;

