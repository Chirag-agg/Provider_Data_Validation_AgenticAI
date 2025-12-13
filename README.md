# Provider Data Validation System

> **AI-Powered Healthcare Provider Validation with Interactive CALL/SMS Verification**  
> Automatically validates provider credentials across multiple data sources using hybrid AI validation (Ollama LLM + deterministic rules), calculates realistic confidence scores, and provides interactive CALL/SMS-based verification for data corrections.

---

##  Key Features

### 1. **Hybrid Validation Engine**
- **Primary**: Ollama CrewAI with LLM-powered intelligent analysis
- **Fallback**: Deterministic helper functions for 100% reliability
- **Weighted Multi-Dimensional Scoring**:
  - Identity Match (25%) - Cross-source provider matching
  - License Validity (20%) - Certification status check
  - Location Accuracy (20%) - Phone/address verification
  - Specialty Verification (15%) - Medical specialty confirmation
  - Hospital Affiliation (10%) - Current affiliation check
  - Data Consistency (10%) - Cross-source discrepancy detection
- **Realistic Confidence Scores**: 60%-95% range with penalty-based adjustments

### 2. **Interactive CALL/SMS Verification** (Demo Mode)
-  Smart questioning - asks only about **mutable fields** (address, hospital)
-  Chat-style conversation display in frontend
-  Real-time status updates
-  **DEMO_MODE** - Limits CALL/SMS to you for safe demos (no charges!)

### 3. **Multi-Source Data Extraction**
Validates against 5 independent data sources:
- **NPI Registry** - Provider identity and basic info
- **License Registry** - Certification status and expiration
- **Hospital Roster** - Affiliation and department
- **Maps Listing** - Practice location verification
- **Clinic Website** - HTML scraping for additional details
- **Historical Data** - Tracks changes in data

### 4. **Modern React Frontend**
- **Dashboard** - System stats + Interactive WorldMap
- **Directory** - Provider search and filtering
- **Provider Detail** - Full validation breakdown with SMS conversation
- **Bulk Outreach** - CALL/SMS campaign management
- **Drift Monitoring** - Automated change detection
- **Manual Review** - Flagged records queue
- **Activity Logs** - Complete audit trail

### 5. **Geographic Visualization**
- Interactive WorldMap with zoom/pan
- Pulsing markers for provider concentrations
- Regional statistics (West, Central, East, International)
- Hover effects with dynamic country colors

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (for AI validation)
- Conda (recommended)

### Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd provider_data_validation
   ```

2. **Run Setup Script**
   ```bash
   # Windows
   scripts\install.bat
   
   # This will:
   # - Create conda environment
   # - Install Python dependencies
   # - Install frontend dependencies
   # - Set up Ollama model
   ```

3. **Configure Environment**
   ```bash
   # Copy example and edit
   cp .env.example .env
   
   # Key settings:
   DEMO_MODE=true              # Disable real SMS
   OLLAMA_MODEL=llama3.1:latest
   API_PORT=8000
   ```

4. **Start System**
   ```bash
   # Windows
   scripts\start_system.bat
   
   # Starts:
   # - Backend API (port 8000)
   # - Frontend Dev Server (port 5173)
   ```

5. **Access Application**
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

---

## 🎯 Validation Flow

1. **Input Received** - Provider name(optional - specialty, contact info)
2. **Ollama Crew** - AI-powered analysis with context understanding
3. **Extract from Sources** - Query 5 data sources with fuzzy matching
4. **Calculate Scores** - Weighted scoring across 6 dimensions
5. **Apply Penalties**:
   - Missing sources: -5% each
   - Data inconsistencies: -8% each
   - Inactive license: -10%
   - Location issues: -7%
6. **Add Variance** - ±2% deterministic randomness
7. **Final Confidence** - 60%-95% realistic range
8. **Status Decision**:
   - ≥60%: VERIFIED
   - 40-60%: PARTIALLY_VERIFIED
   - <40%: UNVERIFIED

---

## 📡 API Endpoints

### Validation
```http
POST   /validate              # Validate single provider
POST   /batch/validate        # Validate multiple providers
GET    /batch/{batch_id}      # Check batch status
GET    /providers             # List validated providers
GET    /providers/{id}        # Get provider details
GET    /stats                 # System statistics
```

### Verification (CALL/SMS)
```http
POST   /verify/start          # Initiate SMS verification
POST   /verify/webhook        # Twilio webhook handler
GET    /verify/session/{id}   # Check session status
GET    /verify/history/{id}   # Verification history
```

### Health
```http
GET    /health                # System health check
```

---

## 🧪 Testing

### Quick Test (API)
```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "Dr. Aarav Mehta",
    "phone": "+91 98765 43210",
    "specialty": "Cardiology"
  }'
```

### Expected Response
```json
{
  "provider_id": "uuid-here",
  "provider_name": "Dr. Aarav Mehta",
  "validation_status": "VERIFIED",
  "confidence_scores": {
    "overall_confidence": 0.87,
    "identity_match": 0.95,
    "license_validity": 1.0,
    "contact_info_accuracy": 0.85,
    "hospital_affiliation": 0.9,
    "specialty_verification": 0.8
  },
  "sources_matched": ["npi", "license", "hospital", "maps"],
  "issues": [],
  "requires_manual_review": false
}
```

---

## 🔐 Environment Variables

### Required
```bash
# Ollama (AI Validation)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest

