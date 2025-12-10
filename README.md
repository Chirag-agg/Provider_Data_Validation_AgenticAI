# Provider Data Validation System

> **AI-Powered Healthcare Provider Validation**  
> Automatically validates provider credentials across multiple data sources using CrewAI agents to detect discrepancies, calculate confidence scores, and flag issues requiring manual review.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Mock Data & Test Scenarios](#mock-data--test-scenarios)
- [Usage Examples](#usage-examples)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Provider Data Validation System is an **AI-powered solution** that automates the verification of healthcare provider information by cross-referencing data from multiple sources including NPI registries, license databases, hospital rosters, and online directories.

### What It Does

- **Multi-Source Validation**: Checks provider data against 6 different sources
- **AI-Powered Analysis**: Uses CrewAI agents to intelligently compare and reconcile data
- **Confidence Scoring**: Calculates detailed confidence scores (0-100%) for each validation dimension
- **Issue Detection**: Automatically flags discrepancies, license problems, and missing data
- **Risk Assessment**: Prioritizes providers requiring manual review (LOW, MEDIUM, HIGH, CRITICAL)
- **Unstructured Data**: Processes PDFs, Excel files, and other document formats

---

## ✨ Features

### Validation Capabilities
- ✅ **Identity Verification** - Match provider names across sources with fuzzy matching
- ✅ **License Validation** - Check license status (Active/Suspended/Revoked) and expiration
- ✅ **Contact Verification** - Validate phone numbers and addresses
- ✅ **Specialty Confirmation** - Verify medical specialties across sources
- ✅ **Hospital Affiliation** - Confirm current hospital affiliations
- ✅ **Data Freshness** - Calculate how recent the data is

### Advanced Features
- 🔍 **Discrepancy Detection** - Highlights mismatches between sources
- 🚨 **Risk Flags** - Automatic flagging of critical issues (e.g., revoked licenses)
- 📊 **Confidence Scores** - Multi-dimensional scoring system
- 📝 **Next Steps** - Actionable recommendations for each provider
- 🎨 **Modern UI** - Beautiful, responsive React interface

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11** - [Download](https://www.python.org/downloads/)
- **Node.js** - [Download](https://nodejs.org/)
- **Conda** - [Download Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### Installation (First Time Only)

**Windows:**
```powershell
# Run installer
.\scripts\install.bat
```

**What it does:**
1. Creates `crewai-env` conda environment
2. Installs Python dependencies (FastAPI, CrewAI, etc.)
3. Installs frontend dependencies (React, Vite)

⏱️ **Install time:** 3-5 minutes

---

### Starting the System

**Every time you want to run the system:**
```powershell
.\scripts\start_system.bat
```

This will:
1. Start the **Backend API** on port 8000
2. Start the **Frontend** on port 5173
3. Open your browser automatically

**URLs:**
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- **FastAPI** - Modern Python web framework
- **CrewAI** - AI agent orchestration framework
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

**Frontend:**
- **React** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **GSAP** - Animations

### Data Sources

The system validates against **6 mock data sources**:

1. **NPI Registry** (`npi_registry.json`) - National Provider Identifier records
2. **License Registry** (`license_registry.json`) - State medical licenses
3. **Hospital Roster** (`hospital_roster.json`) - Hospital staff directories
4. **Maps Listing** (`maps_listing.json`) - Online map/directory listings
5. **Clinic Website** (`clinic_website.html`) - Provider clinic websites
6. **Telemedicine Directory** (`telemedicine_directory.json`) - Online consultation platforms

### AI Agent System

**Three specialized AI agents work together:**

1. **Data Extraction Agent** - Pulls provider data from all sources
2. **Validation Agent** - Compares data, calculates confidence scores
3. **Risk Assessment Agent** - Identifies flags and generates recommendations

---

## 🧪 Mock Data & Test Scenarios

### Test Providers

The mock data includes **10 providers** with varying validation scenarios:

#### ✅ Clean Providers (High Confidence: 90-98%)
- **Dr Meera Reddy** - All sources match perfectly
- **Dr Priya Patel** - Consistent across sources
- **Dr Kavita Desai** - No issues detected

#### ⚠️ Providers with Discrepancies (Medium-High Confidence: 75-85%)

**Dr Aarav Mehta** (Cardiology)
- 📞 **Phone mismatch**: License registry shows +918123456790 (should be +918123456789)
- 📝 **Name variation**: Telemedicine shows "Dr. A. Mehta"
- **Confidence**: ~85%

**Dr Ritu Sharma** (Neurology)
- 🩺 **Specialty mismatch**: Telemedicine shows "Neuro-Rehabilitation Specialist"
- **Confidence**: ~75%

**Dr Vikram Singh** (Orthopedics)
- ❌ **Missing data**: Absent from Telemedicine directory
- **Confidence**: ~80%

#### 🚨 Critical Issues (Low Confidence: 20-45%)

**Dr Shalini Rao** (Dermatology) - HIGH PRIORITY
- 🟠 **License SUSPENDED** - Practicing with suspended license!
- 🏥 **Address mismatch**: Different locations in different sources
- **Confidence**: ~45%
- **Priority**: HIGH - Requires immediate manual review

**Dr Suresh Nair** (Gastroenterology) - CRITICAL
- 🔴 **License REVOKED** (Expired 2023-12-31)
- **Should NOT be practicing**
- **Confidence**: ~20%
- **Priority**: CRITICAL

---

## 💻 Usage Examples

### 1. Validate a Single Provider

**Via Web UI:**
1. Go to "Run Validation"
2. Enter provider name: "Dr Aarav Mehta"
3. Click "Validate Provider"
4. View results with confidence scores and matched sources

**Via API:**
```bash
curl -X POST "http://localhost:8000/validate" \\
  -H "Content-Type: application/json" \\
  -d '{"provider_name": "Dr Aarav Mehta"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "provider_name": "Dr Aarav Mehta",
    "confidence_scores": {
      "overall_confidence": 0.85,
      "identity_match": 0.88,
      "license_validity": 1.0,
      "contact_info_accuracy": 0.75
    },
    "validation_status": "VERIFIED",
    "sources_matched": ["npi", "license", "hospital", "maps", "clinic"],
    "issues": [
      {
        "issue": "Phone number mismatch detected",
        "severity": "LOW",
        "source": "license_registry"
      }
    ]
  }
}
```

### 2. Upload File for Batch Validation

**Upload Excel/PDF:**
1. Go to "Run Validation"
2. Click "Upload File"
3. Select `samples/sample_providers.xlsx`
4. Review all providers in the results

**Via API:**
```bash
curl -X POST "http://localhost:8000/upload" \\
  -F "file=@samples/sample_providers.xlsx"
```

### 3. View Provider Details

**Web UI:**
1. Go to "Directory"
2. Click on any provider (e.g., "Dr Shalini Rao")
3. See detailed view with:
   - 🚨 Issues & Risk Flags
   - 📊 Record Comparisons
   - ✅ Matched Sources
   - 📋 Next Steps

---

## 📚 API Documentation

### Base URL
`http://localhost:8000`

### Endpoints

#### `POST /validate`
Validate a single provider

**Request Body:**
```json
{
  "provider_name": "Dr Aarav Mehta",
  "phone": "+918123456789",  // optional
  "specialty": "Cardiology"    // optional
}
```

#### `POST /validate/batch`
Validate multiple providers

**Request Body:**
```json
{
  "providers": [
    {"provider_name": "Dr Aarav Mehta"},
    {"provider_name": "Dr Shalini Rao"}
  ]
}
```

#### `POST /upload`
Upload Excel or PDF file

**Form Data:**
- `file`: PDF or Excel file containing provider data

#### `GET /health`
Health check endpoint

#### `GET /docs`
Interactive API documentation (Swagger UI)

---

## 🔧 Troubleshooting

### Port Already in Use

**Error:** `Port 8000 is already in use`

**Solution:**
```powershell
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# Or edit scripts/start_system.bat and change port
```

### Conda Environment Not Found

**Error:** `Environment not found`

**Solution:**
```powershell
# Re-run installer
.\scripts\install.bat
```

### Frontend Not Loading

**Error:** Browser shows connection error

**Solution:**
```powershell
# Check if both windows are running
# If not, close all and restart
.\scripts\start_system.bat
```

### Missing Dependencies

**Error:** `Module not found`

**Solution:**
```powershell
# Reinstall dependencies
conda run -n crewai-env pip install -r requirements.txt
cd external_frontend
npm install
```

---

## 📂 Project Structure

```
provider_data_validation/
├── src/provider_data_validation/
│   ├── api.py                 # FastAPI routes
│   ├── services.py            # Validation orchestration
│   ├── models.py              # Pydantic data models
│   ├── file_processor.py      # PDF/Excel parsing
│   └── crews/
│       └── data_validation_crew/  # CrewAI agents
├── external_frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Validation.jsx
│   │   │   ├── Directory.jsx
│   │   │   └── ProviderDetail.jsx  # Detailed view
│   │   └── App.jsx
│   └── package.json
├── mock_data/                 # Validation data sources
│   ├── npi_registry.json
│   ├── license_registry.json
│   ├── hospital_roster.json
│   ├── maps_listing.json
│   ├── clinic_website.html
│   ├── telemedicine_directory.json
│   └── provider_credentials.txt
├── scripts/                   # Executable scripts
│   ├── install.bat            # One-time setup
│   ├── start_system.bat       # Start both backend + frontend
│   ├── start_system.sh        # Linux/Mac startup
│   ├── restart_backend.bat    # Restart just backend
│   └── restart_backend.ps1    # PowerShell restart
├── samples/                   # Sample data files
│   ├── sample_providers.xlsx  # Test data file
│   └── create_sample_file.py  # Sample file generator
├── tests/                     # Test files
│   └── test_fuzzy_matching.py
├── logs/                      # Runtime logs (gitignored)
├── output/                    # Generated outputs (gitignored)
├── docs/                      # Documentation
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── pyproject.toml             # Project metadata
```

---

## 🎨 UI Features

### Provider Detail Page Highlights

When viewing a provider with issues (e.g., Dr Shalini Rao):

- **Manual Review Banner** - Yellow alert for flagged providers
- **Issues Section** - Red/orange warnings for license problems
- **Record Comparison** - Side-by-side view of discrepancies
- **Source Evidence** - All matched sources displayed as badges
- **Next Steps** - Actionable recommendations

### Confidence Score Visualization

- **90-100%**: Green circle - Verified ✓
- **70-89%**: Yellow circle - Needs review ⚠️
- **Below 70%**: Red circle - Critical issues 🚨

---

## 🔮 Future Enhancements

- [ ] Real API integrations (NPI NPPES, state license APIs)
- [ ] Email/SMS verification workflows
- [ ] Machine learning for anomaly detection
- [ ] Historical tracking of provider changes
- [ ] Automated reports and alerts
- [ ] Multi-language support

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. View API docs at `http://localhost:8000/docs`
3. Review mock data files in `/mock_data`

---

**Built with ❤️ using CrewAI, FastAPI, and React**
