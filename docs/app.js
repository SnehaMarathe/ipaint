const defaultApiBase = "http://127.0.0.1:8000";
const apiBase = () => localStorage.getItem("ipant_api_base") || window.IPANT_API_BASE || defaultApiBase;

let currentChart = null;

const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const birthForm = document.getElementById("birthForm");
const demoBtn = document.getElementById("demoBtn");
const askBtn = document.getElementById("askBtn");
const answerBox = document.getElementById("answerBox");
const apiDialog = document.getElementById("apiDialog");
const apiConfigBtn = document.getElementById("apiConfigBtn");
const apiBaseInput = document.getElementById("apiBaseInput");
const saveApiBtn = document.getElementById("saveApiBtn");

const houseCenters = {
  1: { x: 60, y: 200 },
  2: { x: 130, y: 130 },
  3: { x: 60, y: 60 },
  4: { x: 200, y: 60 },
  5: { x: 340, y: 60 },
  6: { x: 270, y: 130 },
  7: { x: 340, y: 200 },
  8: { x: 270, y: 270 },
  9: { x: 340, y: 340 },
  10: { x: 200, y: 340 },
  11: { x: 60, y: 340 },
  12: { x: 130, y: 270 }
};

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${kind}`.trim();
}

function buildNorthIndianSvg(chartMap) {
  const lines = [
    '<line class="svg-line" x1="20" y1="20" x2="200" y2="200"></line>',
    '<line class="svg-line" x1="380" y1="20" x2="200" y2="200"></line>',
    '<line class="svg-line" x1="20" y1="380" x2="200" y2="200"></line>',
    '<line class="svg-line" x1="380" y1="380" x2="200" y2="200"></line>',
    '<line class="svg-line" x1="20" y1="20" x2="380" y2="20"></line>',
    '<line class="svg-line" x1="380" y1="20" x2="380" y2="380"></line>',
    '<line class="svg-line" x1="380" y1="380" x2="20" y2="380"></line>',
    '<line class="svg-line" x1="20" y1="380" x2="20" y2="20"></line>',
    '<line class="svg-line" x1="110" y1="20" x2="20" y2="110"></line>',
    '<line class="svg-line" x1="290" y1="20" x2="380" y2="110"></line>',
    '<line class="svg-line" x1="380" y1="290" x2="290" y2="380"></line>',
    '<line class="svg-line" x1="110" y1="380" x2="20" y2="290"></line>'
  ].join("");

  const labels = Object.entries(houseCenters).map(([house, pos]) => {
    const data = chartMap[house] || { sign: "", planets: "" };
    const sign = data.sign || "";
    const planets = wrapText(data.planets || "", 15).map((line, index) => 
      `<text class="svg-planets" x="${pos.x}" y="${pos.y + 20 + (index * 14)}" text-anchor="middle">${escapeXml(line)}</text>`
    ).join("");

    return `
      <text class="svg-house-num" x="${pos.x}" y="${pos.y - 16}" text-anchor="middle">H${house}</text>
      <text class="svg-sign" x="${pos.x}" y="${pos.y}" text-anchor="middle">${escapeXml(sign)}</text>
      ${planets}
    `;
  }).join("");

  return `
    <svg viewBox="0 0 400 400" role="img" aria-label="North Indian chart">
      ${lines}
      ${labels}
    </svg>
  `;
}

function wrapText(text, limit) {
  if (!text) return [];
  const words = text.split(/\s*,\s*|\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    if ((current + (current ? " " : "") + word).length <= limit) {
      current += (current ? " " : "") + word;
    } else {
      if (current) lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return lines.slice(0, 4);
}

function escapeXml(unsafe) {
  return String(unsafe)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function renderChartPayload(chart) {
  currentChart = chart;
  resultsEl.classList.remove("hidden");
  answerBox.classList.add("hidden");
  answerBox.textContent = "";

  document.getElementById("lagnaValue").textContent = `${chart.core.lagna_sign} ${chart.core.lagna_degree}°`;
  document.getElementById("moonValue").textContent = chart.core.moon_sign;
  document.getElementById("nakshatraValue").textContent = `${chart.core.nakshatra} • Pada ${chart.core.pada}`;
  document.getElementById("dashaValue").textContent = chart.vimshottari.current_balance_lord;
  document.getElementById("birthResolved").textContent = chart.birth_details.resolved_place;

  document.getElementById("summaryPersonality").textContent = chart.summary.personality;
  document.getElementById("summaryCareer").textContent = chart.summary.career;
  document.getElementById("summaryRelationships").textContent = chart.summary.relationships;
  document.getElementById("summaryWealth").textContent = chart.summary.wealth;

  document.getElementById("chartD1").innerHTML = buildNorthIndianSvg(chart.rasi_d1);
  document.getElementById("chartD9").innerHTML = buildNorthIndianSvg(chart.navamsa_d9);

  const placementsBody = document.getElementById("placementsBody");
  placementsBody.innerHTML = "";
  Object.entries(chart.planets).forEach(([planet, info]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${planet}${info.retrograde ? " (R)" : ""}</td>
      <td>${info.sign}</td>
      <td>${info.degree}°</td>
      <td>${info.house}</td>
      <td>${info.navamsa_sign} · H${info.navamsa_house}</td>
    `;
    placementsBody.appendChild(tr);
  });

  const dashaTimeline = document.getElementById("dashaTimeline");
  dashaTimeline.innerHTML = "";
  chart.vimshottari.sequence.forEach(item => {
    const div = document.createElement("div");
    div.className = "dasha-item";
    div.innerHTML = `
      <div>
        <strong>${item.lord} Mahadasha</strong>
        <span>${item.start} → ${item.end}</span>
      </div>
      <span>${item.years} years</span>
    `;
    dashaTimeline.appendChild(div);
  });
}

