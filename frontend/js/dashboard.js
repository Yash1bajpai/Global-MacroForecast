const USE_MOCK = true; // Set to false when backend is ready

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
        "forecast": [
            {
                "date": "2026-04-01",
                "quarter": "Q2-2026",
                "ensemble_pred": 0.538103196463867,
                "lgbm_pred": 0.7012134296312453,
                "sarima_pred": 0.36765467059775175,
                "ci_low": -0.7040917342389401,
                "ci_high": 1.4394010754344435
            },
            {
                "date": "2026-07-01",
                "quarter": "Q3-2026",
                "ensemble_pred": 0.563452579134878,
                "lgbm_pred": 0.7794328981070869,
                "sarima_pred": 0.33775535419663916,
                "ci_low": -0.8187211668859162,
                "ci_high": 1.4942318752791945
            },
            {
                "date": "2026-10-01",
                "quarter": "Q4-2026",
                "ensemble_pred": 0.5146706807688741,
                "lgbm_pred": 0.7102545057841212,
                "sarima_pred": 0.3102875834625526,
                "ci_low": -0.9131405726830754,
                "ci_high": 1.5337157396081804
            },
            {
                "date": "2027-01-01",
                "quarter": "Q1-2027",
                "ensemble_pred": 0.4808262531842922,
                "lgbm_pred": 0.6681703244790963,
                "sarima_pred": 0.28505361426477294,
                "ci_low": -0.9921513571849788,
                "ci_high": 1.5622585857145248
            },
            {
                "date": "2027-04-01",
                "quarter": "Q2-2027",
                "ensemble_pred": 0.4825461670756521,
                "lgbm_pred": 0.6937198918695099,
                "sarima_pred": 0.26187178390661053,
                "ci_low": -1.0590164080859648,
                "ci_high": 1.5827599758991857
            },
            {
                "date": "2027-07-01",
                "quarter": "Q3-2027",
                "ensemble_pred": 0.4721321391646514,
                "lgbm_pred": 0.6937198918695099,
                "sarima_pred": 0.24057520331151713,
                "ci_low": -1.1160860558867787,
                "ci_high": 1.597236462509813
            },
            {
                "date": "2027-10-01",
                "quarter": "Q4-2027",
                "ensemble_pred": 0.46256502641731445,
                "lgbm_pred": 0.6937198918695099,
                "sarima_pred": 0.2210105555664518,
                "ci_low": -1.1651237179488239,
                "ci_high": 1.6071448290817276
            },
            {
                "date": "2028-01-01",
                "quarter": "Q1-2028",
                "ensemble_pred": 0.4530098209320246,
                "lgbm_pred": 0.6922206100966742,
                "sarima_pred": 0.20303699217305524,
                "ci_low": -1.2074923511717848,
                "ci_high": 1.6135663355178953
            }
        ],
        "metrics": {
            "ensemble_rmse": 2.3009,
            "ensemble_mae": 1.1249,
            "w_sarima": 0.489,
            "w_lgbm": 0.511
        }
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
        "forecast": [
            {
                "date": "2026-04-01",
                "quarter": "Q2-2026",
                "ensemble_pred": 0.4547036283302615,
                "lgbm_pred": 0.7718211921072917,
                "sarima_pred": 0.1272732982515392,
                "ci_low": -1.5776609400760375,
                "ci_high": 1.832207536579116
            },
            {
                "date": "2026-07-01",
                "quarter": "Q3-2026",
                "ensemble_pred": 0.3239746352375193,
                "lgbm_pred": 0.5583620894552614,
                "sarima_pred": 0.08196482478505382,
                "ci_low": -1.7006502098315537,
                "ci_high": 1.8645798594016612
            },
            {
                "date": "2026-10-01",
                "quarter": "Q4-2026",
                "ensemble_pred": 0.3049859745909638,
                "lgbm_pred": 0.5492427632759971,
                "sarima_pred": 0.05278587570479124,
                "ci_low": -1.7610710828107845,
                "ci_high": 1.866642834220367
            },
            {
                "date": "2027-01-01",
                "quarter": "Q1-2027",
                "ensemble_pred": 0.41501978685116153,
                "lgbm_pred": 0.7840443311738423,
                "sarima_pred": 0.0339944443391253,
                "ci_low": -1.7926631667754833,
                "ci_high": 1.860652055453734
            },
            {
                "date": "2027-04-01",
                "quarter": "Q2-2027",
                "ensemble_pred": 0.3023015084928282,
                "lgbm_pred": 0.5738786002783517,
                "sarima_pred": 0.021892641364686036,
                "ci_low": -1.810047726656933,
                "ci_high": 1.8538330093863051
            },
            {
                "date": "2027-07-01",
                "quarter": "Q3-2027",
                "ensemble_pred": 0.2776063906343577,
                "lgbm_pred": 0.5328143337523671,
                "sarima_pred": 0.0140990022116977,
                "ci_low": -1.8200278952007187,
                "ci_high": 1.8482258996241143
            },
            {
                "date": "2027-10-01",
                "quarter": "Q4-2027",
                "ensemble_pred": 0.33200486647688754,
                "lgbm_pred": 0.6447590179002671,
                "sarima_pred": 0.009079848340552551,
                "ci_low": -1.8259531353308067,
                "ci_high": 1.8441128320119118
            },
            {
                "date": "2028-01-01",
                "quarter": "Q1-2028",
                "ensemble_pred": 0.3326961029524356,
                "lgbm_pred": 0.6492502802333022,
                "sarima_pred": 0.005847480881947294,
                "ci_low": -1.8295611656752193,
                "ci_high": 1.841256127439114
            }
        ],
        "metrics": {
            "ensemble_rmse": 2.5408,
            "ensemble_mae": 1.0975,
            "w_sarima": 0.492,
            "w_lgbm": 0.508
        }
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
        "forecast": [
            {
                "date": "2026-04-01",
                "quarter": "Q2-2026",
                "ensemble_pred": 0.12625646625980125,
                "lgbm_pred": 0.14626970194733738,
                "sarima_pred": 0.10332284424876198,
                "ci_low": -1.8823409567839051,
                "ci_high": 2.088986645281429
            },
            {
                "date": "2026-07-01",
                "quarter": "Q3-2026",
                "ensemble_pred": 0.056155288580481744,
                "lgbm_pred": 0.07446980380974462,
                "sarima_pred": 0.03516826898300025,
                "ci_low": -1.9985540858187762,
                "ci_high": 2.068890623784777
            },
            {
                "date": "2026-10-01",
                "quarter": "Q4-2026",
                "ensemble_pred": 0.0948979326902945,
                "lgbm_pred": 0.16726547793948193,
                "sarima_pred": 0.011970316460538949,
                "ci_low": -2.0272465838649696,
                "ci_high": 2.0511872167860474
            },
            {
                "date": "2027-01-01",
                "quarter": "Q1-2027",
                "ensemble_pred": 0.06446205917901185,
                "lgbm_pred": 0.11715993184668974,
                "sarima_pred": 0.0040743681821449025,
                "ci_low": -2.035778138004203,
                "ci_high": 2.0439268743684926
            },
            {
                "date": "2027-04-01",
                "quarter": "Q2-2027",
                "ensemble_pred": 0.07875427124440959,
                "lgbm_pred": 0.14626970194733738,
                "sarima_pred": 0.0013868034432004768,
                "ci_low": -2.03853932712608,
                "ci_high": 2.041312934012481
            },
            {
                "date": "2027-07-01",
                "quarter": "Q3-2027",
                "ensemble_pred": 0.03546481863848938,
                "lgbm_pred": 0.06600159678649516,
                "sarima_pred": 0.00047202994528104723,
                "ci_low": -2.03946263009706,
                "ci_high": 2.0404066899876225
            },
            {
                "date": "2027-10-01",
                "quarter": "Q4-2027",
                "ensemble_pred": 0.10292645240509161,
                "lgbm_pred": 0.19260595882595022,
                "sarima_pred": 0.00016066607732658956,
                "ci_low": -2.0397749821322906,
                "ci_high": 2.040096314286944
            },
            {
                "date": "2028-01-01",
                "quarter": "Q1-2028",
                "ensemble_pred": 0.06258888743891941,
                "lgbm_pred": 0.11715993184668974,
                "sarima_pred": 5.468633645296425e-05,
                "ci_low": -2.0398810763558033,
                "ci_high": 2.0399904490287093
            }
        ],
        "metrics": {
            "ensemble_rmse": 1.732,
            "ensemble_mae": 0.9568,
            "w_sarima": 0.466,
            "w_lgbm": 0.534
        }
    },
    "india": {
        "history": {
            "2020-01-01": -5.77772470686801,
            "2020-04-01": -5.77772470686801,
            "2020-07-01": -5.77772470686801,
            "2020-10-01": -5.77772470686801,
            "2021-01-01": 9.68959249192875,
            "2021-04-01": 9.68959249192875,
            "2021-07-01": 9.68959249192875,
            "2021-10-01": 9.68959249192875,
            "2022-01-01": 7.60936497768895,
            "2022-04-01": 7.60936497768895,
            "2022-07-01": 7.60936497768895,
            "2022-10-01": 7.60936497768895,
            "2023-01-01": 9.19075493028345,
            "2023-04-01": 9.19075493028345,
            "2023-07-01": 9.19075493028345,
            "2023-10-01": 9.19075493028345,
            "2024-01-01": 6.49476552383821,
            "2024-04-01": 6.49476552383821,
            "2024-07-01": 6.49476552383821,
            "2024-10-01": 6.49476552383821
        },
        "forecast": [
            {
                "date": "2025-01-01",
                "quarter": "Q1-2025",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            },
            {
                "date": "2025-04-01",
                "quarter": "Q2-2025",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            },
            {
                "date": "2025-07-01",
                "quarter": "Q3-2025",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            },
            {
                "date": "2025-10-01",
                "quarter": "Q4-2025",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            },
            {
                "date": "2026-01-01",
                "quarter": "Q1-2026",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            },
            {
                "date": "2026-04-01",
                "quarter": "Q2-2026",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            },
            {
                "date": "2026-07-01",
                "quarter": "Q3-2026",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            },
            {
                "date": "2026-10-01",
                "quarter": "Q4-2026",
                "ensemble_pred": 6.293112626204884,
                "lgbm_pred": 6.293112626204884
            }
        ],
        "metrics": {
            "ensemble_rmse": 4.6015,
            "ensemble_mae": 2.7392,
            "w_sarima": 0.0,
            "w_lgbm": 1.0
        }
    }
};

