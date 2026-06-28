# 🚀 Step-by-Step Deployment Guide — Global MacroForecast

Is guide ko follow karke aap apne project ko **Render (Backend API)** aur **Vercel (Frontend CDN)** pe live kar sakte ho. Ye pura process 100% free aur beginner-friendly hai!

---

## 📋 Step 1: GitHub Pe Code Push Karo

Sabse pehle hamne jo bhi changes kiye hain (caching header, Procfile, hybrid fetch), unhe apne GitHub repository me upload karo:

VS Code terminal me ye commands chalo:
```bash
cd c:\Yash\GDP_Project
git add .
git commit -m "feat: v1.4.0 Option 1 cloud deployment & 24hr caching setup"
git push origin main
```

---

## ☁️ Step 2: Render Pe Backend Deploy Karo (Free API Hosting)

1. **[Render.com](https://render.com)** pe jao aur apne GitHub account se Login / Sign Up karo.
2. Dashboard pe **"New +"** button pe click karo aur **"Web Service"** select karo.
3. Apna GitHub repository (**Global-MacroForecast**) connect karo.
4. Render automatically settings detect kar lega (`render.yaml` aur `Procfile` se), but agar manual verify karna ho toh ye check karo:
   - **Name:** `global-macroforecast-api` (ya kuch bhi cool naam)
   - **Region:** Singapore ya US (jo pass ho)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
5. **Environment Variables (Advanced section me):**
   - Key: `PYTHON_VERSION` | Value: `3.11.0`
   - Key: `ALLOWED_ORIGINS` | Value: `*`
6. Neeche **"Create Web Service"** pe click kar do! 
7. ⏳ *Note: Pehli baar deploy hone me 3 se 5 minute lagenge. Jab deployment green ho jaye, toh apna Live API URL copy kar lo* (Jaise: `https://global-macroforecast-api.onrender.com`).

---

## 🔗 Step 3: Frontend me Apna Live API URL Daalo

Ab hume frontend ko batana hai ki aapka asli cloud backend kahan chal raha hai:

1. VS Code me `frontend/js/dashboard.js` open karo.
2. **Line 3** pe dhyan do:
   ```javascript
   const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
       ? "http://127.0.0.1:8000" 
       : "https://global-macroforecast-api.onrender.com"; // <-- Yahan apna copied Render URL paste kar do!
   ```
3. Ek baar terminal me ye script chala do taaki latest `forecasts.json` generate ho jaye:
   ```bash
   python src/scripts/export_forecasts.py
   ```
4. Dobara GitHub pe push kar do:
   ```bash
   git commit -am "chore: update render live api url"
   git push origin main
   ```

---

## ⚡ Step 4: Vercel Pe Frontend Deploy Karo (Free CDN)

1. **[Vercel.com](https://vercel.com)** pe jao aur GitHub se login karo.
2. **"Add New..."** -> **"Project"** pe click karo.
3. Apna GitHub repository (**Global-MacroForecast**) Import karo.
4. **Configure Project** screen pe sabse important step:
   - **Root Directory:** Edit pe click karo aur list me se **`frontend`** folder select karke Continue karo.
   - **Framework Preset:** `Other` (ya `Static HTML`) rehne do.
5. **"Deploy"** button pe click kar do!
6. 🎉 Sirf 15 second me aapka stunning Glassmorphism dashboard live ho jayega!

---

## 🏆 Step 5: Resume & Interview Impact Verify Karo

Aapka Vercel link ab recruiters ko bhejne ke liye ready hai!
- **Instant Speed:** Vercel se website kholte hi sub-50ms me load hogi (Kyunki hybrid caching aur `forecasts.json` fallback laga hai).
- **Live API Power:** Background me website aapke Render cloud server se connect hokar latest 24hr cached predictions verify karegi.

### Resume Bullet Point:
> *"Architected a fault-tolerant hybrid macroeconomic nowcasting platform combining Vercel edge static caching with an asynchronous FastAPI backend deployed on Render, implementing `Cache-Control` middleware and graceful degradation during cloud cold-starts."*
