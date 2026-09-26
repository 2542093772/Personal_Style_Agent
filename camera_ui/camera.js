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
const cloudSyncEl = document.getElementById("cloudSync");
const reuseProfileBtn = document.getElementById("reuseProfileBtn");
const updateProfileBtn = document.getElementById("updateProfileBtn");
const reusePanel = document.getElementById("reusePanel");
const cameraPanel = document.getElementById("cameraPanel");
const reuseSummary = document.getElementById("reuseSummary");

let stream = null;
let analysisEnabled = false;
let timer = null;

async function loadExistingProfile() {
  const resp = await fetch("/profile-data");
  const data = await resp.json();
  const stable = data.stable_profile || {};
  const count = stable.sample_count ?? 0;
  const parts = [
    `样本 ${count}`,
    stable.shoulder_width_impression ? `肩部 ${stable.shoulder_width_impression}` : "",
    stable.torso_length_impression ? `躯干 ${stable.torso_length_impression}` : "",
    stable.leg_length_impression ? `腿部 ${stable.leg_length_impression}` : ""
  ].filter(Boolean);
  reuseSummary.textContent = parts.length ? parts.join(" ｜ ") : "当前还没有可用档案";
  sampleCountEl.textContent = count;
  return data;
}

async function chooseReuseProfile() {
  cameraPanel.classList.add("hidden");
  reusePanel.classList.remove("hidden");
  try {
    await loadExistingProfile();
  } catch (e) {
    reuseSummary.textContent = "读取上一次档案失败";
  }
}

function chooseUpdateProfile() {
  reusePanel.classList.add("hidden");
  cameraPanel.classList.remove("hidden");
  statusEl.textContent = "准备更新个人信息。请先开启摄像头。";
}

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
  statusEl.textContent = "摄像头已开启。站好后点击“采集并更新个人档案”。";
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

async function captureAndUpdateProfile() {
  const blob = await captureBlob();
  if (!blob) {
    statusEl.textContent = "当前没有可采集的摄像头画面。";
    return;
  }

  profileBtn.disabled = true;
  collectStateEl.textContent = "正在更新";
  statusEl.textContent = "正在分析这次个人信息更新...";

  const form = new FormData();
  form.append("frame", blob, "profile.jpg");

  try {
    const resp = await fetch("/analyze-profile", { method: "POST", body: form });
    const data = await resp.json();
    if (data.ok) {
      const stable = data.merged_profile?.stable_profile || {};
      resultEl.textContent = JSON.stringify({
        mode: "manual_profile_update",
        stable_profile: stable,
        latest_observation: data.profile,
        style_rules: data.visual_style_rules || {}
      }, null, 2);
      collectStateEl.textContent = "更新成功";
      sampleCountEl.textContent = stable.sample_count ?? 0;
      lastSampleEl.textContent = new Date().toLocaleTimeString();
      const sync = data.github_sync || {};
      cloudSyncEl.textContent = sync.message || "等待同步";
      statusEl.textContent = "个人档案已更新。若角度不理想，可以换一个角度再采一次；否则可以停止摄像头。";
    } else {
      collectStateEl.textContent = "更新失败";
      statusEl.textContent = data.error || "个人档案更新失败，请调整站位或光线后重试。";
    }
  } catch (e) {
    collectStateEl.textContent = "更新失败";
    statusEl.textContent = "个人档案更新接口暂不可用。";
  } finally {
    profileBtn.disabled = false;
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
    resultEl.textContent = "实时穿搭分析接口未连接或暂不可用。";
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

reuseProfileBtn.addEventListener("click", chooseReuseProfile);
updateProfileBtn.addEventListener("click", chooseUpdateProfile);
startBtn.addEventListener("click", () => startCamera().catch(err => {
  statusEl.textContent = "无法开启摄像头：" + err.message;
}));
stopBtn.addEventListener("click", stopCamera);
profileBtn.addEventListener("click", captureAndUpdateProfile);
analysisBtn.addEventListener("click", toggleAnalysis);
window.addEventListener("beforeunload", stopCamera);
