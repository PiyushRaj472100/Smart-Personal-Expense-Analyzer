# Deployment Guide

This document provides step-by-step instructions for deploying the Smart Personal Expense Analyzer application.

## Architecture

- **Frontend**: React/Vite application deployed on Vercel
- **Backend**: FastAPI Python application deployed on Render
- **Database**: MongoDB Atlas

## Prerequisites

1. GitHub repository with the code
2. Vercel account (for frontend)
3. Render account (for backend)
4. MongoDB Atlas account (for database)

## Environment Variables

### Frontend (.env.example)
```
VITE_API_URL=http://localhost:8000
```

### Backend (.env.example)
```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>/<database>?retryWrites=true&w=majority
JWT_SECRET=replace-with-a-64-char-random-secret
JWT_ALGO=HS256
CORS_ORIGINS=http://localhost:3000
```

## Deployment Steps

### 1. Deploy Backend on Render

1. **Connect GitHub to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" -> "Web Service"
   - Connect your GitHub account
   - Select the repository: `PiyushRaj472100/Smart-Personal-Expense-Analyzer`

2. **Configure the Service**
   - Name: `smart-expense-analyzer-backend`
   - Environment: `Python`
   - Root Directory: `python/backend`
   - Build Command: `pip install -r ../requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `JWT_SECRET`: Generate a secure 64-character random string
   - `JWT_ALGO`: `HS256`
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g., `https://your-app.vercel.app`)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note your backend URL (e.g., `https://your-app.onrender.com`)

### 2. Deploy Frontend on Vercel

1. **Connect GitHub to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New..." -> "Project"
   - Import your GitHub repository

2. **Configure the Project**
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Set Environment Variables**
   - `VITE_API_URL`: Your Render backend URL (e.g., `https://your-app.onrender.com`)

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete
   - Your frontend will be available at `https://your-app.vercel.app`

### 3. Update CORS Configuration

After deploying both frontend and backend:

1. Go to your Render backend service
2. Update the `CORS_ORIGINS` environment variable to include your Vercel URL:
   ```
   https://your-app.vercel.app
   ```
3. Redeploy the backend

## Important Notes

### Security
- Never commit `.env` files to version control
- Use strong, unique secrets for JWT_SECRET
- Configure MongoDB Atlas with proper IP whitelisting
- Enable SSL/TLS on all connections

### Performance
- Both Vercel and Render offer free tiers suitable for development
- Consider upgrading plans for production workloads
- Monitor usage and costs

### Troubleshooting

#### Common Issues
1. **CORS Errors**: Ensure `CORS_ORIGINS` includes your frontend URL
2. **Database Connection**: Verify MongoDB URI and network access
3. **Build Failures**: Check logs for missing dependencies or syntax errors

#### Health Checks
- Backend health endpoint: `https://your-backend-url.onrender.com/api/health`
- Frontend should redirect all routes to `index.html`

## Post-Deployment Checklist

- [ ] Frontend loads correctly on Vercel
- [ ] Backend API endpoints are accessible
- [ ] Database connection is working
- [ ] User authentication functions properly
- [ ] Expense tracking features work end-to-end
- [ ] CORS is properly configured
- [ ] Environment variables are set correctly
- [ ] SSL certificates are active
- [ ] Error monitoring is configured (optional)

## Monitoring and Maintenance

- Monitor Render dashboard for backend performance
- Check Vercel analytics for frontend usage
- Set up alerts for downtime or errors
- Regularly update dependencies
- Backup database regularly

## Scaling

When ready to scale:

1. **Backend**: Upgrade Render plan, add caching, implement load balancing
2. **Frontend**: Vercel automatically scales, consider edge functions for better performance
3. **Database**: Upgrade MongoDB Atlas tier, optimize queries, add indexes

## Support

For issues:
- Check service logs on respective platforms
- Review this documentation
- Create GitHub issues for code-related problems
- Contact platform support for infrastructure issues
