# Smart Personal Expense Analyzer

A full-stack personal finance application for tracking expenses, analyzing spending behavior, and generating AI-powered insights. This project combines a **FastAPI + MongoDB backend** with a **React + Vite frontend** to help users manage transactions, detect unusual spending, and view financial analytics in a modern dashboard.

---

## Features

### Core Features
- User signup and login with JWT authentication
- Add, view, and delete expense transactions
- Dashboard with financial overview
- Analytics with charts and time-based filters
- User profile management
- SMS-based transaction parsing

### AI-Powered Features
- Automatic expense categorization
- Spending anomaly detection
- Personalized financial tips
- Financial health insights

### Frontend Highlights
- Responsive UI built with React
- Clean layout with sidebar navigation
- Interactive charts and analytics
- Mobile-friendly design
- Centralized API service layer
- Authentication context and protected routes

---

## Tech Stack

### Backend
- **Python**
- **FastAPI**
- **MongoDB**
- **PyMongo**
- **JWT Authentication**

### Frontend
- **React 18**
- **Vite**
- **TailwindCSS**
- **React Router**
- **Axios**
- **Recharts**
- **Lucide React**

---

## Project Structure

```text
Smart_Personal_Expense_Analyzer/
├── python/
│   ├── backend/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── db_test.py
│   │   ├── .env                  # Create this manually
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── transactions.py
│   │   │   ├── dashboard.py
│   │   │   ├── analytics.py
│   │   │   └── profile.py
│   │   └── __pycache__/          # Auto-generated
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── categorizer.py
│   │   ├── anomaly.py
│   │   ├── tips_engine.py
│   │   ├── sms_parser.py
│   │   └── train_models.ipynb    # Optional
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   └── Layout.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Signup.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Transactions.jsx
│   │   │   ├── Analytics.jsx
│   │   │   └── Profile.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   └── context/
│   │       └── AuthContext.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .eslintrc.cjs
│   ├── .gitignore
│   ├── .env.example
│   ├── .env                  # Optional, create if needed
│   └── README.md
│
├── README.md
├── SETUP.md
├── PROJECT_STRUCTURE.md
└── requirements.txt          # Optional root reference file
```

---

## Important File Overview

### Backend
- `python/backend/main.py` — FastAPI app entry point, CORS setup, route registration
- `python/backend/database.py` — MongoDB connection and collection setup
- `python/backend/routes/auth.py` — Signup and login endpoints
- `python/backend/routes/transactions.py` — Transaction CRUD and AI categorization
- `python/backend/routes/dashboard.py` — Dashboard summary data
- `python/backend/routes/analytics.py` — Analytics with filtering
- `python/backend/routes/profile.py` — Profile fetch and update
- `python/ai/categorizer.py` — Expense categorization logic
- `python/ai/anomaly.py` — Spending anomaly detection
- `python/ai/tips_engine.py` — Personalized tips generation
- `python/ai/sms_parser.py` — SMS transaction extraction

### Frontend
- `frontend/src/App.jsx` — Main app with routing
- `frontend/src/components/Layout.jsx` — App layout and sidebar navigation
- `frontend/src/pages/Dashboard.jsx` — Financial overview and insights
- `frontend/src/pages/Transactions.jsx` — Add, list, delete, and parse transactions
- `frontend/src/pages/Analytics.jsx` — Charts and analytics
- `frontend/src/pages/Profile.jsx` — User settings and profile management
- `frontend/src/services/api.js` — Axios API configuration
- `frontend/src/context/AuthContext.jsx` — Authentication state provider

---

## Prerequisites

Before running the project, make sure you have:

- **Python 3.8+**
- **Node.js 18+**
- **npm**
- **MongoDB** installed locally or a MongoDB Atlas connection string

---

## Environment Variables

### Backend: `python/backend/.env`

```env
MONGO_URI=mongodb://localhost:27017/
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_ALGO=HS256
```

### Frontend: `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## Installation and Setup

## 1) Clone the Repository

```bash
git clone https://github.com/your-username/Smart_Personal_Expense_Analyzer.git
cd Smart_Personal_Expense_Analyzer
```

---

## 2) Backend Setup

### Move to the Python folder
```bash
cd python
```

### Create a virtual environment
#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux
```bash
python -m venv venv
source venv/bin/activate
```

### Install Python dependencies
```bash
pip install -r requirements.txt
```

### Move to backend folder
```bash
cd backend
```

### Create `.env` file
```env
MONGO_URI=mongodb://localhost:27017/
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_ALGO=HS256
```

