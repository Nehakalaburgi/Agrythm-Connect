# Agrythm Connect — Voice Agent Telemetry & Operations Dashboard

> **Real-Time Voice Intelligence, Grounded Weather Advisories, and Farmer Telemetry for Gate Zero Voice Agents**  
> Built with **React 18+**, **Vite**, **Tailwind CSS**, and **SQLite REST Telemetry**.

---

## 🌾 Overview

**Agrythm Connect Dashboard** is a real-time agricultural voice telemetry and monitoring system designed for the Gate Zero voice agent. It provides end-to-end visibility into automated weather advisory phone calls dispatched to farmers across regional agricultural zones in **Hindi** and **English**.

The dashboard bridges live telephony execution records stored in the Gate Zero SQLite database (`gate0.db`) with an interactive, field-first operator interface.

---

## ⚡ Key Architectural Features

### 1. Live SQLite Telemetry Integration (Gate Zero Bridge)
- **Local SQLite Telemetry Engine (`gate0.db`)**: Connects directly to the Gate Zero telephony backend via a lightweight local REST API server (`weathercall/server.py` on port `8000`).
- **Real-Time Dual Endpoints**:
  - `GET /api/calls`: Streams live attempt logs joined with execution outcomes (`attempts` + `day_results` tables), capturing call status (`answered`, `unanswered`, `busy`, `failed`, `skipped`), attempt numbers, duration, and spoken message text.
  - `GET /api/farmers`: Streams registered farmer profiles directly from the database with automated Google Sheets fallback if the server is offline.
- **Continuous Polling**: Auto-polls every 15 seconds to stream live call updates as the backend voice agent dials farmers.

### 2. Spoken Advisory Meteorological Grounding
- **Natural Language Weather Parser (`extractWeatherFromMessage`)**:
  - Dynamically extracts structured meteorological data directly from the generated spoken text in both **Hindi** (*"आज मौसम Partly cloudy रहेगा। तापमान 21 से 32 डिग्री सेल्सियस के बीच रहेगा..."*) and **English** (*"It will be Partly cloudy. The temperature will be between 21 and 32 degrees Celsius..."*).
  - Grounds and displays key parameters:
    - **Atmospheric Condition**: e.g., `Partly Cloudy`, `Clear`, `Light Rain`, `Overcast`.
    - **Temperature Range**: e.g., `21°C – 32°C`.
    - **Precipitation Chance**: e.g., `20%`, `70%`.
    - **Derived Humidity & Wind Speed**: Realistic meteorological estimates correlated with rain probability and atmospheric condition (e.g., `57%` humidity, `10 km/h` wind speed).
  - **Skipped Call Handling**: Gracefully handles skipped runs (`weather_unavailable`, `no_consent`, `inactive`), displaying clear explanatory badges instead of missing data.

### 3. Farmer Privacy & Phone Masking
- **Strict UI Masking**: Farmer phone numbers are automatically masked across all dashboard views (`+91 98XXX XX001`) to protect user privacy in field displays.
- **Database Contact Integrity**: The underlying SQLite database and internal data models retain the exact, unmasked phone numbers (`+91 98450 12001`) required for automated telephony and SMS dispatch.
- **Smart Search**: Filter bar allows operators to search by either the visible masked format or raw phone digits.

### 4. Bilingual Support (Hindi & English)
- The voice agent and dashboard strictly support **Hindi** and **English**, standardizing language tags and badge formatting across all tables and cards.

---

## 🖥 Dashboard Views & Components

1. **Live Call History Table (`CallHistoryTable.jsx`)**:
   - Shows Call ID, timestamp, attempt number, farmer contact (masked), district, village, language badge, duration, and delivery status badge (`Delivered`, `Unanswered / Busy`, `Failed`, `Skipped`).
   - Displays real-time weather summary and spoken message preview.
   - Clicking any call opens the comprehensive Call Detail Drawer.

2. **Call Detail Drawer (`CallDetailDrawer.jsx`)**:
   - Slide-over panel featuring:
     - Farmer profile summary with masked contact.
     - Simulated post-call audio player with playback scrubber.
     - **Weather Advisory Grounding Box**: Live telemetry badges (`Live Grounded (Open-Meteo)`), Temperature, Rain Chance, Humidity, Wind Speed, and the complete spoken message text.
     - Original dialog transcript in native language.

3. **Farmer Directory (`FarmerDirectory.jsx`)**:
   - Displays farmer cards loaded live from the backend database (`/api/farmers`).
   - Shows total calls recorded per farmer, today's engagement indicator, village, district, language preference, and masked phone numbers.
   - One-click **"View Call Logs"** filters the call history directly to that farmer's records.

4. **District Weather Advisories (`WeatherAlertsView.jsx`)**:
   - Aggregates call records by agricultural district.
   - Displays district alert cards with latest forecast, temperature ranges, precipitation probabilities, and recorded spoken advisories.

5. **Operational KPI Metrics (`KpiMetrics.jsx`)**:
   - Real-time summary cards: **Total Calls**, **Delivered Calls**, **Unanswered / Busy**, and **Skipped / Failed**.

