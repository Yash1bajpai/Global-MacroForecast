// Static Data URL for Vercel Deployment Fallback
const STATIC_DATA_URL = "data/forecasts.json";

// Standardized country names for UI
const COUNTRY_TITLES = {
    us: "United States",
    germany: "Germany",
    japan: "Japan",
    india: "India"
};

// --- GLOBAL VARIABLES ---
let currentCountry = null;
let chartInstance = null;

// --- DOM ELEMENTS ---
const cards = document.querySelectorAll(".country-card");
const chartWrapper = document.getElementById("chart-wrapper");
const chartTitle = document.getElementById("chart-title");

// --- SAFE DOM HELPER ---
function clearElement(el) {
    while (el.firstChild) {
        el.removeChild(el.firstChild);
    }
}

// --- EVENT LISTENERS ---
cards.forEach(card => {
    card.addEventListener("click", (e) => {
        const country = e.currentTarget.dataset.country;

        if (currentCountry === country) {
            collapseAll();
            return;
        }

        currentCountry = country;
        cards.forEach(c => c.classList.remove("active"));
        e.currentTarget.classList.add("active");

        expandCard(country);
    });
});

function collapseAll() {
    currentCountry = null;
    cards.forEach(c => c.classList.remove("active"));
    chartWrapper.classList.remove("visible");
    chartWrapper.classList.add("hidden");
}

// --- DATA (history only) ---
// Forecasts are paused while the models are under repair. This page reads only
// the bundled reported-history snapshot and never calls a forecast endpoint.
const COUNTRIES = ["us", "germany", "japan", "india"];

let cachedStaticData = null;

const apiStatusText = document.getElementById("api-status-text");
const apiStatusBadge = apiStatusText ? apiStatusText.parentElement : null;

function hasHistory(data) {
    return !!(data && typeof data === "object" && data.history &&
        Object.keys(data.history).length > 0 &&
        Object.values(data.history).every((v) => typeof v === "number"));
}

function quarterLabel(isoDate) {
    const d = new Date(isoDate + "T00:00:00Z");
    return "Q" + (Math.floor(d.getUTCMonth() / 3) + 1) + " " + d.getUTCFullYear();
}

async function fetchStaticData() {
    if (cachedStaticData) return cachedStaticData;
    const res = await fetch(STATIC_DATA_URL);
    if (!res.ok) throw new Error(`History snapshot failed (HTTP ${res.status})`);
    cachedStaticData = await res.json();
    return cachedStaticData;
}

function renderCard(country, data) {
    if (!hasHistory(data)) return;
    const valEl = document.getElementById("val-" + country);
    const trendEl = document.getElementById("trend-" + country);
    if (!valEl || !trendEl) return;
    const dates = Object.keys(data.history);
    const last = data.history[dates[dates.length - 1]];
    valEl.textContent = (last > 0 ? "+" : "") + last.toFixed(2) + "%";
    trendEl.textContent = "Reported QoQ growth, " + quarterLabel(dates[dates.length - 1]);
}

async function initializeCards() {
    if (apiStatusText) apiStatusText.textContent = "Forecasts paused (under repair)";
    if (apiStatusBadge) apiStatusBadge.classList.add("api-fallback");
    try {
        const all = await fetchStaticData();
        for (const c of COUNTRIES) renderCard(c, all[c]);
    } catch (err) {
        console.error("History snapshot unavailable.", err);
    }
}

// --- EXPAND CARD LOGIC ---
function expandCard(country) {
    chartWrapper.classList.remove("hidden");
    chartWrapper.classList.add("visible");
    chartTitle.textContent = COUNTRY_TITLES[country] + " - Recent GDP growth (reported)";
    fetchStaticData().then((all) => {
        if (currentCountry !== country || !hasHistory(all[country])) return;
        drawChart(all[country]);
    }).catch((err) => console.error(`No history for ${country}.`, err));
}

