/* ================================================================
   history.js — Logika halaman Detection History
   ================================================================ */

let currentPage = 0;
const PAGE_SIZE = 10;
let currentMode = "";

const tableBody       = document.getElementById("historyTableBody");
const filterMode      = document.getElementById("filterMode");
const btnRefresh      = document.getElementById("btnRefreshHistory");
const btnPrevPage     = document.getElementById("btnPrevPage");
const btnNextPage     = document.getElementById("btnNextPage");
const paginationInfo  = document.getElementById("paginationInfo");

document.addEventListener("DOMContentLoaded", loadHistory);

filterMode.addEventListener("change", () => {
  currentMode = filterMode.value;
  currentPage = 0;
  loadHistory();
});

btnRefresh.addEventListener("click", loadHistory);

btnPrevPage.addEventListener("click", () => {
  if (currentPage > 0) {
    currentPage--;
    loadHistory();
  }
});

btnNextPage.addEventListener("click", () => {
  currentPage++;
  loadHistory();
});

async function loadHistory() {
  tableBody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">
    <div class="spinner-fire mx-auto mb-2" style="width:24px;height:24px;"></div>
    Memuat data...
  </td></tr>`;

  try {
    const skip = currentPage * PAGE_SIZE;
    let url = `/api/history?skip=${skip}&limit=${PAGE_SIZE}`;
    if (currentMode) url += `&mode=${currentMode}`;

    const res = await fetch(url);
    const data = await res.json();

    renderTable(data);
    paginationInfo.textContent = `Menampilkan ${data.length} data — Halaman ${currentPage + 1}`;
    btnPrevPage.disabled = currentPage === 0;
    btnNextPage.disabled = data.length < PAGE_SIZE;

  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-danger">
      Gagal memuat data: ${err.message}
    </td></tr>`;
  }
}

function renderTable(sessions) {
  if (sessions.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="9" class="text-center py-5 text-muted">
      <i class="bi bi-inbox fs-1 d-block mb-2"></i>
      Belum ada riwayat deteksi
    </td></tr>`;
    return;
  }

  tableBody.innerHTML = sessions.map(s => `
    <tr>
      <td class="text-muted">#${s.id}</td>
      <td><span class="mode-badge ${s.mode}">${s.mode}</span></td>
      <td>${s.filename || '<span class="text-muted">—</span>'}</td>
      <td><span class="text-fire fw-700">${s.total_fire}</span></td>
      <td><span class="text-smoke fw-700">${s.total_smoke}</span></td>
      <td>${(s.avg_confidence * 100).toFixed(1)}%</td>
      <td>${s.fps ? s.fps.toFixed(1) : '-'}</td>
      <td class="fs-12 text-muted">${formatDate(s.created_at)}</td>
      <td>
        <div class="d-flex gap-1">
          ${s.output_path ? `
            <button class="btn btn-sm btn-outline-primary" onclick="viewResult(${s.id}, '${s.mode}')">
              <i class="bi bi-eye"></i>
            </button>
          ` : ''}
          <button class="btn btn-sm btn-outline-danger" onclick="deleteSession(${s.id})">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </td>
    </tr>
  `).join("");
}

async function deleteSession(id) {
  if (!confirm(`Hapus sesi #${id}? Tindakan ini tidak dapat dibatalkan.`)) return;

  try {
    const res = await fetch(`/api/history/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Gagal menghapus sesi");

    showToast(`Sesi #${id} berhasil dihapus`, "success");
    loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function viewResult(id, mode) {
  try {
    const res = await fetch(`/api/history/${id}`);
    const data = await res.json();

    if (!data.output_path) {
      showToast("File hasil tidak tersedia", "error");
      return;
    }

    const filename = data.output_path.split(/[/\\]/).pop();
    const mediaType = mode === "video" ? "videos" : "images";
    const url = `/api/download/${mediaType}/${filename}`;
    window.open(url, "_blank");
  } catch (err) {
    showToast("Gagal memuat detail sesi", "error");
  }
}