6. **Top Filter & Search Bar (`TopFilterBar.jsx`)**:
   - Text search across Farmer Name, Phone Number, Village, and Call ID.
   - Quick date presets: **"Today"**, **"Yesterday"**, and **"All Dates"** with native date picker sync.
   - Multi-dropdown filters for District, Language (Hindi, English), and Call Status.

---

## 🗂 Project Directory Structure

```text
gate0/dashboard/
├── public/
│   ├── favicon.svg                   # Agrythm leaf favicon
│   └── icons.svg                     # Vector icon symbols
├── src/
│   ├── components/
│   │   ├── CallDetailDrawer.jsx      # Slide-over call inspection drawer & weather grounding
│   │   ├── CallHistoryTable.jsx      # Real-time voice agent telemetry table
│   │   ├── FarmerDirectory.jsx       # Registered farmer profiles loaded from SQLite API
│   │   ├── Header.jsx                # Sticky navigation header with live sync status
│   │   ├── KpiMetrics.jsx            # KPI cards (Total, Delivered, Unanswered, Skipped)
│   │   ├── OverviewCard.jsx          # Metric presentation card wrapper
│   │   ├── Sidebar.jsx               # Left sidebar navigation
│   │   ├── TopFilterBar.jsx          # Live search, date presets, and dropdown filters
│   │   ├── WeatherAlertsView.jsx     # District-level weather advisory intelligence
│   │   └── index.js                  # Component barrel export
│   ├── hooks/
│   │   ├── useVoiceAgentData.js      # Polling hook, filtering engine & data enrichment
│   │   └── index.js                  # Hooks barrel export
│   ├── utils/
│   │   ├── callAnalytics.js          # Metric aggregation and duration formatters
│   │   ├── constants.js              # API endpoints, sheet IDs, and status definitions
│   │   ├── csvParser.js              # Streaming CSV parser wrapper
│   │   ├── googleSheets.js           # SQLite telemetry fetcher with Sheets fallback
│   │   └── index.js                  # Weather parser, phone masking & language normalizer
│   ├── App.css                       # Application utility styles
│   ├── App.jsx                       # Main application shell and tab router
│   ├── index.css                     # Tailwind CSS directives
│   └── main.jsx                      # React 18+ application entrypoint
├── index.html                        # HTML root with viewport settings
├── package.json                      # Project dependencies and npm scripts
├── postcss.config.js                 # PostCSS Tailwind plugins
├── tailwind.config.js                # Custom color palette tokens
└── vite.config.js                    # Vite bundler configuration
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18 or higher
- **Python**: v3.10+ (for Gate Zero telemetry server)
- **SQLite3**: Included with Python standard library

### 2. Start the Gate Zero Telemetry API Server
From your backend repository root (`gate0/`):
```bash
# Start the SQLite telemetry server on port 8000
python -m weathercall.server
```
The server will start and log:
```text
Gate Zero SQLite Telemetry API running on http://0.0.0.0:8000
  - Calls endpoint:   http://localhost:8000/api/calls
  - Farmers endpoint: http://localhost:8000/api/farmers
```

### 3. Start the Dashboard Frontend
From the `gate0/dashboard/` directory:
```bash
# Install dependencies
npm install

# Start local development server
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 🔍 Code Quality & Build

### Static Linting
Verify zero linting warnings across all source files:
```bash
npm run lint
```
*Uses [Oxlint](https://oxc.rs/) — passes with 0 warnings and 0 errors.*

### Production Build
Generate optimized production bundles:
```bash
npm run build
```
Builds to `dist/` ready for hosting on Vercel, Netlify, or Firebase App Hosting.

---

## 📡 API Reference

### `GET /api/calls`
Returns call execution attempts joined with daily outcomes.

**Response Schema:**
```json
[
  {
    "call_id": "F001-2026-10-30-1",
    "farmer_id": "F001",
    "call_date": "2026-10-30",
    "attempt_no": 1,
    "attempt_status": "answered",
    "call_status": "answered",
    "skip_reason": null,
    "language": "hi",
    "duration_sec": 42,
    "message_text": "नमस्ते Ramesh... आज मौसम Partly cloudy रहेगा। तापमान 21 से 32 डिग्री सेल्सियस के बीच रहेगा। बारिश की संभावना 20 प्रतिशत है...",
    "weather_source": "open-meteo"
  }
]
```

### `GET /api/farmers`
Returns registered farmer profiles from the SQLite `farmers` table.

**Response Schema:**
```json
[
  {
    "farmer_id": "F001",
    "farmer_name": "Ramesh",
    "phone_number": "+91 98450 12001",
    "village": "Mandya",
    "district": "Mandya",
    "state": "Karnataka",
    "primary_language": "Hindi",
    "call_consent": "Yes",
    "active": "Yes"
  }
]
```

---

## 📄 License
Internal proprietary software for **Agrythm Connect — Voice Intelligence System**. All rights reserved.
