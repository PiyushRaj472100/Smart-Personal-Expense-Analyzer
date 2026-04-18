# Smart Expense Analyzer - Frontend

A modern, responsive React frontend for the Smart Expense Analyzer application.

## Features

- 🎨 Modern UI with TailwindCSS
- 📱 Fully responsive design
- 🔐 Authentication (Login/Signup)
- 💰 Dashboard with financial overview
- 📊 Analytics with charts and insights
- 📝 Transaction management
- 👤 User profile management
- 🤖 SMS transaction parser

## Tech Stack

- React 18
- React Router v6
- Vite
- TailwindCSS
- Recharts (for analytics charts)
- Axios (for API calls)
- Lucide React (icons)

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm/yarn installed
- Backend server running on port 8000

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file (optional, defaults to http://localhost:8000):
```bash
cp .env.example .env
```

Edit `.env` if your backend is running on a different port/URL:
```
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` folder.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── context/        # React context (Auth)
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── index.html          # HTML template
├── package.json        # Dependencies
├── vite.config.js      # Vite configuration
├── tailwind.config.js  # TailwindCSS configuration
└── postcss.config.js   # PostCSS configuration
```

## API Endpoints

The frontend communicates with the backend API at `/api/`:

- `/api/auth/signup` - User registration
- `/api/auth/login` - User login
- `/api/dashboard/` - Dashboard data
- `/api/transactions/` - Transaction CRUD operations
- `/api/analytics/` - Analytics data
- `/api/profile/` - User profile management

## Notes

- The frontend uses a proxy configuration in `vite.config.js` to forward `/api` requests to the backend
- JWT tokens are stored in localStorage
- All API calls automatically include the auth token in headers