# Demo Mode
DEMO_MODE=true                 # Set to false for production
```

### Optional (CALL/SMS Verification)
```bash
# Twilio Configuration
TWILIO_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
NOTIFY_TO=+your_test_number    # Fallback number for testing
```

---

## 🎨 Frontend Features

### StatCards
- **Total Providers** - System-wide count
- **Issues Found** - Flagged records
- **Auto Updated** - Successfully validated
- **Needs Review** - Manual attention required
- **Avg Confidence** - Overall quality score

### WorldMap
- Interactive geography with zoom/pan
- Provider distribution by region
- Pulsing markers for concentrations
- Neon color effects on hover
- Regional statistics display

### Provider Detail
- Full validation breakdown
- Confidence scores by dimension
- Matched sources visualization
- SMS conversation display (demo mode)
- Verification history timeline

---

## 🔧 Project Structure

```
provider_data_validation/
├── src/provider_data_validation/
│   ├── api.py                          # FastAPI endpoints
│   ├── services.py                     # Validation orchestration
│   ├── models.py                       # Pydantic models
│   ├── main.py                         # CLI entry point
│   ├── crews/
│   │   ├── data_validation_crew/       # AI validation
│   │   ├── drift_monitoring_crew/      # Change detection
│   │   └── notification_crew/          # Alerts
│   └── tools/
│       ├── twilio_tools.py             # SMS functionality
│       ├── verification_service.py     # SMS verification logic
│       ├── verification_store.py       # Session management
│       ├── ocr_agent.py                # Vision LLM OCR
│       └── file_processor.py           # Document handling
├── external_frontend/
│   └── src/
│       ├── pages/                      # Dashboard, Directory, etc.
│       ├── components/                 # StatCard, WorldMap, etc.
│       └── services/                   # API client
├── mock_data/                          # Test data sources
│   ├── npi_registry.json
│   ├── license_registry.json
│   ├── hospital_roster.json
│   ├── maps_listing.json
│   └── clinic_website.html
└── scripts/
    ├── install.bat                     # Setup automation
    └── start_system.bat                # Launch script

```

## 📝 Mock Data & Test Scenarios

The system includes realistic mock data for testing:

### Providers
- **Dr. Aarav Mehta** - Cardiology, 95% confidence (perfect match)
- **Dr. Shalini Rao** - Dermatology, 72% confidence (specialty mismatch)
- **Dr. Vikram Singh** - Orthopedics, 65% confidence (multiple issues)
- **Dr. Priya Patel** - Pediatrics, 78% confidence (minor discrepancies)

### Test Scenarios
1. **Perfect Match** - All sources agree, 90-95% confidence
2. **Minor Discrepancy** - Phone format different, 80-89% confidence
3. **Specialty Mismatch** - "Cardiology" vs "Interventional Cardiology", 70-79%
4. **Multiple Issues** - Missing sources + data conflicts, 60-69%
5. **Failed Validation** - Inactive license, <60% confidence

---


## 🐛 Troubleshooting

### Ollama Not Responding
```bash
# Start Ollama service
ollama serve

# Pull required model
ollama pull llama3.1:latest

# Test
ollama run llama3.1:latest "Hello"
```

### Frontend Build Errors
```bash
cd external_frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend Import Errors
```bash
# Verify activated environment
conda activate crewai-env

# Reinstall dependencies
pip install -r requirements.txt
```

## 📚 Key Learnings & Design Decisions

1. **Hybrid Validation** - Combining AI with deterministic fallbacks ensures reliability
2. **Realistic Scoring** - Weighted dimensions + penalties + variance = believable results
3. **Demo Mode** - Essential for hackathons to avoid charges and demonstrate functionality
4. **Phone Verification** - Successful SMS delivery implicitly validates phone number

---

## 🎯 Production Deployment

### Checklist
- [ ] Set `DEMO_MODE=false`
- [ ] Configure valid Twilio credentials
- [ ] Set up ngrok or production webhooks
- [ ] Migrate to persistent database (replace in-memory storage)
- [ ] Set up error monitoring (Sentry, etc.)
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS
- [ ] Set up backup/restore procedures

### Recommended Infrastructure
- **Backend**: AWS EC2 / Azure VM / DigitalOcean
- **Frontend**: Vercel / Netlify
- **Database**: PostgreSQL for sessions/history
- **SMS**: Twilio with local number for target region
- **Monitoring**: Grafana + Prometheus

---

## 📞 Support & Documentation

- **API Docs**: http://localhost:8000/docs (when running)
- **Health Check**: http://localhost:8000/health

---

## 🎉 Project Status

**✅ PRODUCTION READY FOR HACKATHON!**

All features implemented, tested, and documented:
- ✅ Hybrid AI + Rule-based validation
- ✅ Interactive SMS verification (demo mode)
- ✅ Beautiful React UI with WorldMap
- ✅ Realistic confidence scoring (60-95%)
- ✅ Multi-source data integration
- ✅ Complete API documentation
- ✅ Comprehensive testing

---

*Built with CrewAI, FastAPI, React, and Ollama*  
*Last Updated: December 13, 2025*
