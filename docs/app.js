const state = {
  sessionId: null,
  chart: null,
  freeQuestionUsed: false,
  paidQuestions: 0,
  config: null,
};

const chartForm = document.getElementById('chartForm');
const questionForm = document.getElementById('questionForm');
const lookupPlaceBtn = document.getElementById('lookupPlace');
const confirmPaymentBtn = document.getElementById('confirmPaymentBtn');
const readingOutput = document.getElementById('readingOutput');
const answerOutput = document.getElementById('answerOutput');
const chartCanvas = document.getElementById('chartCanvas');
const birthSummary = document.getElementById('birthSummary');
const sessionBadge = document.getElementById('sessionBadge');
const qrWrap = document.getElementById('qrWrap');
const paymentStatus = document.getElementById('paymentStatus');
const upiInfo = document.getElementById('upiInfo');
const headline = document.getElementById('headline');

async function fetchConfig() {
  const response = await fetch('/api/config');
  const data = await response.json();
  state.config = data;
  headline.textContent = data.headline;
}

async function lookupPlaceDetails() {
  const place = document.getElementById('place').value.trim();
  if (!place) {
    alert('Enter a place first.');
    return;
  }

  lookupPlaceBtn.disabled = true;
  lookupPlaceBtn.textContent = 'Looking up...';

  try {
    const geoResp = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(place)}&count=1&language=en&format=json`);
    const geoData = await geoResp.json();
    const result = geoData?.results?.[0];
    if (!result) throw new Error('Location not found.');

    document.getElementById('latitude').value = result.latitude;
    document.getElementById('longitude').value = result.longitude;
    if (result.timezone) document.getElementById('timezone').value = result.timezone;
  } catch (error) {
    alert(error.message || 'Unable to look up that place. Enter latitude, longitude, and timezone manually.');
  } finally {
    lookupPlaceBtn.disabled = false;
    lookupPlaceBtn.textContent = 'Lookup place details';
  }
}

function formatPlanet(planet) {
  return `${planet.name} — ${planet.sign} ${planet.degree_in_sign}°${planet.retrograde ? ' ℞' : ''}`;
}

function renderSummary(chart) {
  const details = chart.birth_details;
  birthSummary.classList.remove('empty');
  birthSummary.innerHTML = `
    <strong>${details.name || 'Guest'}</strong><br />
    ${details.date_of_birth} • ${details.birth_time} • ${details.place}<br />
    Coordinates: ${details.latitude}, ${details.longitude} • ${details.timezone}<br />
    <br />
    <strong>Moon sign:</strong> ${chart.moon_sign}<br />
    <strong>Ascendant:</strong> ${chart.ascendant.sign} ${chart.ascendant.degree}°<br />
    <strong>Nakshatra:</strong> ${chart.nakshatra}<br />
    <strong>System:</strong> ${chart.system}
  `;
}

function renderChart(chart) {
  chartCanvas.classList.remove('empty');
  const houses = Array.from({ length: 12 }, (_, index) => {
    const houseNumber = index + 1;
    const housePlanets = chart.house_map[houseNumber] || [];
    const cuspLongitude = chart.houses[index] ?? 0;
    const signIndex = Math.floor(cuspLongitude / 30) % 12;
    const sign = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'][signIndex];
    return `
      <div class="house">
        <strong>House ${houseNumber}</strong>
        <span class="sign">Cusp sign: ${sign}</span>
        <ul>
          ${housePlanets.length ? housePlanets.map(item => `<li>${item}</li>`).join('') : '<li>—</li>'}
        </ul>
      </div>
    `;
  }).join('');
  chartCanvas.innerHTML = `<div class="chart-grid">${houses}</div>`;
}

function renderReading(text) {
  readingOutput.classList.remove('empty');
  readingOutput.textContent = text;
}

function renderAnswer(text) {
  answerOutput.classList.remove('empty');
  answerOutput.textContent = text;
}

async function loadQr() {
  if (!state.sessionId) return;
  const response = await fetch(`/api/payment/qr?amount=1&session_id=${encodeURIComponent(state.sessionId)}`);
  const data = await response.json();
  qrWrap.classList.remove('empty');
  qrWrap.innerHTML = `<img src="${data.qr_data_uri}" alt="UPI QR code for ₹1 unlock" />`;
  upiInfo.innerHTML = `UPI: <strong>${state.config.upi_id}</strong><br />Amount: ₹1 per question unlock`;
}

chartForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    name: document.getElementById('name').value.trim(),
    place: document.getElementById('place').value.trim(),
    date_of_birth: document.getElementById('dob').value.trim(),
    birth_time: document.getElementById('birthTime').value.trim(),
    latitude: Number(document.getElementById('latitude').value),
    longitude: Number(document.getElementById('longitude').value),
    timezone: document.getElementById('timezone').value.trim(),
  };

  if (!payload.place || !payload.date_of_birth || !payload.birth_time || Number.isNaN(payload.latitude) || Number.isNaN(payload.longitude)) {
    alert('Please complete the birth details, including latitude and longitude.');
    return;
  }

  const button = chartForm.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = 'Generating chart...';

  try {
    const response = await fetch('/api/chart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Unable to generate chart.');

    state.sessionId = data.session_id;
    state.chart = data.chart;
    state.freeQuestionUsed = data.free_question_used;
    state.paidQuestions = data.paid_questions;
    sessionBadge.textContent = `Session ${state.sessionId.slice(0, 8)}`;
    renderSummary(data.chart);
    renderChart(data.chart);
    renderReading(data.reading);
    paymentStatus.textContent = 'Your first question is free. After that, each next answer unlocks for ₹1.';
    await loadQr();
  } catch (error) {
    alert(error.message || 'Something went wrong.');
  } finally {
    button.disabled = false;
    button.textContent = 'Generate my chart';
  }
});

questionForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.sessionId) {
    alert('Generate your chart first.');
    return;
  }

  const question = document.getElementById('questionInput').value.trim();
  if (!question) {
    alert('Please enter a question.');
    return;
  }

  const button = questionForm.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = 'Asking...';

  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId, question }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Unable to answer right now.');
    renderAnswer(data.answer);
    state.freeQuestionUsed = data.free_question_used;
    state.paidQuestions = data.paid_questions;
    paymentStatus.textContent = data.requires_payment_next
      ? `Free question used. Paid unlocks remaining: ${state.paidQuestions}.`
      : `Paid unlocks remaining: ${state.paidQuestions}.`;
  } catch (error) {
    renderAnswer(error.message || 'Unable to answer.');
  } finally {
    button.disabled = false;
    button.textContent = 'Ask now';
  }
});

confirmPaymentBtn.addEventListener('click', async () => {
  if (!state.sessionId) {
    alert('Generate your chart first.');
    return;
  }
  confirmPaymentBtn.disabled = true;
  confirmPaymentBtn.textContent = 'Confirming...';
  try {
    const response = await fetch('/api/payment/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Payment confirmation failed.');
    state.paidQuestions = data.paid_questions;
    paymentStatus.innerHTML = `<span class="success">${data.message} Paid unlocks available: ${state.paid_questions}.</span>`;
  } catch (error) {
    paymentStatus.innerHTML = `<span class="error">${error.message || 'Payment confirmation failed.'}</span>`;
  } finally {
    confirmPaymentBtn.disabled = false;
    confirmPaymentBtn.textContent = 'I have paid ₹1';
  }
});

lookupPlaceBtn.addEventListener('click', lookupPlaceDetails);
fetchConfig();
