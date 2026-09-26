const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const profileBtn = document.getElementById("profileBtn");
const analysisBtn = document.getElementById("analysisBtn");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const collectStateEl = document.getElementById("collectState");
const sampleCountEl = document.getElementById("sampleCount");
const lastSampleEl = document.getElementById("lastSample");

let stream = null;
let analysisEnabled = false;
let profileCollectionEnabled = false;
let timer = null;
let profileTimer = null;

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
  statusEl.textContent = "摄像头已开启。可开启持续视觉采集来完善个人档案。";
}

function stopCamera() {
  analysisEnabled = false;
  profileCollectionEnabled = false;
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
  if (profileTimer) {
    clearInterval(profileTimer);
    profileTimer = null;
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
  profileBtn.textContent = "开启持续视觉采集";
  analysisBtn.textContent = "开启实时穿搭分析";
  statusEl.textContent = "摄像头已停止";
  collectStateEl.textContent = "未采集";
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

async function collectProfileSample() {
  if (!profileCollectionEnabled) return;
  const blob = await captureBlob();
  if (!blob) return;

  const form = new FormData();
  form.append("frame", blob, "profile.jpg");

  try {
    const resp = await fetch("/analyze-profile", { method: "POST", body: form });
    const data = await resp.json();
    if (data.ok) {
      const stable = data.merged_profile?.stable_profile || {};
      resultEl.textContent = JSON.stringify({
        mode: "continuous_profile_collection",
        stable_profile: stable,
        latest_observation: data.profile
      }, null, 2);
      statusEl.textContent = "持续视觉采集中：正在累积你的稳定外形与比例特征。";
      collectStateEl.textContent = "采集中";
      sampleCountEl.textContent = stable.sample_count ?? 0;
      lastSampleEl.textContent = new Date().toLocaleTimeString();
    } else {
      statusEl.textContent = "持续视觉采集失败，请检查模型配置。";
    }
  } catch (e) {
    statusEl.textContent = "持续视觉采集接口暂不可用。";
  }
}

function toggleProfileCollection() {
  profileCollectionEnabled = !profileCollectionEnabled;
  profileBtn.textContent = profileCollectionEnabled
    ? "停止持续视觉采集"
    : "开启持续视觉采集";

  if (profileCollectionEnabled) {
    statusEl.textContent = "持续视觉采集已开启。默认只保存提取后的特征，不保存原始画面。";
    collectProfileSample();
    if (profileTimer) clearInterval(profileTimer);
    profileTimer = setInterval(collectProfileSample, 12000);
  } else {
    if (profileTimer) {
      clearInterval(profileTimer);
      profileTimer = null;
    }
    statusEl.textContent = "持续视觉采集已停止，但摄像头仍开启。";
    collectStateEl.textContent = "已暂停";
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
profileBtn.addEventListener("click", toggleProfileCollection);
analysisBtn.addEventListener("click", toggleAnalysis);
window.addEventListener("beforeunload", stopCamera);
