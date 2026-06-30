/* ================================================================
   camera_detect.js — Logika halaman Live Detection (WebSocket)
   ================================================================ */

let videoStream   = null;
let websocket     = null;
let captureInterval = null;
let isDetecting   = false;

const videoEl        = document.getElementById("videoElement");
const outputImg       = document.getElementById("outputImage");
const captureCanvas   = document.getElementById("captureCanvas");
const cameraPlaceholder = document.getElementById("cameraPlaceholder");
const cameraOverlay   = document.getElementById("cameraOverlay");
const fpsBadge        = document.getElementById("fpsBadge");
const btnStart        = document.getElementById("btnStart");
const btnStop         = document.getElementById("btnStop");
const connStatus      = document.getElementById("connStatus");

const liveFireCount   = document.getElementById("liveFireCount");
const liveSmokeCount  = document.getElementById("liveSmokeCount");
const liveFps         = document.getElementById("liveFps");
const liveFrameCount  = document.getElementById("liveFrameCount");
const detectionStatusBox = document.getElementById("detectionStatusBox");

const CAPTURE_FPS = 2;          // kirim frame ke server 10x/detik
const JPEG_QUALITY = 0.5;

// ── Start Detection ────────────────────────────────────────────────
btnStart.addEventListener("click", async () => {
  try {
    btnStart.disabled = true;
    btnStart.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Mengakses kamera...';

    // 1. Akses webcam
    videoStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    });
    videoEl.srcObject = videoStream;

    // 2. Buka WebSocket
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    websocket = new WebSocket(`${wsProtocol}//${window.location.host}/ws/detect`);

    websocket.onopen = () => {
      connStatus.textContent = "Connected";
      connStatus.className = "badge bg-success-subtle text-success";
      startCapturing();
      isDetecting = true;

      cameraPlaceholder.classList.add("d-none");
      outputImg.style.display = "block";
      cameraOverlay.classList.remove("d-none");
      btnStart.classList.add("d-none");
      btnStop.classList.remove("d-none");
      showToast("Deteksi real-time dimulai", "success");
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    };

    websocket.onerror = () => {
      showToast("Terjadi kesalahan koneksi WebSocket", "error");
    };

    websocket.onclose = () => {
      connStatus.textContent = "Disconnected";
      connStatus.className = "badge bg-secondary-subtle text-secondary";
      stopDetection();
    };

  } catch (err) {
    showToast("Gagal mengakses kamera: " + err.message, "error");
    btnStart.disabled = false;
    btnStart.innerHTML = '<i class="bi bi-play-fill"></i> Start Detection';
  }
});

// ── Stop Detection ─────────────────────────────────────────────────
btnStop.addEventListener("click", () => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send("stop");
    websocket.close();
  }
  stopDetection();
});

function stopDetection() {
  isDetecting = false;

  if (captureInterval) {
    clearInterval(captureInterval);
    captureInterval = null;
  }

  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
    videoStream = null;
  }

  cameraPlaceholder.classList.remove("d-none");
  outputImg.style.display = "none";
  cameraOverlay.classList.add("d-none");
  btnStart.classList.remove("d-none");
  btnStart.disabled = false;
  btnStart.innerHTML = '<i class="bi bi-play-fill"></i> Start Detection';
  btnStop.classList.add("d-none");
}

// ── Capture frame & kirim ke server ───────────────────────────────
function startCapturing() {
  const ctx = captureCanvas.getContext("2d");
  captureCanvas.width = 640;
  captureCanvas.height = 480;

  let skippedCount = 0;
  captureInterval = setInterval(() => {
    if (!isDetecting || !websocket || websocket.readyState !== WebSocket.OPEN) return;
    if (videoEl.readyState < 2) {
      skippedCount++;
      if (skippedCount <= 5) {
        console.warn(`[DEBUG] Frame dilewati, videoEl.readyState = ${videoEl.readyState} (butuh >= 2). videoEl.videoWidth=${videoEl.videoWidth}`);
      }
      return;
    }

    ctx.drawImage(videoEl, 0, 0, captureCanvas.width, captureCanvas.height);
    const base64Frame = captureCanvas.toDataURL("image/jpeg", JPEG_QUALITY);
    websocket.send(base64Frame);
  }, 1000 / CAPTURE_FPS);
}

// ── Tangani pesan dari server ──────────────────────────────────────
let receivedFrameCount = 0;

function handleServerMessage(data) {
  if (data.status === "error") {
    console.warn("Server error:", data.message);
    return;
  }

  // Update gambar hasil deteksi
  if (data.frame_base64) {
    outputImg.src = data.frame_base64;
    receivedFrameCount++;
    if (receivedFrameCount <= 3) {
      console.log(`[DEBUG] Frame #${receivedFrameCount} diterima, panjang base64: ${data.frame_base64.length}, outputImg display: ${getComputedStyle(outputImg).display}, outputImg size: ${outputImg.offsetWidth}x${outputImg.offsetHeight}`);
    }
  } else {
    console.warn("[DEBUG] Pesan dari server TIDAK ada frame_base64:", data);
  }

  // Update statistik
  fpsBadge.textContent = `FPS: ${data.fps.toFixed(1)}`;
  liveFps.textContent = data.fps.toFixed(1);
  liveFrameCount.textContent = data.frame_number;
  liveFireCount.textContent = data.total_fire;
  liveSmokeCount.textContent = data.total_smoke;

  // Update status bahaya
  updateDangerStatus(data.fire_count, data.smoke_count);
}

function updateDangerStatus(fireCount, smokeCount) {
  if (fireCount > 0) {
    detectionStatusBox.innerHTML = `
      <i class="bi bi-exclamation-triangle-fill fs-1 text-fire d-block mb-2"></i>
      <div class="fw-700 text-fire">BAHAYA — Api Terdeteksi!</div>
      <small class="text-muted">${fireCount} objek api terdeteksi</small>
    `;
  } else if (smokeCount > 0) {
    detectionStatusBox.innerHTML = `
      <i class="bi bi-exclamation-circle-fill fs-1 text-warning d-block mb-2"></i>
      <div class="fw-700 text-warning">PERINGATAN — Asap Terdeteksi</div>
      <small class="text-muted">${smokeCount} objek asap terdeteksi</small>
    `;
  } else {
    detectionStatusBox.innerHTML = `
      <i class="bi bi-shield-check fs-1 text-success d-block mb-2"></i>
      <div class="fw-700">Aman — Tidak ada bahaya</div>
      <small class="text-muted">Status akan diperbarui secara real-time</small>
    `;
  }
}

// ── Bersihkan koneksi saat halaman ditutup ─────────────────────────
window.addEventListener("beforeunload", () => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send("stop");
  }
  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
  }
});
