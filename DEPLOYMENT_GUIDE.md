# 🚀 Deployment Guide - Tech Job Scraper

This guide will help you deploy your tech job scraper to Railway (backend) and Netlify (frontend) for **free**.

## 📋 Prerequisites

1. GitHub account with your code pushed
2. Railway account (free)
3. Netlify account (free)

## 🔧 Backend Deployment (Railway)

### Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Click "Deploy from GitHub repo"

### Step 2: Deploy Backend
1. **Select Repository**: Choose your `job-scraper` repository
2. **Railway will automatically detect**: Python app and use the `railway.toml` config
3. **Environment Variables**: Railway will ask you to set these:
   ```
   DATABASE_URL=postgresql://railway-provided-url  (Railway provides this automatically)
   PORT=8000  (Railway provides this automatically)
   ```
4. **Deploy**: Click "Deploy" - Railway will:
   - Install Python dependencies
   - Install Playwright browsers
   - Start your FastAPI server
   - Start your scheduler (twice daily scraping)
   - Provide a public URL like: `https://your-app-name.railway.app`

### Step 3: Verify Backend
- Visit `https://your-app-name.railway.app/health` - should return `{"status": "healthy"}`
- Visit `https://your-app-name.railway.app/docs` - should show API documentation
- Check logs in Railway dashboard to see scraping working

## 🎨 Frontend Deployment (Netlify)

### Step 1: Create Netlify Account
1. Go to [netlify.com](https://netlify.com)
2. Sign up with your GitHub account
3. Click "Add new site" → "Import from Git"

### Step 2: Deploy Frontend
1. **Select Repository**: Choose your `job-scraper` repository
2. **Build Settings** (Netlify will auto-detect from `netlify.toml`):
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/build`
3. **Environment Variables**: Set this in Netlify:
   ```
   REACT_APP_API_URL=https://your-railway-app.railway.app
   ```
   (Replace with your actual Railway URL)
4. **Deploy**: Click "Deploy site"

### Step 3: Update API URL
1. **Get your Railway URL** from Railway dashboard
2. **Update netlify.toml**:
   ```toml
   REACT_APP_API_URL = "https://your-actual-railway-url.railway.app"
   ```
3. **Push to GitHub** - Netlify will auto-redeploy

## ✅ Verification Checklist

### Backend (Railway)
- [ ] Health endpoint working: `/health`
- [ ] API docs accessible: `/docs`
- [ ] Companies endpoint: `/companies` (should show Apple & NVIDIA)
- [ ] Jobs endpoint: `/jobs` (should return job listings)
- [ ] Scheduler running (check Railway logs for scraping activity)

### Frontend (Netlify)
- [ ] Site loads without errors
- [ ] Company filter dropdown shows Apple & NVIDIA
- [ ] Job listings display correctly
- [ ] Filtering works (company, location, etc.)
- [ ] No console errors in browser

## 🔄 Automatic Updates

Both platforms will automatically redeploy when you push to GitHub:
- **Railway**: Backend API and scheduler restart with new code
- **Netlify**: Frontend rebuilds and deploys new version

## 📊 Monitoring

### Railway Logs
```bash
# View in Railway dashboard or via CLI
railway logs
```

### Netlify Logs
- Check build logs in Netlify dashboard
- Use browser dev tools for frontend errors

## 🛠️ Troubleshooting

### Common Issues

#### Backend Won't Start
1. Check Railway logs for Python errors
2. Verify `requirements.txt` has all dependencies
3. Check environment variables are set

#### Frontend Can't Connect to API
1. Verify `REACT_APP_API_URL` is set correctly in Netlify
2. Check CORS settings in FastAPI
3. Test API URL directly in browser

#### Scheduler Not Running
1. Check Railway logs for scheduler errors
2. Verify database connection
3. Check Playwright browser installation

#### Database Issues
1. Railway provides PostgreSQL automatically
2. Check connection string in logs
3. Verify database migrations ran

## 💰 Cost Breakdown

### Railway (Backend)
- **Free tier**: 500 hours/month + $5 credit
- **Your usage**: ~24/7 = 720 hours/month
- **Estimated cost**: $0-5/month (within free limits for small apps)

### Netlify (Frontend)
- **Free tier**: 100GB bandwidth/month
- **Your usage**: Minimal for personal/portfolio use
- **Estimated cost**: $0/month

### Total Monthly Cost: $0-5

## 🔐 Security Notes

- Railway automatically handles HTTPS
- Netlify automatically handles HTTPS
- Database credentials managed by Railway
- No secrets in your code (all in environment variables)

## 📱 URLs After Deployment

You'll get two URLs:
- **Frontend**: `https://your-netlify-site.netlify.app`
- **Backend API**: `https://your-railway-app.railway.app`

## 🎉 Success!

Once deployed, your job scraper will:
- ✅ Scrape Apple & NVIDIA jobs twice daily (12 PM & 12 AM)
- ✅ Store data in PostgreSQL database
- ✅ Serve jobs via REST API
- ✅ Display jobs in React frontend
- ✅ Auto-deploy on code changes
- ✅ Run 24/7 for free (or very low cost)

---

## 🆘 Need Help?

If you encounter issues:
1. Check the logs in Railway/Netlify dashboards
2. Verify environment variables are set correctly
3. Test API endpoints directly
4. Check GitHub Actions if using CI/CD 