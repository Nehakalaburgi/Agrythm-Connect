# Agrythm Connect — Trust AI Monitoring Dashboard (Screen C01)

> **Field-First Post-Call Handling System for Multilingual Weather Report Voice Agents**  
> Built with **React 18+**, **Vite**, **Tailwind CSS**, and **PapaParse**.

---

## 🌾 Overview

**Agrythm Connect** is an agricultural voice intelligence and monitoring dashboard engineered under the **Trust AI Light System (Field-First Architecture)**. It provides real-time visibility and post-call operations for an automated weather report voice agent communicating with farmers across regional agricultural zones in their native languages (Kannada, Hindi).

### Key Architectural Highlights
- **100% Live Cloud Ingestion (Zero Mock / Dummy Data)**: The dashboard strictly renders live records fetched directly from linked Google Sheets via CSV export. When the sheet is empty or contains only headers, the system cleanly shows `0` metrics and a helpful prompt to populate rows.
- **Dual-Sheet Relational Linking**:
  - **Sheet 1 (Master Farmer Directory)**: Profiles, phone numbers, preferred languages, districts, and villages.
  - **Sheet 2 (Call Execution Logs)**: Call timestamps, duration, delivered weather advisories, rainfall chances, AI confidence scores, transcripts, and operator resolution notes.
- **Top Filter & Dynamic Calendar Synchronizer**:
  - Automated date calculation: Clicking **"Today"** or **"Yesterday"** automatically computes and fills the exact calendar date (`YYYY-MM-DD`).
  - Reset action: Clicking **"All Dates"** clears the date filter back to showing all records.
  - Granular multi-filter: District, Language, and Call Status dropdowns.
- **Dynamic Weather Advisories Counter**:
  - The left sidebar navigation badge dynamically computes and shows the number of active alerts (`rainfall_chance >= 50%` or high-risk advisory warnings) currently present in the call logs.
  - Dynamically updates to `0 Alerts` or an amber warning pill based strictly on live data.
- **Right Slide-Over Inspection Drawer**:
  - Voice audio synthesis player simulation with progress scrubbing.
  - Meteorological grounding telemetry (rainfall chance, temperature, wind speed, moisture).
  - Multilingual dialog transcript review.
  - Post-call operator action suite: Change status (Resolved, Escalated, Pending) and append operator notes.
- **Bidirectional Cloud Writeback**: Integrated webhook and Google Apps Script support for persisting operator status changes and follow-up notes directly back to the cloud spreadsheet.

---

## 🎨 Design System & Tokens (Trust AI Light)

Adheres strictly to the **Trust AI Light System (Field-First Architecture)**:

| Token | Hex / Class | Purpose |
| :--- | :--- | :--- |
| **`trust-navy`** | `#0F2444` | Primary brand accent, active tabs, major action buttons |
| **`trust-green`** | `#1E6F43` | Agriculture baseline actions, verified trust badges, live telemetry pulses |
| **`trust-canvas`** | `#F8FAFC` (`bg-slate-50`) | Soft canvas slate background |
| **`trust-card`** | `#FFFFFF` | Crisp white card background |
| **Text Primary** | `#0F172A` (`text-slate-900`) | Headings and primary text |
| **Text Secondary** | `#64748B` (`text-slate-500`) | Micro-labels and descriptions |
| **Card Borders** | `border border-slate-200/80` | Subtle, clean light borders without heavy drop shadows |
| **Typography** | `text-[11px] font-bold tracking-wider text-slate-500 uppercase` | Sub-headers and section markers |

---

## 📊 Google Sheets Data Schema & Setup

The dashboard connects to two Google Sheets via public CSV export:

