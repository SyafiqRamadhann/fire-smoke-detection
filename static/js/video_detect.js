/* ================================================================
   video_detect.js — Logika halaman Video Detection
   ================================================================ */

let selectedFileV = null;
let currentOutputUrlV = null;

const uploadAreaV  = document.getElementById("uploadAreaV");
const fileInputV   = document.getElementById("fileInputV");
const previewBoxV  = document.getElementById("previewBoxV");
const previewVideo = document.getElementById("previewVideo");
const fileNameElV  = document.getElementById("fileNameV");
const btnDetectV   = document.getElementById("btnDetectV");
const btnRemoveV   = document.getElementById("btnRemoveFileV");
const btnDownloadV = document.getElementById("btnDownloadV");
const resultBoxV   = document.getElementById("resultBoxV");
const loadingBoxV  = document.getElementById("loadingBoxV");
const loadingTextV = document.getElementById("loadingTextV");
const progressFillV = document.getElementById("progressFillV");
const statsRowV    = document.getElementById("statsRowV");

uploadAreaV.addEventListener("click", () => fileInputV.click());

fileInputV.addEventListener("change", (e) => {
  if (e.target.files.length) handleFileV(e.target.files[0]);
});

["dragenter", "dragover"].forEach(evt => {
  uploadAreaV.addEventListener(evt, (e) => {
    e.preventDefault();
    uploadAreaV.classList.add("drag-over");
  });
});
["dragleave", "drop"].forEach(evt => {
  uploadAreaV.addEventListener(evt, (e) => {
    e.preventDefault();
    uploadAreaV.classList.remove("drag-over");
  });
});
uploadAreaV.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) handleFileV(file);
});

function handleFileV(file) {
  const validTypes = ["video/mp4", "video/avi", "video/x-msvideo", "video/quicktime"];
  const validExt = [".mp4", ".avi", ".mov"];
  const ext = "." + file.name.split(".").pop().toLowerCase();

  if (!validTypes.includes(file.type) && !validExt.includes(ext)) {
    showToast("Format file tidak didukung. Gunakan MP4 atau AVI.", "error");
    return;
  }
  if (file.size > 500 * 1024 * 1024) {
    showToast("Ukuran file maksimal 500MB.", "error");
    return;
  }

  selectedFileV = file;
  previewVideo.src = URL.createObjectURL(file);
  previewBoxV.classList.remove("d-none");
  fileNameElV.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
  btnDetectV.disabled = false;
}

btnRemoveV.addEventListener("click", () => {
  selectedFileV = null;
  fileInputV.value = "";
  previewBoxV.classList.add("d-none");
  btnDetectV.disabled = true;
});

btnDetectV.addEventListener("click", async () => {
  if (!selectedFileV) return;

  loadingBoxV.classList.remove("d-none");
  resultBoxV.classList.add("d-none");
  statsRowV.classList.add("d-none");
  btnDownloadV.classList.add("d-none");
  btnDetectV.disabled = true;

  // Simulasi progress bar (karena proses video sinkron di backend)
  let fakeProgress = 0;
  const progressInterval = setInterval(() => {
    fakeProgress = Math.min(fakeProgress + Math.random() * 8, 92);
    progressFillV.style.width = fakeProgress + "%";
  }, 600);

  const formData = new FormData();
  formData.append("file", selectedFileV);

  try {
    const res = await fetch("/api/detect/video", {
      method: "POST",
      body: formData,
    });

    clearInterval(progressInterval);
    progressFillV.style.width = "100%";

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Deteksi video gagal");
    }

    const data = await res.json();
    setTimeout(() => renderResultV(data), 300);
    showToast("Deteksi video berhasil!", "success");

  } catch (err) {
    clearInterval(progressInterval);
    showToast(err.message, "error");
    resultBoxV.classList.remove("d-none");
  } finally {
    setTimeout(() => {
      loadingBoxV.classList.add("d-none");
      btnDetectV.disabled = false;
      progressFillV.style.width = "0%";
    }, 400);
  }
});

function renderResultV(data) {
  currentOutputUrlV = data.output_url;

  resultBoxV.innerHTML = `
    <video src="${data.output_url}" controls class="w-100" style="max-height:440px; object-fit:contain;"></video>
  `;
  resultBoxV.classList.remove("d-none");

  document.getElementById("resFireV").textContent  = data.total_fire;
  document.getElementById("resSmokeV").textContent = data.total_smoke;
  document.getElementById("resConfV").textContent  = (data.avg_confidence * 100).toFixed(1) + "%";
  document.getElementById("resFpsV").textContent   = data.fps.toFixed(1);
  statsRowV.classList.remove("d-none");

  btnDownloadV.classList.remove("d-none");
}

btnDownloadV.addEventListener("click", () => {
  if (!currentOutputUrlV) return;
  const a = document.createElement("a");
  a.href = currentOutputUrlV;
  a.download = "fire_smoke_detection_video.mp4";
  document.body.appendChild(a);
  a.click();
  a.remove();
});