async function createChart(payload) {
  setStatus("Calculating kundli and chart strengths...");
  const response = await fetch(`${apiBase()}/api/chart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Could not generate the chart.");
  }
  renderChartPayload(data);
  setStatus("Kundli generated successfully.", "ok");
}

birthForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await createChart({
      name: document.getElementById("name").value.trim() || "Guest",
      date_of_birth: document.getElementById("date_of_birth").value.trim(),
      time_of_birth: document.getElementById("time_of_birth").value.trim(),
      place_of_birth: document.getElementById("place_of_birth").value.trim()
    });
  } catch (error) {
    setStatus(error.message, "error");
  }
});

demoBtn.addEventListener("click", async () => {
  document.getElementById("name").value = "Guest";
  document.getElementById("date_of_birth").value = "13/05/1980";
  document.getElementById("time_of_birth").value = "20:15";
  document.getElementById("place_of_birth").value = "Pune, Maharashtra, India";
  try {
    await createChart({
      name: "Guest",
      date_of_birth: "13/05/1980",
      time_of_birth: "20:15",
      place_of_birth: "Pune, Maharashtra, India"
    });
  } catch (error) {
    setStatus(error.message, "error");
  }
});

askBtn.addEventListener("click", async () => {
  if (!currentChart) {
    setStatus("Generate the kundli first.", "error");
    return;
  }
  const question = document.getElementById("questionInput").value.trim();
  if (!question) {
    setStatus("Please enter a question.", "error");
    return;
  }

  answerBox.classList.remove("hidden");
  answerBox.textContent = "Consulting the chart...";
  setStatus("Thinking through your chart question...");

  try {
    const response = await fetch(`${apiBase()}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, chart_context: currentChart })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not answer this question.");
    }
    answerBox.textContent = data.answer;
    setStatus("Answer ready.", "ok");
  } catch (error) {
    answerBox.textContent = "";
    answerBox.classList.add("hidden");
    setStatus(error.message, "error");
  }
});

apiConfigBtn.addEventListener("click", () => {
  apiBaseInput.value = apiBase();
  apiDialog.showModal();
});

saveApiBtn.addEventListener("click", (event) => {
  event.preventDefault();
  localStorage.setItem("ipant_api_base", apiBaseInput.value.trim() || defaultApiBase);
  apiDialog.close();
  setStatus(`Backend set to ${apiBase()}`, "ok");
});

setStatus(`Backend: ${apiBase()}`);
