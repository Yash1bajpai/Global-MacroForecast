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

// --- MOCK DATA FOR INDEPENDENT UI TESTING ---
const MOCK_DATA = {
    "us": {
        "history": {
            "2021-04-01": 1.6875713541763204,
            "2021-07-01": 0.8216679141918704,
            "2021-10-01": 1.701202308971439,
            "2022-01-01": -0.2551237912953752,
            "2022-04-01": 0.1564245950852694,
            "2022-07-01": 0.719306332529257,
            "2022-10-01": 0.6878691350323152,
            "2023-01-01": 0.7212436699248315,
            "2023-04-01": 0.6259090548015322,
            "2023-07-01": 1.1470027396091709,
            "2023-10-01": 0.8405149026469161,
            "2024-01-01": 0.2096414414644698,
            "2024-04-01": 0.8815888542736516,
            "2024-07-01": 0.8213953149049047,
            "2024-10-01": 0.4588204928330341,
            "2025-01-01": -0.1626486056421683,
            "2025-04-01": 0.9415531607956495,
            "2025-07-01": 1.0705948402604193,
            "2025-10-01": 0.1202722552804402,
            "2026-01-01": 0.4020341702936747
        },
        "metrics": {
            "ensemble_rmse": 2.3009,
            "ensemble_mae": 1.1249,
            "w_sarima": 0.489,
            "w_lgbm": 0.511
        },
        "forecast": [
            {
                "date": "2026-04-01",
                "quarter": "Q2-2026",
                "ensemble_pred": 0.4710181272471546,
                "lgbm_pred": 0.569931493786407,
                "sarima_pred": 0.36765467059775175,
                "ci_low": -0.7040917342389401,
                "ci_high": 1.4394010754344435
            },
            {
                "date": "2026-07-01",
                "quarter": "Q3-2026",
                "ensemble_pred": 0.498449461770615,
                "lgbm_pred": 0.6522252320322084,
                "sarima_pred": 0.33775535419663916,
                "ci_low": -0.8187211668859162,
                "ci_high": 1.4942318752791945
            },
            {
                "date": "2026-10-01",
                "quarter": "Q4-2026",
                "ensemble_pred": 0.4390206854416715,
                "lgbm_pred": 0.5622114620909654,
                "sarima_pred": 0.3102875834625526,
                "ci_low": -0.9131405726830754,
                "ci_high": 1.5337157396081804
            },
            {
                "date": "2027-01-01",
                "quarter": "Q1-2027",
                "ensemble_pred": 0.4745908559112879,
                "lgbm_pred": 0.6559679814790879,
                "sarima_pred": 0.28505361426477294,
                "ci_low": -0.9921513571849788,
                "ci_high": 1.5622585857145248
            },
            {
                "date": "2027-04-01",
                "quarter": "Q2-2027",
                "ensemble_pred": 0.3902319206579483,
                "lgbm_pred": 0.5130657892908331,
                "sarima_pred": 0.26187178390661053,
                "ci_low": -1.0590164080859648,
                "ci_high": 1.5827599758991857
            },
            {
                "date": "2027-07-01",
                "quarter": "Q3-2027",
                "ensemble_pred": 0.4276108948557833,
                "lgbm_pred": 0.6065941691515684,
                "sarima_pred": 0.24057520331151713,
                "ci_low": -1.1160860558867787,
                "ci_high": 1.597236462509813
            },
            {
                "date": "2027-10-01",
                "quarter": "Q4-2027",
                "ensemble_pred": 0.4029422938404388,
                "lgbm_pred": 0.5770413545370722,
                "sarima_pred": 0.2210105555664518,
                "ci_low": -1.1651237179488239,
                "ci_high": 1.6071448290817276
            },
            {
                "date": "2028-01-01",
                "quarter": "Q1-2028",
                "ensemble_pred": 0.44256190742451945,
                "lgbm_pred": 0.6717745954048834,
                "sarima_pred": 0.20303699217305524,
                "ci_low": -1.2074923511717848,
                "ci_high": 1.6135663355178953
            }
        ]
    },
    "germany": {
        "history": {
            "2021-04-01": 2.3233038841798503,
            "2021-07-01": 0.0864426274667096,
            "2021-10-01": 0.5362000012505419,
            "2022-01-01": 0.6757112682674205,
            "2022-04-01": 0.1516367733128021,
            "2022-07-01": 0.2931588586013944,
            "2022-10-01": -0.3499940863635586,
            "2023-01-01": -0.4725392774176384,
            "2023-04-01": -0.0762116182423611,
            "2023-07-01": 1.3030364343080691e-05,
            "2023-10-01": -0.2767043616906051,
            "2024-01-01": -0.1075425802792295,
            "2024-04-01": -0.2585829132620176,
            "2024-07-01": 0.0191714096384743,
            "2024-10-01": 0.182010753692019,
            "2025-01-01": 0.3725368286565,
            "2025-04-01": -0.2004333297815463,
            "2025-07-01": -0.0382109192479163,
            "2025-10-01": 0.2386442490294626,
            "2026-01-01": 0.3426606754983297
        },
        "metrics": {
            "ensemble_rmse": 2.4179,
            "ensemble_mae": 1.1262,
            "w_sarima": 0.47,
            "w_lgbm": 0.53
        },
        "forecast": [
            {
                "date": "2026-04-01",
                "quarter": "Q2-2026",
                "ensemble_pred": 0.45076416093037386,
                "lgbm_pred": 0.7376334165134913,
                "sarima_pred": 0.1272732982515392,
                "ci_low": -1.5776609400760375,
                "ci_high": 1.832207536579116
            },
            {
                "date": "2026-07-01",
                "quarter": "Q3-2026",
                "ensemble_pred": 0.3850356688568159,
                "lgbm_pred": 0.6537966060525294,
                "sarima_pred": 0.08196482478505382,
                "ci_low": -1.7006502098315537,
                "ci_high": 1.8645798594016612
            },
            {
                "date": "2026-10-01",
                "quarter": "Q4-2026",
                "ensemble_pred": 0.5036862404212024,
                "lgbm_pred": 0.9035412808300951,
                "sarima_pred": 0.05278587570479124,
                "ci_low": -1.7610710828107845,
                "ci_high": 1.866642834220367
            },
            {
                "date": "2027-01-01",
                "quarter": "Q1-2027",
                "ensemble_pred": 0.46399791911258315,
                "lgbm_pred": 0.845321755232442,
                "sarima_pred": 0.0339944443391253,
                "ci_low": -1.7926631667754833,
                "ci_high": 1.860652055453734
            },
            {
                "date": "2027-04-01",
                "quarter": "Q2-2027",
                "ensemble_pred": 0.4320428685256874,
                "lgbm_pred": 0.7957609944986509,
                "sarima_pred": 0.021892641364686036,
                "ci_low": -1.810047726656933,
                "ci_high": 1.8538330093863051
            },
            {
                "date": "2027-07-01",
                "quarter": "Q3-2027",
                "ensemble_pred": 0.477032465713339,
                "lgbm_pred": 0.8875583673091342,
                "sarima_pred": 0.0140990022116977,
                "ci_low": -1.8200278952007187,
                "ci_high": 1.8482258996241143
            },
            {
                "date": "2027-10-01",
                "quarter": "Q4-2027",
                "ensemble_pred": 0.4053698919789974,
                "lgbm_pred": 0.7567969118093164,
                "sarima_pred": 0.009079848340552551,
                "ci_low": -1.8259531353308067,
                "ci_high": 1.8441128320119118
            },
            {
                "date": "2028-01-01",
                "quarter": "Q1-2028",
                "ensemble_pred": 0.5038990985128141,
                "lgbm_pred": 0.9455675141477338,
                "sarima_pred": 0.005847480881947294,
                "ci_low": -1.8295611656752193,
                "ci_high": 1.841256127439114
            }
        ]
    },
    "japan": {
        "history": {
            "2021-04-01": 0.6981320861,
            "2021-07-01": -0.142902614,
            "2021-10-01": 1.1971655649,
            "2022-01-01": -0.3250008384,
            "2022-04-01": 0.9068461421,
            "2022-07-01": -0.3597802362,
            "2022-10-01": 0.4634436375,
            "2023-01-01": 0.8159416022,
            "2023-04-01": 0.0795630149,
            "2023-07-01": -1.3660923089,
            "2023-10-01": 0.5289645209,
            "2024-01-01": -0.2995330162,
            "2024-04-01": -0.0209113219,
            "2024-07-01": 0.6834865651,
            "2024-10-01": 0.3481387861,
            "2025-01-01": 0.5073262254,
            "2025-04-01": 0.270451708,
            "2025-07-01": -0.5874929249,
            "2025-10-01": 0.1842364822,
            "2026-01-01": 0.4526321206
        },
        "metrics": {
            "ensemble_rmse": 1.6153,
            "ensemble_mae": 0.9673,
            "w_sarima": 0.437,
            "w_lgbm": 0.563
        },
        "forecast": [
            {
                "date": "2026-04-01",
                "quarter": "Q2-2026",
                "ensemble_pred": 0.35039629809537515,
                "lgbm_pred": 0.5421744496601532,
                "sarima_pred": 0.10332284424876198,
                "ci_low": -1.8823409567839051,
                "ci_high": 2.088986645281429
            },
            {
                "date": "2026-07-01",
                "quarter": "Q3-2026",
                "ensemble_pred": 0.2738906883452243,
                "lgbm_pred": 0.45918677584307854,
                "sarima_pred": 0.03516826898300025,
                "ci_low": -1.9985540858187762,
                "ci_high": 2.068890623784777
            },
            {
                "date": "2026-10-01",
                "quarter": "Q4-2026",
                "ensemble_pred": 0.2221894809794466,
                "lgbm_pred": 0.38536137244438917,
                "sarima_pred": 0.011970316460538949,
                "ci_low": -2.0272465838649696,
                "ci_high": 2.0511872167860474
            },
            {
                "date": "2027-01-01",
                "quarter": "Q1-2027",
                "ensemble_pred": 0.2663708361616817,
                "lgbm_pred": 0.46996507507297414,
                "sarima_pred": 0.0040743681821449025,
                "ci_low": -2.035778138004203,
                "ci_high": 2.0439268743684926
            },
            {
                "date": "2027-04-01",
                "quarter": "Q2-2027",
                "ensemble_pred": 0.26996511810854423,
                "lgbm_pred": 0.4784353197226744,
                "sarima_pred": 0.0013868034432004768,
                "ci_low": -2.03853932712608,
                "ci_high": 2.041312934012481
            },
            {
                "date": "2027-07-01",
                "quarter": "Q3-2027",
                "ensemble_pred": 0.26956536208995346,
                "lgbm_pred": 0.4784353197226744,
                "sarima_pred": 0.00047202994528104723,
                "ci_low": -2.03946263009706,
                "ci_high": 2.0404066899876225
            },
            {
                "date": "2027-10-01",
                "quarter": "Q4-2027",
                "ensemble_pred": 0.2170286637619828,
                "lgbm_pred": 0.38536137244438917,
                "sarima_pred": 0.00016066607732658956,
                "ci_low": -2.0397749821322906,
                "ci_high": 2.040096314286944
            },
            {
                "date": "2028-01-01",
                "quarter": "Q1-2028",
                "ensemble_pred": 0.26461423519511434,
                "lgbm_pred": 0.46996507507297414,
                "sarima_pred": 5.468633645296425e-05,
                "ci_low": -2.0398810763558033,
                "ci_high": 2.0399904490287093
            }
        ]
    },
    "india": {
        "history": {
            "2019-04-01": -4.631922312934478,
            "2019-07-01": -0.0771129028573014,
            "2019-10-01": 1.496625194634582,
            "2020-01-01": 5.968399354088128,
            "2020-04-01": -34.59498568803294,
            "2020-07-01": 20.264562822309173,
            "2020-10-01": 9.09617762366164,
            "2021-01-01": 7.732034322585868,
            "2021-04-01": -18.795405557924383,
            "2021-07-01": 10.036615315294029,
            "2021-10-01": 6.28187239802056,
            "2022-01-01": 6.487081150685725,
            "2022-04-01": -10.13083494865672,
            "2022-07-01": 11.66328391995819,
            "2022-10-01": -2.990418909636716,
            "2023-01-01": 8.189755231237328,
            "2023-04-01": -7.765649611384084,
            "2023-07-01": 2.80816018409098,
            "2023-10-01": 6.811403614734779,
            "2024-01-01": 6.118608868126252
        },
        "metrics": {
            "ensemble_rmse": 4.2507,
            "ensemble_mae": 2.4191,
            "w_sarima": 0.0,
            "w_lgbm": 1.0
        },
        "forecast": [
            {
                "date": "2024-04-01",
                "quarter": "Q2-2024",
                "ensemble_pred": -0.6118171937340465,
                "lgbm_pred": -0.6118171937340465
            },
            {
                "date": "2024-07-01",
                "quarter": "Q3-2024",
                "ensemble_pred": 3.839819513176146,
                "lgbm_pred": 3.839819513176146
            },
            {
                "date": "2024-10-01",
                "quarter": "Q4-2024",
                "ensemble_pred": 4.8880578589802,
                "lgbm_pred": 4.8880578589802
            },
            {
                "date": "2025-01-01",
                "quarter": "Q1-2025",
                "ensemble_pred": 4.101188212936768,
                "lgbm_pred": 4.101188212936768
            },
            {
                "date": "2025-04-01",
                "quarter": "Q2-2025",
                "ensemble_pred": 0.9772871343202354,
                "lgbm_pred": 0.9772871343202354
            },
            {
                "date": "2025-07-01",
                "quarter": "Q3-2025",
                "ensemble_pred": 3.480078324471487,
                "lgbm_pred": 3.480078324471487
            },
            {
                "date": "2025-10-01",
                "quarter": "Q4-2025",
                "ensemble_pred": 4.893328820500808,
                "lgbm_pred": 4.893328820500808
            },
            {
                "date": "2026-01-01",
                "quarter": "Q1-2026",
                "ensemble_pred": 3.111526647432659,
                "lgbm_pred": 3.111526647432659
            }
        ]
    }
};