### Run the backend server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Backend URLs
- API Base URL: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`

---

## 3) Frontend Setup

Open a **new terminal** and go to the frontend folder:

```bash
cd Smart_Personal_Expense_Analyzer/frontend
```

### Install frontend dependencies
```bash
npm install
```

### Create `.env` file if needed
```env
VITE_API_URL=http://localhost:8000
```

### Start the frontend
```bash
npm run dev
```

### Frontend URL
- Frontend App: `http://localhost:3000`

> If your Vite config uses a different port, use that configured port instead.

---

## Quick Start

After setup:

1. Start MongoDB
2. Run the backend on port `8000`
3. Run the frontend on port `3000`
4. Open the app in your browser
5. Create an account or log in
6. Add transactions and explore analytics

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Register a new user |
| POST | `/api/auth/login` | Log in a user |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/` | Get dashboard overview |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions/` | Get all transactions |
| POST | `/api/transactions/add` | Add a transaction |
| POST | `/api/transactions/from-sms` | Parse transaction from SMS |
| DELETE | `/api/transactions/{id}` | Delete transaction |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/analytics/?period=weekly` | Weekly analytics |
| GET | `/api/analytics/?period=monthly` | Monthly analytics |
| GET | `/api/analytics/?period=yearly` | Yearly analytics |

### Profile
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/profile/` | Get user profile |
| PUT | `/api/profile/` | Update user profile |

### Health / Docs
| Method | Endpoint | Description |
|---|---|---|
| GET | `/docs` | Swagger API documentation |
| GET | `/api/health` | Health check if implemented |

---

## How the Application Works

### Authentication Flow
- User signs up or logs in
- Backend validates credentials
- JWT token is generated
- Frontend stores auth state
- Protected pages become accessible

### Transaction Flow
- User adds a new expense manually or via SMS
- Backend stores transaction in MongoDB
- AI module categorizes the expense
- Dashboard and analytics update accordingly

### Analytics Flow
- Transactions are aggregated by selected period
- Charts visualize spending trends
- AI modules detect patterns and anomalies
- Personalized tips are generated for the user

---

## Example Run Commands

### Backend
```bash
cd Smart_Personal_Expense_Analyzer/python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd Smart_Personal_Expense_Analyzer/frontend
npm install
npm run dev
```

---

## Troubleshooting

### Backend Issues

#### 1. Module not found
Make sure you:
- Installed all Python dependencies
- Activated the virtual environment
- Are running from `python/backend/`

#### 2. MongoDB connection error
Check that:
- MongoDB is running locally
- `MONGO_URI` is correct
- Atlas connection string is valid if using cloud MongoDB

#### 3. JWT errors
Check that:
- `.env` exists inside `python/backend/`
- `JWT_SECRET` is defined
- `JWT_ALGO` is set correctly

---

### Frontend Issues

#### 1. Frontend cannot connect to backend
Make sure:
- Backend is running on port `8000`
- `VITE_API_URL` matches the backend URL
- CORS is properly configured in FastAPI

#### 2. `npm install` fails
Try:
```bash
rm -rf node_modules package-lock.json
npm install
```

#### 3. Port already in use
You can:
- Stop the process using the port
- Change the frontend port in `vite.config.js`
- Change backend port in the uvicorn command if needed

---

## Security Notes

Before deploying to production:

- Change `JWT_SECRET` to a strong random value
- Never commit `.env` files to GitHub
- Restrict CORS origins to your production domain
- Use secure MongoDB credentials
- Validate and sanitize all inputs
- Use HTTPS in production

---

## Production Deployment Checklist

- Set real environment variables
- Use a strong JWT secret
- Configure production MongoDB
- Build frontend using:

```bash
npm run build
```

- Deploy backend to a Python hosting platform
- Deploy frontend to a static hosting provider
- Update frontend API URL to production backend URL

---

## Suggested `.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
venv/
.env

# Node
node_modules/
dist/

# OS / Editor
.DS_Store
.vscode/
.idea/
```

---

## Future Improvements

- Budget planning and alerts
- Recurring expense detection
- Multi-currency support
- Export reports as PDF or CSV
- Admin analytics dashboard
- Email notifications
- Advanced ML-based prediction models

---

## License

This project is suitable for:
- Academic submission
- Portfolio showcase
- Learning full-stack development
- Experimenting with AI-based finance tools

Add your preferred license here, for example:

```text
MIT License
```

---

## Contributing

If you want to contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your fork
5. Open a pull request

---

## Final Notes

This project is a strong full-stack application that demonstrates:
- Backend API development with FastAPI
- MongoDB integration
- JWT authentication
- React frontend architecture
- AI-based finance features
- Dashboard and analytics design

It is ideal for a **resume project**, **GitHub portfolio**, or **college major project**.

---