function slidbar() {
  document.body.classList.toggle("open");  
  const sliderBtn = document.getElementById("slider-btn");
  if (document.body.classList.contains("open")) {
    sliderBtn.style.display = "none";
  } else {
    sliderBtn.style.display = "inline-block";
  }
}

document.addEventListener("DOMContentLoaded", function() {
  const menuHeading = document.querySelector(".slider h2");
  menuHeading.addEventListener("click", function() {
    document.body.classList.remove("open");
    document.getElementById("slider-btn").style.display = "inline-block";
  });
});

// Toggle button logic
const localBtn = document.getElementById('localBtn');
const ytBtn = document.getElementById('ytBtn');
const localPanel = document.getElementById('localPanel');
const ytPanel = document.getElementById('ytPanel');
const localInput = document.getElementById('localVideo');
const processLocalBtn = document.getElementById('processLocalBtn');
const ytUrl = document.getElementById('ytUrl');
const ytError = document.getElementById('ytError');
const processYtBtn = document.getElementById('processYtBtn');
const summaryOutput = document.getElementById('summaryOutput');


const ytRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;

function switchMode(isYouTube) {
  if (isYouTube) {
    ytBtn.classList.add('active');
    localBtn.classList.remove('active');
    ytPanel.classList.add('active');
    localPanel.classList.remove('active');
  } else {
    localBtn.classList.add('active');
    ytBtn.classList.remove('active');
    localPanel.classList.add('active');
    ytPanel.classList.remove('active');
  }
  localInput.value = "";
  processLocalBtn.disabled = true;
  ytUrl.value = "";
  processYtBtn.disabled = true;
  ytError.style.display = "none";
  summaryOutput.innerHTML = "";
}

localBtn.addEventListener('click', () => switchMode(false));
ytBtn.addEventListener('click', () => switchMode(true));
switchMode(false);

localInput.addEventListener("change", () => {
  processLocalBtn.disabled = !localInput.files || localInput.files.length === 0;
});

function validateYouTube(url) {
  return ytRegex.test(url.trim());
}

ytUrl.addEventListener("input", () => {
  const value = ytUrl.value;
  const valid = validateYouTube(value);
  ytError.style.display = value && !valid ? "inline" : "none";
  processYtBtn.disabled = !valid;
});

// Show loading state
function showLoading() {
  summaryOutput.innerHTML = '<div class="summary-container"><div class="loading-spinner"></div> <span>Processing video, please wait...</span></div>';
}

// Process local video
processLocalBtn.addEventListener("click", async () => {
  const file = localInput.files[0];
  if (!file) return;
  showLoading();

  const formData = new FormData();
  formData.append("video", file);

  try {
    const res = await fetch("/notes_sumariser/summarise_local", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    
    if (data.summary) {
      summaryOutput.innerHTML = data.summary;
    } else if (data.error) {
      summaryOutput.innerHTML = `<p style="color: #b91c1c;"><strong>Error:</strong> ${data.error}</p>`;
    } else {
      summaryOutput.innerHTML = "<p>No summary generated.</p>";
    }
  } catch (err) {
    summaryOutput.innerHTML = '<p style="color: #b91c1c;"><strong>Error:</strong> Failed to process video.</p>';
  }
});

// Process YouTube link
processYtBtn.addEventListener("click", async () => {
  const link = ytUrl.value.trim();
  if (!validateYouTube(link)) return;
  showLoading();

  try {
    const res = await fetch("/notes_sumariser/summarise_youtube", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: link })
    });
    const data = await res.json();
    
    if (data.summary) {
      summaryOutput.innerHTML = data.summary;
    } else if (data.error) {
      summaryOutput.innerHTML = `<p style="color: #b91c1c;"><strong>Error:</strong> ${data.error}</p>`;
    } else {
      summaryOutput.innerHTML = "<p>No summary generated.</p>";
    }
  } catch (err) {
    summaryOutput.innerHTML = '<p style="color: #b91c1c;"><strong>Error:</strong> Failed to process YouTube link.</p>';
  }
});