// --- GLOBAL VARIABLES ---
let currentCountry = null; // No country selected by default
let chartInstance = null;
const API_BASE = "http://127.0.0.1:8000/api";


// --- DOM ELEMENTS ---
const mockToggle = document.getElementById("mock-toggle");
const cards = document.querySelectorAll(".country-card");
const chartWrapper = document.getElementById("chart-wrapper");
const chartTitle = document.getElementById("chart-title");

// --- EVENT LISTENERS ---
mockToggle.addEventListener("change", () => {
    if(currentCountry) expandCard(currentCountry);
});

cards.forEach(card => {
    card.addEventListener("click", (e) => {
        const country = e.currentTarget.dataset.country;
        
        if(currentCountry === country) {
            collapseAll();
            return;
        }
        
        currentCountry = country;
        cards.forEach(c => c.classList.remove("active"));
        e.currentTarget.classList.add("active");
        
        chartTitle.textContent = COUNTRY_TITLES[country] + " - 8-Quarter Forecast";
        
        // Move the chart wrapper immediately AFTER the clicked card in the DOM (mobile responsive trick)
        // or just keep it below the grid. Since our CSS puts it below the grid, we just unhide it.
        
        expandCard(country);
    });
});

function collapseAll() {
    currentCountry = null;
    cards.forEach(c => c.classList.remove("active"));
    chartWrapper.classList.remove("visible");
    chartWrapper.classList.add("hidden");
}

