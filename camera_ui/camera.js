const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const analysisBtn = document.getElementById("analysisBtn");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");

let stream = null;
let analysisEnabled = false;
let timer = null;

async function startCamera() {
  stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
    audio: false
  });
  video.srcObject = stream;
  video.classList.add("active");
  startBtn.disabled = true;
  stopBtn.disabled = false;
  analysisBtn.disabled = false;
  statusEl.textContent = "摄像头已开启，仅在当前页面会话中使用。";
}

function stopCamera() {
  analysisEnabled = false;
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  video.srcObject = null;
  video.classList.remove("active");
  startBtn.disabled = false;
  stopBtn.disabled = true;
  analysisBtn.disabled = true;
  analysisBtn.textContent = "开启实时分析";
  statusEl.textContent = "摄像头已停止";
}

async function sendFrame() {
  if (!analysisEnabled || !stream || video.readyState < 2) return;

  const w = video.videoWidth || 640;
  const h = video.videoHeight || 480;
  const targetW = 640;
  const targetH = Math.round(h * targetW / w);
  canvas.width = targetW;
  canvas.height = targetH;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, targetW, targetH);

  const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.75));
  if (!blob) return;

  const form = new FormData();
  form.append("frame", blob, "frame.jpg");

  try {
    const resp = await fetch("/analyze-frame", { method: "POST", body: form });
    const data = await resp.json();
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    resultEl.textContent = "分析接口未连接或暂不可用。";
  }
}

function toggleAnalysis() {
  analysisEnabled = !analysisEnabled;
  analysisBtn.textContent = analysisEnabled ? "停止实时分析" : "开启实时分析";
  statusEl.textContent = analysisEnabled
    ? "实时分析已开启：当前以低频抓帧方式工作。"
    : "实时分析已停止，但摄像头仍开启。";

  if (analysisEnabled) {
    if (timer) clearInterval(timer);
    timer = setInterval(sendFrame, 1500);
  } else if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

startBtn.addEventListener("click", () => startCamera().catch(err => {
  statusEl.textContent = "无法开启摄像头：" + err.message;
}));
stopBtn.addEventListener("click", stopCamera);
analysisBtn.addEventListener("click", toggleAnalysis);
window.addEventListener("beforeunload", stopCamera);
