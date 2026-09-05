// Configurable Backend API URL (Option 1 Deployment)
const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
    ? "http://127.0.0.1:8000" 
    : "https://global-macroforecast.onrender.com";

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

function setTrend(el, annRate, nextQtr, isAnnual = false) {
    clearElement(el);
    const prefix = isAnnual ? "Annual ~" : "Annualized ~";
    const baseText = document.createTextNode(prefix + annRate.toFixed(1) + "% ");
    el.appendChild(baseText);

    const span = document.createElement("span");
    if (nextQtr > 0.2) {
        span.className = "trend-up";
        span.textContent = "▲ Expansion";
    } else if (nextQtr < 0) {
        span.className = "trend-down";
        span.textContent = "▼ Contraction";
    } else {
        span.className = "trend-flat";
        span.textContent = "▶ Stagnation";
    }
    el.appendChild(span);
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

        chartTitle.textContent = COUNTRY_TITLES[country] + " - 8-Quarter Forecast";
        expandCard(country);
    });
});

function collapseAll() {
    currentCountry = null;
    cards.forEach(c => c.classList.remove("active"));
    chartWrapper.classList.remove("visible");
    chartWrapper.classList.add("hidden");
}

// --- FETCH DATA (Option 1 Hybrid Caching & Graceful Degradation) ---
let cachedStaticData = null;
let cachedApiData = {};

async function fetchData(country) {
    if (cachedApiData[country]) {
        return cachedApiData[country];
    }

    try {
        // Attempt to fetch from live FastAPI endpoint (cached for 24h by backend Cache-Control header)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 4000); // 4s timeout for cloud cold-starts

        const res = await fetch(`${API_BASE_URL}/api/dashboard/${country}`, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!res.ok) throw new Error(`API status ${res.status}`);
        const apiData = await res.json();
        cachedApiData[country] = apiData;
        return apiData;
    } catch (error) {
        console.warn(`Live API unreachable or cold-starting (${error.message}). Gracefully falling back to static forecasts.json...`);
        try {
            if (!cachedStaticData) {
                const res = await fetch(STATIC_DATA_URL);
                if (!res.ok) throw new Error("Failed to load static forecasts.json");
                cachedStaticData = await res.json();
            }
            if (cachedStaticData[country]) {
                return cachedStaticData[country];
            }
        } catch (staticErr) {
            console.error("Both live API and static JSON failed for " + country, staticErr);
            throw staticErr;
        }
    }
}

// --- INITIAL LOAD ---
async function initializeCards() {
    for (const c of ["us", "germany", "japan", "india"]) {
        try {
            const data = await fetchData(c);

            const nextQtr = data.forecast[0].ensemble_pred;
            const valEl = document.getElementById("val-" + c);
            const trendEl = document.getElementById("trend-" + c);
            const rmseEl = document.getElementById("rmse-" + c);

            valEl.textContent = (nextQtr > 0 ? "+" : "") + nextQtr.toFixed(2) + "%";

            const r = nextQtr / 100.0;
            const annRate = (Math.pow(1 + r, 4) - 1) * 100.0;
            setTrend(trendEl, annRate, nextQtr, false);

            rmseEl.textContent = data.metrics.ensemble_rmse.toFixed(2) + "%";
        } catch (err) {
            console.error("Failed to initialize card for " + c, err);
        }
    }
}

// --- EXPAND CARD LOGIC ---
async function expandCard(country) {
    chartWrapper.classList.remove("hidden");
    chartWrapper.classList.add("visible");

    try {
        const data = await fetchData(country);
        drawChart(data);
    } catch (err) {
        console.error("Failed to expand card for " + country, err);
    }
}

// --- CHART.JS ---
function drawChart(data) {
    const ctx = document.getElementById("gdpChart").getContext("2d");

    const histDates = Object.keys(data.history);
    const histValues = Object.values(data.history);

    const fcDates = data.forecast.map(d => d.date);
    const fcValues = data.forecast.map(d => d.ensemble_pred);

    const allLabels = [...histDates, ...fcDates];
    const historyData = [...histValues, ...Array(fcDates.length).fill(null)];

    const lastHistValue = histValues[histValues.length - 1];
    const forecastData = [...Array(histDates.length - 1).fill(null), lastHistValue, ...fcValues];

    if (chartInstance) {
        chartInstance.destroy();
    }

    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const tickColor = isLight ? "#475569" : "#94A3B8";
    const gridColor = isLight ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.06)";
    const tooltipBg = isLight ? "rgba(255, 255, 255, 0.98)" : "rgba(30, 41, 59, 0.98)";
    const tooltipTitle = isLight ? "#0F172A" : "#F8FAFC";
    const tooltipBody = isLight ? "#059669" : "#34D399";

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: "Historical GDP",
                    data: historyData,
                    borderColor: isLight ? "#2563EB" : "#60A5FA",
                    backgroundColor: isLight ? "rgba(37, 99, 235, 0.1)" : "rgba(96, 165, 250, 0.15)",
                    borderWidth: 2.5,
                    pointBackgroundColor: isLight ? "#FFFFFF" : "#1E293B",
                    pointBorderColor: isLight ? "#2563EB" : "#60A5FA",
                    pointRadius: 4,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: "Forecast",
                    data: forecastData,
                    borderColor: isLight ? "#059669" : "#34D399",
                    borderWidth: 2.5,
                    borderDash: [5, 5],
                    pointBackgroundColor: isLight ? "#059669" : "#34D399",
                    pointRadius: 5,
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: "index",
                    intersect: false,
                    backgroundColor: tooltipBg,
                    titleColor: tooltipTitle,
                    bodyColor: tooltipBody,
                    borderColor: isLight ? "rgba(108, 92, 231, 0.25)" : "rgba(157, 141, 241, 0.4)",
                    borderWidth: 1,
                    padding: 12
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor, drawBorder: false },
                    ticks: { color: tickColor, maxTicksLimit: 12 }
                },
                y: {
                    grid: {
                        color: (context) => context.tick.value === 0 ? (isLight ? "rgba(13, 148, 136, 0.4)" : "rgba(28, 254, 186, 0.4)") : gridColor,
                        lineWidth: (context) => context.tick.value === 0 ? 2 : 1,
                        drawBorder: false
                    },
                    ticks: {
                        color: tickColor,
                        callback: function(value) { return value + "%"; }
                    }
                }
            },
            interaction: { mode: "nearest", axis: "x", intersect: false }
        }
    });
}

// --- FLOATING PARTICLES LOGIC ---
function initParticles() {
    const container = document.getElementById('particles-container');
    if (!container) return;

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
