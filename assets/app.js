const CATEGORY_META = {
  "Workshop":        { color: "#D9A441", icon: "🧩" },
  "Open Day":        { color: "#5C8AA3", icon: "🚪" },
  "Teatro":          { color: "#A8452B", icon: "🎭" },
  "Letture Animate": { color: "#2F5D50", icon: "📖" },
  "Event":           { color: "#8C8272", icon: "🎉" }
};
const CITIES = ["Orbassano", "Rivalta di Torino", "Rivoli"];
const CATEGORIES = Object.keys(CATEGORY_META);

let ACTIVITIES = [];
let selectedCities = new Set();
let selectedCategories = new Set();
let calYear, calMonth;

async function loadActivities(){
  const res = await fetch('data/activities.json');
  ACTIVITIES = await res.json();
}

function fmtDateIt(dateStr, time){
  const d = new Date(dateStr + "T" + time + ":00");
  return d.toLocaleDateString('it-IT', {weekday:'long', day:'numeric', month:'long'}) + " · " + time;
}

function gcalLink(a){
  const start = new Date(a.date + "T" + a.time + ":00");
  const end = new Date(start.getTime() + (a.durationMin || 60) * 60000);
  const fmt = d => d.getFullYear().toString() + String(d.getMonth()+1).padStart(2,'0') + String(d.getDate()).padStart(2,'0')
    + "T" + String(d.getHours()).padStart(2,'0') + String(d.getMinutes()).padStart(2,'0') + "00";
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: a.title,
    dates: fmt(start) + "/" + fmt(end),
    details: a.desc + " — " + a.venue,
    location: a.venue + ", " + a.city,
    ctz: "Europe/Rome"
  });
  return "https://calendar.google.com/calendar/render?" + params.toString();
}

function cardHtml(a){
  const meta = CATEGORY_META[a.category] || CATEGORY_META["Event"];
  const imageBlock = a.image
    ? `<img class="card-image" src="${a.image}" alt="">`
    : `<div class="card-image" style="--cat-color:${meta.color}">${meta.icon}</div>`;
  return `
  <article class="card" style="--cat-color:${meta.color}">
    ${imageBlock}
    <div class="card-body">
      <div class="card-top">
        <span class="cat-dot"></span>
        <span class="cat-name">${a.category}</span>
      </div>
      <h3>${a.title}</h3>
      <p class="desc">${a.desc}</p>
      <div class="meta">
        <span>📍 ${a.venue}, ${a.city}</span>
        <span>🗓️ ${fmtDateIt(a.date, a.time)}</span>
        <span>👧🧒 ${a.ageMin}–${a.ageMax} anni</span>
      </div>
      <div class="card-actions">
        <a class="btn btn-primary" href="${gcalLink(a)}" target="_blank" rel="noopener">+ Google Calendar</a>
        <a class="btn btn-ghost" href="${a.link}" target="_blank" rel="noopener">Fonte</a>
      </div>
    </div>
  </article>`;
}

function matchesFilters(a){
  const cityOk = selectedCities.size === 0 || selectedCities.has(a.city);
  const catOk = selectedCategories.size === 0 || selectedCategories.has(a.category);
  return cityOk && catOk;
}

function renderChips(){
  const cityBox = document.getElementById('city-chips');
  cityBox.innerHTML = CITIES.map(c =>
    `<button class="chip" data-type="city" data-value="${c}" aria-pressed="${selectedCities.has(c)}">${c}</button>`
  ).join('');
  const catBox = document.getElementById('category-chips');
  catBox.innerHTML = CATEGORIES.map(c =>
    `<button class="chip" data-type="category" data-value="${c}" aria-pressed="${selectedCategories.has(c)}">${CATEGORY_META[c].icon} ${c}</button>`
  ).join('');
  document.querySelectorAll('.chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const set = btn.dataset.type === 'city' ? selectedCities : selectedCategories;
      const v = btn.dataset.value;
      set.has(v) ? set.delete(v) : set.add(v);
      renderChips();
      renderCards();
    });
  });
}

function renderCards(){
  const grid = document.getElementById('card-grid');
  const list = ACTIVITIES.filter(matchesFilters);
  grid.innerHTML = list.map(cardHtml).join('') || '<p>Nessuna attività trovata con questi filtri.</p>';
}

function renderCalendar(){
  const label = document.getElementById('calendarLabel');
  const first = new Date(calYear, calMonth, 1);
  label.textContent = first.toLocaleDateString('it-IT', {month:'long', year:'numeric'});
  const grid = document.getElementById('calendarGrid');
  const weekdays = ['Lun','Mar','Mer','Gio','Ven','Sab','Dom'];
  let html = weekdays.map(w => `<div class="cal-weekday">${w}</div>`).join('');

  const startWeekday = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();

  for (let i = 0; i < startWeekday; i++) html += `<div class="cal-day empty"></div>`;

  for (let day = 1; day <= daysInMonth; day++){
    const dateStr = `${calYear}-${String(calMonth+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
    const dayActs = ACTIVITIES.filter(a => a.date === dateStr);
    const chips = dayActs.map(a =>
      `<button class="cal-event-chip" style="background:${(CATEGORY_META[a.category]||CATEGORY_META["Event"]).color}" data-id="${a.id}">${a.time} ${a.title}</button>`
    ).join('');
    html += `<div class="cal-day"><div class="cal-daynum">${day}</div><div class="cal-events">${chips}</div></div>`;
  }
  grid.innerHTML = html;

  document.querySelectorAll('.cal-event-chip').forEach(chip => {
    chip.addEventListener('click', () => openPanel(ACTIVITIES.find(a => a.id == chip.dataset.id)));
  });
}

function openPanel(a){
  const content = document.getElementById('panelContent');
  content.innerHTML = `<div class="panel-item">${cardHtml(a)}</div>`;
  document.getElementById('detailPanel').classList.add('open');
  document.getElementById('detailPanel').setAttribute('aria-hidden', 'false');
  document.getElementById('panelOverlay').classList.add('open');
}
function closePanel(){
  document.getElementById('detailPanel').classList.remove('open');
  document.getElementById('detailPanel').setAttribute('aria-hidden', 'true');
  document.getElementById('panelOverlay').classList.remove('open');
}

async function initNewsPage(){
  await loadActivities();
  renderChips();
  renderCards();
}

async function initCalendarPage(){
  await loadActivities();
  const today = new Date();
  if (ACTIVITIES.length){
    const d = new Date(ACTIVITIES[0].date);
    calYear = d.getFullYear(); calMonth = d.getMonth();
  } else {
    calYear = today.getFullYear(); calMonth = today.getMonth();
  }
  renderCalendar();
  document.getElementById('panelClose').addEventListener('click', closePanel);
  document.getElementById('panelOverlay').addEventListener('click', closePanel);
  document.getElementById('prevMonth').addEventListener('click', () => {
    calMonth--; if (calMonth < 0){ calMonth = 11; calYear--; } renderCalendar();
  });
  document.getElementById('nextMonth').addEventListener('click', () => {
    calMonth++; if (calMonth > 11){ calMonth = 0; calYear++; } renderCalendar();
  });
}

if (document.getElementById('card-grid')) initNewsPage();
if (document.getElementById('calendarGrid')) initCalendarPage();