// --- CHART.JS (history only) ---
function drawChart(data) {
    if (!hasHistory(data)) return;
    const ctx = document.getElementById("gdpChart").getContext("2d");
    const histDates = Object.keys(data.history);
    const histValues = Object.values(data.history);
    if (chartInstance) chartInstance.destroy();

    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const tickColor = isLight ? "#475569" : "#94A3B8";
    const gridColor = isLight ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.06)";
    const tooltipBg = isLight ? "rgba(255, 255, 255, 0.98)" : "rgba(30, 41, 59, 0.98)";
    const tooltipTitle = isLight ? "#0F172A" : "#F8FAFC";

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: histDates.map(quarterLabel),
            datasets: [{
                label: "Reported QoQ GDP growth",
                data: histValues,
                borderColor: isLight ? "#2563EB" : "#60A5FA",
                backgroundColor: isLight ? "rgba(37, 99, 235, 0.1)" : "rgba(96, 165, 250, 0.15)",
                borderWidth: 2.5,
                pointBackgroundColor: isLight ? "#FFFFFF" : "#1E293B",
                pointBorderColor: isLight ? "#2563EB" : "#60A5FA",
                pointRadius: 4,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: "index", intersect: false,
                    backgroundColor: tooltipBg, titleColor: tooltipTitle,
                    bodyColor: isLight ? "#1D4ED8" : "#93C5FD",
                    borderWidth: 1, padding: 12,
                    callbacks: { label: (c) => c.parsed.y.toFixed(2) + "%" }
                }
            },
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: tickColor, maxTicksLimit: 12 } },
                y: { grid: { color: gridColor }, ticks: { color: tickColor, callback: (v) => v + "%" } }
            },
            interaction: { mode: "nearest", axis: "x", intersect: false }
        }
    });
}

// --- FLOATING PARTICLES LOGIC ---
function initParticles() {
    const container = document.getElementById('particles-container');
    if (!container) return;
    // The container is display:none in the shipped theme; skip mounting
    // 25 animated elements whose requestAnimationFrame loops would burn CPU
    // while invisible.
    if (getComputedStyle(container).display === 'none') return;

    const symbols = ['%', '📈', '$', '€', '¥', '₹', '📉'];
    const particleCount = 25; // Increased slightly

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'econ-particle';
        particle.textContent = symbols[Math.floor(Math.random() * symbols.length)];
        
        const size = Math.random() * 2 + 1.5; // 1.5rem to 3.5rem
        particle.style.fontSize = `${size}rem`;
        
        container.appendChild(particle);

        // Initial random position
        let x = Math.random() * window.innerWidth;
        let y = Math.random() * window.innerHeight;
        
        // Random velocity (drift)
        let vx = (Math.random() - 0.5) * 1.2; 
        let vy = (Math.random() - 0.5) * 1.2; 
        
        // Random rotation
        let rot = Math.random() * 360;
        let vRot = (Math.random() - 0.5) * 1.5;

        function animate() {
            x += vx;
            y += vy;
            rot += vRot;

            // Bounce off edges (with a 100px buffer so they don't pop out abruptly)
            if (x < -100) vx = Math.abs(vx);
            if (x > window.innerWidth + 100) vx = -Math.abs(vx);
            if (y < -100) vy = Math.abs(vy);
            if (y > window.innerHeight + 100) vy = -Math.abs(vy);

            particle.style.transform = `translate(${x}px, ${y}px) rotate(${rot}deg)`;
            requestAnimationFrame(animate);
        }
        
        // Start animation
        animate();
    }
}

function initThemeSwitcher() {
    const themeBtn = document.getElementById("theme-toggle-btn");
    const themeIcon = document.getElementById("theme-icon");
    const themeText = document.getElementById("theme-text");
    if (!themeBtn) return;

    let currentTheme = localStorage.getItem("macro_theme") || "dark";
    applyTheme(currentTheme);

    themeBtn.addEventListener("click", () => {
        currentTheme = currentTheme === "dark" ? "light" : "dark";
        localStorage.setItem("macro_theme", currentTheme);
        applyTheme(currentTheme);
        const activeCard = document.querySelector(".country-card.active");
        if (activeCard) {
            expandCard(activeCard.dataset.country);
        }
    });

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        if (theme === "light") {
            if (themeIcon) themeIcon.textContent = "🌙";
            if (themeText) themeText.textContent = "Dark Mode";
        } else {
            if (themeIcon) themeIcon.textContent = "☀️";
            if (themeText) themeText.textContent = "Light Mode";
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initThemeSwitcher();
    initializeCards();
    initParticles();
});
