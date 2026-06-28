# 📔 Daily Development Journal — Global MacroForecast

## 2026-06-28: Option 1 Cloud Deployment & Caching Strategy

### 🎯 Objective
Transitioning the backend to cloud hosting (Render/Railway) while implementing a 24-hour HTTP cache header (`Cache-Control: max-age=86400`) and configuring the frontend for seamless live API fetching with static fallbacks.

### 🏛️ Architectural Decisions
1. **Option 1 Implementation (Backend + Caching):**
   - Retaining the live FastAPI server to showcase full-stack machine learning engineering on the resume.
   - Injecting `Cache-Control: max-age=86400` middleware in FastAPI. This ensures CDN/browser layer caching for 24 hours, giving instant subsequent loads while maintaining a live API.
2. **Unified Dashboard Endpoint (`/api/dashboard/{country}`):**
   - Instead of making 3 separate HTTP requests (`/history`, `/metrics`, `/forecast`), we created a single consolidated endpoint returning `{ "history": ..., "metrics": ..., "forecast": ... }`. This eliminates network latency overhead.
3. **Graceful Degradation on Frontend:**
   - Updated `dashboard.js` to attempt dynamic fetching from the deployed API URL first. If the API is unreachable or waking up from a cloud cold-start, it seamlessly falls back to `data/forecasts.json` (or `MOCK_DATA`), guaranteeing 100% UI uptime for recruiters.
4. **Live API Configuration:**
   - Configured `API_BASE_URL` in `dashboard.js` to point directly to the live Render backend service: `https://global-macroforecast.onrender.com`. Un-ignored `models_saved/` in `.gitignore` so that all 8 serialized ML models are available in production container memory.
