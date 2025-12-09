# 🚀 GETTING STARTED - Start Here

**Welcome to the Provider Data Validation System!**

This is your entry point. Follow the steps below to get everything running.

## ⚠️ IMPORTANT: If you got an error starting the system

If you saw an error like `[Errno 11001] getaddrinfo failed`, the issue has been fixed!
→ Read: **[SETUP_FIX.md](SETUP_FIX.md)** for complete details and solutions.

## ⏱️ Expected Time: 5 Minutes

## ✅ Step 1: Verify Prerequisites (1 minute)

Check you have these installed:

```bash
# Check Python
python --version
# Should be 3.10 or higher

# Check Node.js
node --version
npm --version
# Should be 18 or higher

# Check pip
pip --version
```

If any are missing, install them:

- Python: <https://www.python.org/downloads/>
- Node.js: <https://nodejs.org/>

## 📦 Step 2: Install Dependencies (2 minutes)

### Easy Way (Recommended - Windows)

```bash
install.bat
```

### Manual Way

```bash
# Navigate to project root
cd provider_data_validation

# Install Python dependencies
pip install fastapi uvicorn pydantic python-multipart openpyxl pypdf beautifulsoup4 httpx

# Install frontend dependencies
cd external_frontend
npm install
cd ..
```

## 🔧 Step 3: Setup Configuration (30 seconds)

```bash
# Copy environment template
copy .env.example .env
# On Linux/Mac: cp .env.example .env
```

Edit `.env` if needed (optional for quick test):

```
HOST=0.0.0.0
PORT=8000
```

## ▶️ Step 4: Run the System (1 minute)

### **Option A: Windows Users** (Recommended)

```bash
start_system.bat
```

Two terminal windows will open automatically:

- **Backend**: Running on <http://localhost:8000>
- **Frontend**: Running on <http://localhost:5173>

### **Option B: Linux/Mac Users**

```bash
chmod +x start_system.sh
./start_system.sh
```

### **Option C: Manual (Any OS)**

Open 2 terminals:

**Terminal 1 - Backend:**

```bash
python -m uvicorn src.provider_data_validation.api:app --reload --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd external_frontend
npm run dev
```

## ✨ Step 5: Verify Everything Works (1 minute)

### Check Backend

```bash
curl http://localhost:8000/health
```

Should see: `{"status":"healthy",...}`

### Open Frontend

Visit: <http://localhost:5173>

### Open API Documentation

Visit: <http://localhost:8000/docs>

## 🎉 Success

Your system is now running!

- **Frontend Dashboard**: <http://localhost:5173>
- **API Swagger Docs**: <http://localhost:8000/docs>
- **Backend API**: <http://localhost:8000>

## 🧪 Quick Test

Try validating a provider:

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "Dr Aarav Mehta",
    "phone": "8123456789"
  }'
```

Should return a detailed validation result with confidence scores!

## 📚 Next: Read Documentation

Now that everything is running, learn about the system:

1. **[QUICK_START.md](QUICK_START.md)** - 5-minute overview
2. **[SYSTEM_README.md](SYSTEM_README.md)** - Complete guide
3. **[API_INTEGRATION.md](API_INTEGRATION.md)** - API reference
4. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Test everything

Or jump directly to:

- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Navigation guide

## 🆘 Troubleshooting

### "Port 8000 already in use"

```bash
# Change the port
set PORT=8001
python -m uvicorn src.provider_data_validation.api:app --port 8001
```

### "ModuleNotFoundError"

```bash
# Reinstall dependencies
pip install -e . --force-reinstall
```

### "npm: command not found"

- Node.js is not installed or not in PATH
- Restart your terminal after installation

### "Vite: Cannot find module"

```bash
cd external_frontend
rm -rf node_modules
npm install
```

See [QUICK_START.md](QUICK_START.md) for more troubleshooting.

## 🎯 Common Next Steps

### I want to

**...test the API**
→ Go to <http://localhost:8000/docs> and use Swagger UI

**...understand the system**
→ Read [SYSTEM_README.md](SYSTEM_README.md)

**...customize validation**
→ Edit `src/provider_data_validation/services.py`

**...add new endpoints**
→ Edit `src/provider_data_validation/api.py`

**...integrate with my app**
→ Use `external_frontend/src/services/api.js` as reference

**...deploy to production**
→ Read Docker section in [SYSTEM_README.md](SYSTEM_README.md)

**...run all tests**
→ Follow [TESTING_GUIDE.md](TESTING_GUIDE.md)

## 📋 System Components

- **Backend API** (FastAPI) - Port 8000 - `src/provider_data_validation/api.py`
- **Frontend** (React/Vite) - Port 5173 - `external_frontend/`
- **Mock Data** - `mock_data/` folder
- **Documentation** - 6 markdown files (start with QUICK_START.md)

## 🔗 Important Links

| Resource | URL/File |
|----------|----------|
| Frontend | <http://localhost:5173> |
| API Docs | <http://localhost:8000/docs> |
| API Root | <http://localhost:8000> |
| Full Docs | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |
| System Guide | [SYSTEM_README.md](SYSTEM_README.md) |
| API Reference | [API_INTEGRATION.md](API_INTEGRATION.md) |

## ✅ Verification Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed  
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Health check passes
- [ ] API docs load
- [ ] Frontend dashboard visible

## 🎓 30-Second System Overview

**What is this?**
An AI-powered system that validates medical providers by checking them against multiple data sources.

**How does it work?**

1. User provides provider info (PDF, Excel, or API)
2. System searches 5 data sources
3. Calculates confidence scores
4. Returns validation result with risk flags

**Key Features:**

- Batch processing (validate 1000s at once)
- Confidence scoring (6 dimensions)
- Risk flagging (inactive licenses, etc.)
- RESTful API (10 endpoints)
- Interactive dashboard
- Production-ready Docker setup

**Use Cases:**

- Insurance verification
- Provider onboarding
- Fraud detection
- Hospital credentialing
- Licensing compliance

---

**Ready to dive deeper?**

Start with [QUICK_START.md](QUICK_START.md) for a complete 5-minute guide!

**Questions?** Check [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for navigation.

---

**Status**: ✅ Ready to Use
**Time to First Validation**: ~5 minutes
**Time to Full Understanding**: ~2 hours