// --- GLOBAL VARIABLES ---
let currentCountry = null;
let chartInstance = null;

// --- DOM ELEMENTS ---
const mockToggle = document.getElementById("mock-toggle");
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
mockToggle.addEventListener("change", () => {
    if (currentCountry) expandCard(currentCountry);
});

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
    if (mockToggle && mockToggle.checked) {
        return MOCK_DATA[country];
    }

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
            console.warn("Static JSON fallback failed, using MOCK_DATA.", staticErr);
        }
        return MOCK_DATA[country];
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

            const annRate = nextQtr * 4;
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

    const gradientBlue = ctx.createLinearGradient(0, 0, 0, 400);
    gradientBlue.addColorStop(0, "rgba(27, 54, 93, 0.18)"); // Royal Oxford Navy accent
    gradientBlue.addColorStop(1, "rgba(27, 54, 93, 0.0)");

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: "Historical GDP",
                    data: historyData,
                    borderColor: "#1B365D",
                    backgroundColor: gradientBlue,
                    borderWidth: 2.5,
                    pointBackgroundColor: "#FFFFFF",
                    pointBorderColor: "#1B365D",
                    pointRadius: 4,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: "Forecast",
                    data: forecastData,
                    borderColor: "#C5A059",
                    borderWidth: 2.5,
                    borderDash: [5, 5],
                    pointBackgroundColor: "#C5A059",
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
                    backgroundColor: "rgba(15, 23, 42, 0.95)", // Oxford Slate
                    titleColor: "#FFFFFF",
                    bodyColor: "#C5A059",
                    borderColor: "rgba(197, 160, 89, 0.4)",
                    borderWidth: 1,
                    padding: 12
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(0, 0, 0, 0.05)", drawBorder: false },
                    ticks: { color: "#475569", maxTicksLimit: 12 }
                },
                y: {
                    grid: {
                        color: (context) => context.tick.value === 0 ? "rgba(197, 160, 89, 0.4)" : "rgba(0, 0, 0, 0.05)",
                        lineWidth: (context) => context.tick.value === 0 ? 2 : 1,
                        drawBorder: false
                    },
                    ticks: {
                        color: "#475569",
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

document.addEventListener("DOMContentLoaded", () => {
    initializeCards();
    initParticles();
});
