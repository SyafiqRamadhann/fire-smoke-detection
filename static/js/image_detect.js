/* ================================================================
   image_detect.js — Logika halaman Image Detection
   ================================================================ */

let selectedFile = null;
let currentOutputUrl = null;

const uploadArea   = document.getElementById("uploadArea");
const fileInput    = document.getElementById("fileInput");
const previewBox   = document.getElementById("previewBox");
const previewImg   = document.getElementById("previewImg");
const fileNameEl   = document.getElementById("fileName");
const btnDetect    = document.getElementById("btnDetect");
const btnRemove    = document.getElementById("btnRemoveFile");
const btnDownload  = document.getElementById("btnDownload");
const resultBox    = document.getElementById("resultBox");
const loadingBox   = document.getElementById("loadingBox");
const statsRow     = document.getElementById("statsRow");
const detailList   = document.getElementById("detailList");

// ── Klik untuk upload ──────────────────────────────────────────────
uploadArea.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
});

// ── Drag & Drop ────────────────────────────────────────────────────
["dragenter", "dragover"].forEach(evt => {
  uploadArea.addEventListener(evt, (e) => {
    e.preventDefault();
    uploadArea.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach(evt => {
  uploadArea.addEventListener(evt, (e) => {
    e.preventDefault();
    uploadArea.classList.remove("drag-over");
  });
});

uploadArea.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// ── Handle file terpilih ───────────────────────────────────────────
function handleFile(file) {
  const validTypes = ["image/jpeg", "image/jpg", "image/png"];
  if (!validTypes.includes(file.type)) {
    showToast("Format file tidak didukung. Gunakan JPG atau PNG.", "error");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast("Ukuran file maksimal 10MB.", "error");
    return;
  }

  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewBox.classList.remove("d-none");
    fileNameEl.textContent = file.name;
    btnDetect.disabled = false;
  };
  reader.readAsDataURL(file);
}

// ── Hapus file ─────────────────────────────────────────────────────
btnRemove.addEventListener("click", () => {
  selectedFile = null;
  fileInput.value = "";
  previewBox.classList.add("d-none");
  btnDetect.disabled = true;
});

// ── Jalankan Deteksi ───────────────────────────────────────────────
btnDetect.addEventListener("click", async () => {
  if (!selectedFile) return;

  loadingBox.classList.remove("d-none");
  resultBox.classList.add("d-none");
  statsRow.classList.add("d-none");
  btnDownload.classList.add("d-none");
  detailList.innerHTML = "";
  btnDetect.disabled = true;

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch("/api/detect/image", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Deteksi gagal");
    }

    const data = await res.json();
    renderResult(data);
    showToast("Deteksi berhasil dijalankan!", "success");

  } catch (err) {
    showToast(err.message, "error");
    resultBox.classList.remove("d-none");
  } finally {
    loadingBox.classList.add("d-none");
    btnDetect.disabled = false;
  }
});

// ── Render hasil deteksi ───────────────────────────────────────────
function renderResult(data) {
  currentOutputUrl = data.output_url;

  resultBox.innerHTML = `<img src="${data.output_url}" alt="Hasil deteksi">`;
  resultBox.classList.remove("d-none");

  document.getElementById("resFire").textContent  = data.total_fire;
  document.getElementById("resSmoke").textContent = data.total_smoke;
  document.getElementById("resConf").textContent  = (data.avg_confidence * 100).toFixed(1) + "%";
  statsRow.classList.remove("d-none");

  btnDownload.classList.remove("d-none");

  // Render detail list
  if (data.detections.length === 0) {
    detailList.innerHTML = `<div class="text-center text-muted py-3 fs-13">
      <i class="bi bi-shield-check fs-3 d-block mb-1"></i>
      Tidak ada objek api atau asap terdeteksi
    </div>`;
  } else {
    detailList.innerHTML = `
      <div class="fs-13 fw-700 mb-2 text-muted">DETAIL DETEKSI (${data.detections.length})</div>
      <div class="d-flex flex-wrap gap-2">
        ${data.detections.map(d => `
          <span class="det-badge ${d.class_name.toLowerCase()}">
            <i class="bi bi-${d.class_name === 'Fire' ? 'fire' : 'cloud-haze2-fill'}"></i>
            ${d.class_name} ${(d.confidence * 100).toFixed(0)}%
          </span>
        `).join("")}
      </div>
    `;
  }
}

// ── Download hasil ─────────────────────────────────────────────────
btnDownload.addEventListener("click", () => {
  if (!currentOutputUrl) return;
  const a = document.createElement("a");
  a.href = currentOutputUrl;
  a.download = "fire_smoke_detection_result.jpg";
  document.body.appendChild(a);
  a.click();
  a.remove();
});