### 1. Sheet 1: Master Farmer Directory
- **Link**: [Agrythm Connect — Gate Zero Master](https://docs.google.com/spreadsheets/d/1WwdKz4dyAL2tgMaMqStDvm95TQmaYKJtKCMPXYKWFcg/edit?usp=sharing)
- **Sheet ID**: `1WwdKz4dyAL2tgMaMqStDvm95TQmaYKJtKCMPXYKWFcg`
- **Headers (Row 1)**:
  ```csv
  farmer_id,farmer_name,phone_number,primary_language,district,village
  ```
- **Sample Row (Copy & Paste to Row 2 to test)**:
  ```csv
  F-1001,Basavaraj Patil,+91 98451 22340,Kannada,Dharwad,Navalgund
  ```

---

### 2. Sheet 2: Call Execution Logs
- **Link**: [Weather Voice Agent Call Logs](https://docs.google.com/spreadsheets/d/14SwDi8WGten2dzqXDT-w29gbDLBpyDwjHQ8P-DnNds0/edit?usp=sharing)
- **Sheet ID**: `14SwDi8WGten2dzqXDT-w29gbDLBpyDwjHQ8P-DnNds0`
- **Headers (Row 1)**:
  ```csv
  call_id,farmer_id,call_timestamp,duration_sec,weather_forecast,rainfall_chance,advisory_summary,ai_confidence_score,call_status,transcript_preview,operator_notes
  ```
- **Sample Row (Copy & Paste to Row 2 to test)**:
  ```csv
  CALL-8901,F-1001,2026-10-25 09:30:00,142,Scattered Showers,75%,Heavy thunderstorm predicted by 3 PM. Postpone urea spraying.,0.96,Completed,Bot: Namaskara Basavaraj avare. Dharwad zillege e dina male baruvudu... Farmer: Howdu, kothambari bittane madabahuda? Bot: E dina bittane madabedi.,Verified and grounded by field operator
  ```

> [!IMPORTANT]
> Both Google Sheets must have their sharing permissions set to **"Anyone with the link can view"** so the dashboard can fetch the live CSV export stream.

---

## ⚡ Google Apps Script for Bidirectional Writeback (Optional)

To enable the **"Save & Sync to Sheet"** button in the dashboard to write updates back into your Google Sheet:

1. Open your **Call Execution Logs** Google Sheet.
2. Navigate to **Extensions** > **Apps Script**.
3. Paste the following script and save:
   ```javascript
   function doPost(e) {
     try {
       var data = JSON.parse(e.postData.contents);
       var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
       
       if (data.action === "updateCall") {
         var rows = sheet.getDataRange().getValues();
         var callId = data.call_id;
         var foundRow = -1;
         
         for (var i = 1; i < rows.length; i++) {
           if (rows[i][0] == callId) {
             foundRow = i + 1;
             break;
           }
         }
         
         if (foundRow !== -1) {
           sheet.getRange(foundRow, 9).setValue(data.call_status);
           sheet.getRange(foundRow, 11).setValue(data.operator_notes);
         } else {
           sheet.appendRow([
             data.call_id,
             data.farmer_id,
             data.call_timestamp,
             data.duration_sec,
             data.weather_forecast,
             data.rainfall_chance,
             data.advisory_summary,
             data.ai_confidence_score,
             data.call_status,
             data.transcript_preview,
             data.operator_notes
           ]);
         }
       }
       return ContentService.createTextOutput(JSON.stringify({ status: "success" }))
         .setMimeType(ContentService.MimeType.JSON);
     } catch (error) {
       return ContentService.createTextOutput(JSON.stringify({ status: "error", message: error.toString() }))
         .setMimeType(ContentService.MimeType.JSON);
     }
   }
   ```
4. Click **Deploy** > **New deployment** > **Web app**:
   - **Execute as**: *Me*
   - **Who has access**: *Anyone*
5. Copy the deployed Web App URL and paste it into the **Cloud Sync & Setup** tab in the dashboard.

---

## 🗂 Project Directory Structure

```text
AgrythmConnect Dashboard/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── CallDetailDrawer.jsx      # Right slide-over inspection drawer (post-call actions)
│   │   ├── CallHistoryTable.jsx      # Main live voice agent telemetry table
│   │   ├── CloudSyncSettings.jsx     # Google Sheets connection status & Apps Script setup
│   │   ├── FarmerDirectory.jsx       # Master farmer profile directory (Sheet 1)
│   │   ├── Header.jsx                # Field-first sticky header with live indicators
│   │   ├── KpiMetrics.jsx            # Trust AI KPI summary cards (Calculated from Sheet 2)
│   │   ├── OverviewCard.jsx          # Reusable card adhering to Trust AI tokens
│   │   ├── Sidebar.jsx               # Left sidebar navigation with dynamic alert counters
│   │   ├── TopFilterBar.jsx          # Calendar selector, quick presets & multi-filters
│   │   ├── TrustAiAnalyticsView.jsx  # Model grounding and dialect distribution analytics
│   │   ├── WeatherAlertsView.jsx     # District weather warnings compiled from call records
│   │   └── index.js                  # Component barrel export
│   ├── hooks/
│   │   ├── useVoiceAgentData.js      # Reactive state, live polling & filter computations
│   │   └── index.js                  # Hooks barrel export
│   ├── utils/
│   │   ├── constants.js              # Theme tokens, sheet IDs, and configuration
│   │   ├── csvParser.js              # PapaParse promise wrapper
│   │   ├── googleSheets.js           # Fetch service and Apps Script sync helper
│   │   └── index.js                  # Utils barrel export
│   ├── App.css                       # Minimal app-level utility styles
│   ├── App.jsx                       # Main application layout and tab router
│   ├── index.css                     # Tailwind directives and base typography
│   └── main.jsx                      # React 18+ application root
├── index.html                        # HTML entry with Inter font & viewport metadata
├── package.json                      # Project dependencies and scripts
├── postcss.config.js                 # PostCSS configuration with Tailwind & Autoprefixer
├── tailwind.config.js                # Custom Trust AI color token extensions
└── README.md                         # Comprehensive documentation
```

---

## 🚀 Running & Operating the Dashboard

### 1. Prerequisites
- [Node.js](https://nodejs.org/) (v18 or higher recommended)
- `npm` (comes with Node.js)

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Local Development Server
```bash
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

### 4. Stopping the Server
To stop the development server when running in your terminal:
- Press `Ctrl + C` (or `Cmd + C` on macOS) in the terminal.
- Press `Y` if prompted to terminate the batch job.

### 5. Static Lint & Code Quality Verification
```bash
npm run lint
```
Runs Oxlint across the entire repository. Configured to pass with **0 warnings and 0 errors**.

### 6. Build for Production
```bash
npm run build
```
Creates an optimized, minified production build in the `dist/` directory ready for deployment on Vercel, Netlify, or Firebase App Hosting.

---

## 🛠 Tech Stack

- **Framework**: [React 18+](https://react.dev/) with [Vite](https://vite.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) with extended Trust AI color palette
- **Data Ingestion**: [PapaParse](https://www.papaparse.com/) for streaming CSV parsing
- **Icons**: [Lucide React](https://lucide.dev/) for clean, lightweight SVG icons
- **Quality & Linting**: [Oxlint](https://oxc.rs/) for high-speed static code verification

---

## ❓ Troubleshooting & FAQs

### Why does the dashboard show "0 Records"?
The dashboard contains **zero dummy data**. It will display `0` until you add rows to your Google Sheets:
1. Open the [Call Logs Sheet](https://docs.google.com/spreadsheets/d/14SwDi8WGten2dzqXDT-w29gbDLBpyDwjHQ8P-DnNds0/edit?usp=sharing).
2. Insert a row of call data under Row 1.
3. The dashboard will auto-poll every 15 seconds (or click **"Sync Now"** in the header) and immediately display your data.

### How does the Date Filter work?
- Clicking **"Today"** sets the filter to today's date (`YYYY-MM-DD`).
- Clicking **"Yesterday"** sets the filter to yesterday's date.
- Clicking **"All Dates"** clears the date input to view every call in history.

### How does the Weather Alert badge count work?
The badge in the left sidebar counts how many calls in the logs have high-risk advisories (e.g. `rainfall_chance >= 50%` or thunderstorm/rain warnings). If there are 0 active warnings, it will display `0 Alerts`.

---

## 📄 License
Internal proprietary software for **Agrythm Connect — Trust AI Monitoring System**. All rights reserved.
