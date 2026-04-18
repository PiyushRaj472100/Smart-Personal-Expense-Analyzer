# Backend Setup Instructions

## Quick Start

1. **Navigate to backend directory:**
```bash
cd python/backend
```

2. **Create `.env` file:**
```env
MONGO_URI=mongodb://localhost:27017/
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGO=HS256
```

3. **Install dependencies** (from python directory):
```bash
cd ..
pip install -r requirements.txt
```

4. **Run the server:**
```bash
cd backend
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
python/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # MongoDB connection
│   ├── routes/              # API routes
│   │   ├── auth.py
│   │   ├── transactions.py
│   │   ├── dashboard.py
│   │   ├── analytics.py
│   │   └── profile.py
│   └── .env                 # Environment variables (create this)
└── ai/                      # AI modules
    ├── categorizer.py
    ├── anomaly.py
    ├── tips_engine.py
    └── sms_parser.py
```

## Important Notes

- The backend must be run from the `backend/` directory
- MongoDB must be running and accessible
- All imports are relative to the python/ directory (added to sys.path by main.py)
- CORS is configured to allow all origins (update for production)