// --- FETCH DATA ---
async function fetchData(country) {
    const isMock = mockToggle.checked;
    if (isMock) {
        return MOCK_DATA[country];
    }

    try {
        const [histRes, fcRes, metRes] = await Promise.all([
            fetch(API_BASE + "/history/" + country),
            fetch(API_BASE + "/forecast/" + country),
            fetch(API_BASE + "/metrics/" + country)
        ]);

        if (!histRes.ok || !fcRes.ok || !metRes.ok) throw new Error("API Error");

        const history = await histRes.json();
        const forecast = await fcRes.json();
        const metrics = await metRes.json();
        return { history, forecast, metrics };
    } catch (error) {
        console.error("API failed, falling back to mock.");
        mockToggle.checked = true;
        return MOCK_DATA[country];
    }
}

// --- INITIAL LOAD ---
async function initializeCards() {
    for (const c of ['us', 'germany', 'japan', 'india']) {
        const data = await fetchData(c);
        
        const nextQtr = data.forecast[0].ensemble_pred;
        const valEl = document.getElementById("val-" + c);
        const trendEl = document.getElementById("trend-" + c);
        const rmseEl = document.getElementById("rmse-" + c);
        
        valEl.textContent = (nextQtr > 0 ? '+' : '') + nextQtr.toFixed(2) + "%";
        
        const annRate = nextQtr * 4;
        if (nextQtr > 0.2) {
            trendEl.innerHTML = "Annualized ~" + annRate.toFixed(1) + "% <span class='trend-up'>▲ Expansion</span>";
        } else if (nextQtr < 0) {
            trendEl.innerHTML = "Annualized ~" + annRate.toFixed(1) + "% <span class='trend-down'>▼ Contraction</span>";
        } else {
            trendEl.innerHTML = "Annualized ~" + annRate.toFixed(1) + "% <span class='trend-flat'>▶ Stagnation</span>";
        }
        
        rmseEl.textContent = data.metrics.ensemble_rmse.toFixed(2) + "%";
    }
}

