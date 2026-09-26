const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const profileBtn = document.getElementById("profileBtn");
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
  profileBtn.disabled = false;
  analysisBtn.disabled = false;
  statusEl.textContent = "摄像头已开启。建议先点击“建立视觉档案”。";
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
  profileBtn.disabled = true;
  analysisBtn.disabled = true;
  analysisBtn.textContent = "开启实时穿搭分析";
  statusEl.textContent = "摄像头已停止";
}

async function captureBlob() {
  if (!stream || video.readyState < 2) return null;
  const w = video.videoWidth || 640;
  const h = video.videoHeight || 480;
  const targetW = 960;
  const targetH = Math.round(h * targetW / w);
  canvas.width = targetW;
  canvas.height = targetH;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, targetW, targetH);
  return await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.85));
}

async function analyzeProfile() {
  const blob = await captureBlob();
  if (!blob) return;

  statusEl.textContent = "正在识别你的视觉特征...";
  const form = new FormData();
  form.append("frame", blob, "profile.jpg");

  try {
    const resp = await fetch("/analyze-profile", { method: "POST", body: form });
    const data = await resp.json();
    resultEl.textContent = JSON.stringify(data, null, 2);
    statusEl.textContent = data.ok
      ? "本次视觉档案观察已完成。可换正面/侧面/更完整全身视角继续补充。"
      : "视觉档案识别失败，请检查配置。";
  } catch (e) {
    statusEl.textContent = "视觉档案接口未连接或暂不可用。";
  }
}

async function sendFrame() {
  if (!analysisEnabled) return;
  const blob = await captureBlob();
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
  analysisBtn.textContent = analysisEnabled ? "停止实时穿搭分析" : "开启实时穿搭分析";
  statusEl.textContent = analysisEnabled
    ? "实时穿搭分析已开启。"
    : "实时穿搭分析已停止，但摄像头仍开启。";

  if (analysisEnabled) {
    if (timer) clearInterval(timer);
    timer = setInterval(sendFrame, 2500);
  } else if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

startBtn.addEventListener("click", () => startCamera().catch(err => {
  statusEl.textContent = "无法开启摄像头：" + err.message;
}));
stopBtn.addEventListener("click", stopCamera);
profileBtn.addEventListener("click", analyzeProfile);
analysisBtn.addEventListener("click", toggleAnalysis);
window.addEventListener("beforeunload", stopCamera);
