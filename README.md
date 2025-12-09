# Provider Data Validation System

## Quick Start

\\\ash
# Install once
install.bat

# Start system
start_system.bat
\\\

Then visit:
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## What It Does

Validates healthcare providers against multiple data sources:
- NPI Registry
- License Registry  
- Hospital Roster
- Maps Listing
- Clinic Websites

Returns confidence scores (0-1) and risk flags.

## API Endpoints

- \POST /validate\ - Validate single provider
- \POST /validate/batch\ - Validate multiple providers
- \POST /upload\ - Upload PDF/Excel file
- \GET /health\ - Health check
- \GET /docs\ - Interactive API docs

## File Structure

\\\
src/provider_data_validation/
 api.py              # FastAPI application
 services.py         # Validation logic
 models.py           # Data models
 file_processor.py   # PDF/Excel extraction

external_frontend/      # React app
mock_data/              # Sample data sources
\\\

## Troubleshooting

**Port 8000 already in use?**
\\\ash
# Edit start_system.bat, change:
set PORT=8001
\\\

**npm command not found?**
Install Node.js: https://nodejs.org/

**Python not found?**
Install Python: https://www.python.org/downloads/

## Done

Everything is set up. Just run the scripts and start validating.
