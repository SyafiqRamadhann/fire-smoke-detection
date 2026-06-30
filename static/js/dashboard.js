/* ================================================================
   dashboard.js — Logika global aplikasi
   Dipakai di SEMUA halaman (load via base.html)
   ================================================================ */

// ── Toast Notification System ─────────────────────────────────────
function showToast(message, type = "info") {
  let container = document.querySelector(".toast-container-custom");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container-custom";
    document.body.appendChild(container);
  }

  const icons = {
    success: "bi-check-circle-fill",
    error:   "bi-x-circle-fill",
    info:    "bi-info-circle-fill",
  };
  const colors = { success: "#22c55e", error: "#ef4444", info: "#4361ee" };

  const toast = document.createElement("div");
  toast.className = `toast-custom ${type}`;
  toast.innerHTML = `
    <i class="bi ${icons[type] || icons.info}" style="color:${colors[type] || colors.info}; font-size:18px;"></i>
    <div style="font-size:13px; color:#1e2340; flex:1;">${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all .3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Cek Status Model (ditampilkan di sidebar) ─────────────────────
async function checkModelStatus() {
  const dot  = document.getElementById("statusDot");
  const text = document.getElementById("statusText");
  if (!dot || !text) return;

  try {
    const res  = await fetch("/api/model/info");
    const data = await res.json();

    if (data.loaded) {
      dot.classList.add("ready");
      dot.classList.remove("error");
      text.textContent = "Model Ready";
    } else {
      dot.classList.add("error");
      dot.classList.remove("ready");
      text.textContent = "Model Not Loaded";
    }
  } catch (e) {
    dot.classList.add("error");
    text.textContent = "Server Offline";
  }
}

// ── Helper: format angka ────────────────────────────────────────
function formatNumber(num) {
  return new Intl.NumberFormat("id-ID").format(num);
}

function formatPercent(val) {
  return (val * 100).toFixed(1) + "%";
}

function formatDate(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString("id-ID", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// ── Inisialisasi saat halaman dimuat ───────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  checkModelStatus();
  // Refresh status setiap 15 detik
  setInterval(checkModelStatus, 15000);

  // Jalankan loader dashboard jika berada di halaman dashboard
  if (document.getElementById("statTotalFire")) {
    loadDashboardStats();
    setInterval(loadDashboardStats, 10000);
  }
});

// ── Loader Statistik Dashboard ─────────────────────────────────────
async function loadDashboardStats() {
  try {
    const res  = await fetch("/api/stats");
    const data = await res.json();

    setText("statTotalFire",  formatNumber(data.total_fire));
    setText("statTotalSmoke", formatNumber(data.total_smoke));
    setText("statAvgConf",    formatPercent(data.avg_confidence));
    setText("statAvgFps",     data.avg_fps.toFixed(1));
    setText("statTotalSession", formatNumber(data.total_sessions));

    const lastEl = document.getElementById("statLastDetection");
    if (lastEl) {
      lastEl.textContent = data.last_session
        ? formatDate(data.last_session.created_at)
        : "Belum ada deteksi";
    }
  } catch (e) {
    console.error("Gagal memuat statistik dashboard:", e);
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}