// --- EXPAND CARD LOGIC ---
async function expandCard(country) {
    chartWrapper.classList.remove("hidden");
    chartWrapper.classList.add("visible");
    
    const data = await fetchData(country);
    drawChart(data);
}

// --- CHART.JS ---
function drawChart(data) {
    const ctx = document.getElementById('gdpChart').getContext('2d');

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

    let gradientBlue = ctx.createLinearGradient(0, 0, 0, 400);
    gradientBlue.addColorStop(0, 'rgba(59, 130, 246, 0.4)');   
    gradientBlue.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: 'Historical GDP',
                    data: historyData,
                    borderColor: '#3b82f6',
                    backgroundColor: gradientBlue,
                    borderWidth: 2,
                    pointBackgroundColor: '#070B14',
                    pointBorderColor: '#3b82f6',
                    pointRadius: 4,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Forecast',
                    data: forecastData,
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointBackgroundColor: '#f59e0b',
                    pointRadius: 4,
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
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(18, 24, 38, 0.9)',
                    titleColor: '#94a3b8',
                    bodyColor: '#f8fafc',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { color: '#94a3b8', maxTicksLimit: 12 }
                },
                y: {
                    grid: { 
                        color: (context) => context.tick.value === 0 ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.05)', 
                        lineWidth: (context) => context.tick.value === 0 ? 2 : 1,
                        drawBorder: false 
                    },
                    ticks: { 
                        color: '#94a3b8',
                        callback: function(value) { return value + '%'; }
                    }
                }
            },
            interaction: { mode: 'nearest', axis: 'x', intersect: false }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initializeCards();
});
