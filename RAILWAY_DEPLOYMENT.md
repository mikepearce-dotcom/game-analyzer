# Sentient Tracker - Railway Deployment Guide

This guide walks you through deploying Sentient Tracker to Railway.

## Prerequisites

1. **GitHub Account** - Railway deploys from Git repositories
2. **Railway Account** - Sign up at https://railway.app/
3. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
4. **MongoDB Atlas Account** (optional) - If not using Railway's MongoDB plugin

---

## Deployment Steps

### Step 1: Push Code to GitHub

```bash
cd Game-analyzer-main
git init
git add .
git commit -m "Initial commit - Emergent dependencies removed"
git remote add origin https://github.com/YOUR_USERNAME/game-analyzer.git
git push -u origin main
```

### Step 2: Set Up Railway Project

1. Go to https://railway.app/
2. Click **"New Project"**
3. Select **"Deploy from GitHub"**
4. Connect your GitHub account and select the `game-analyzer` repository
5. Railway will auto-detect the Python backend (from `Procfile`)

### Step 3: Configure Backend Service

Railway will create a service from your Procfile. Configure it:

1. Click on the service that was created
2. Go to **Settings**
3. Ensure **Root Directory** is set to `/` (or empty)
4. Set **Build Command**: `pip install -r backend/requirements.txt`
5. Set **Start Command**: `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`

### Step 4: Add MongoDB

#### Option A: Railway's MongoDB Plugin (Recommended)
1. In your Railway project, click **+ Add Service**
2. Search for **"MongoDB"** and add it
3. Railway automatically sets `MONGO_URL` environment variable ✅

#### Option B: MongoDB Atlas
1. Create a cluster at https://www.mongodb.com/cloud/atlas
2. Get your connection string: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`
3. In Railway, set `MONGO_URL` environment variable manually

### Step 5: Set Environment Variables

In Railway dashboard, go to **Variables** and add:

```
OPENAI_API_KEY = sk-...your-key...
DB_NAME = sentient_tracker
CORS_ORIGINS = https://yourdomain.railway.app,https://*.railway.app
```

**For MongoDB:**
- If using Railway MongoDB plugin: `MONGO_URL` is auto-set ✅
- If using Atlas: Add manually with your connection string

### Step 6: Deploy Frontend

Railway has two options for hosting frontend:

#### Option A: Deploy with Backend (Single Service)
Build static frontend and serve from backend:

```bash
cd frontend
npm install
npm run build
```

Add to `Procfile`:
```
release: pip install -r backend/requirements.txt && cd frontend && npm install && npm run build
web: cd backend && python -m http.server --directory ../frontend/build 8000 & uvicorn server:app --host 0.0.0.0 --port 8000
```

**Then in backend/server.py, add static file serving:**
```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")
```

#### Option B: Deploy Frontend Separately (Recommended)
1. Create new Railway service from `frontend/` directory
2. Build command: `npm install && npm run build`
3. Start command: `npm start` or serve with `npx serve -s build -l 3000`
4. Set `REACT_APP_BACKEND_URL` environment variable to your backend Railway URL

### Step 7: Verify Deployment

1. Go to your Railway project dashboard
2. Check each service's logs for errors
3. Click on **Deployments** tab to see build status
4. Visit your deployed app URL:
   - Backend: `https://yourdomain-backend.railway.app/api`
   - Frontend: `https://yourdomain-frontend.railway.app`

---

## Configuration Files

### Procfile (Already Created)
Tells Railway how to start your app:
```
web: cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
```

### railway.json (Already Created)
Defines environment variables for Railway's template system.

### Environment Variables Reference

| Variable | Required | Example |
|----------|----------|---------|
| `OPENAI_API_KEY` | ✅ Yes | `sk-...` |
| `MONGO_URL` | ✅ Yes | `mongodb+srv://...` or Railway auto-set |
| `DB_NAME` | ❌ No | `sentient_tracker` |
| `CORS_ORIGINS` | ❌ No | Auto-configured |

---

## Troubleshooting

### Build Fails: "No module named openai"
- Ensure `requirements.txt` is in `/backend/` 
- Check **Build Command** includes: `pip install -r backend/requirements.txt`

### 502 Bad Gateway
- Check backend logs: Railway Dashboard → Service → Logs
- Verify `MONGO_URL` is set and accessible
- Verify `OPENAI_API_KEY` is valid

### Frontend Can't Connect to Backend
- Set `REACT_APP_BACKEND_URL` in frontend service variables
- Example: `https://yourdomain-backend.railway.app`
- Verify CORS_ORIGINS includes your frontend URL

### MongoDB Connection Fails
- If using Atlas, add Railway's IPs to MongoDB whitelist:
  1. Go to MongoDB Atlas dashboard
  2. Network Access → Whitelist → Add IP
  3. Add `0.0.0.0/0` (allows all, or add Railway's specific IPs)

### Port Issues
- Railway assigns `$PORT` environment variable
- Ensure your app binds to `0.0.0.0:$PORT`
- Backend Procfile already handles this ✅

---

## Cost Estimation

**Railway Pricing (as of Feb 2026):**
- Compute: $5/month per service + usage (generally free tier covers small apps)
- Database: $5/month for MongoDB plugin
- **Total baseline: ~$10-15/month**

**OpenAI Usage:**
- GPT-4o-mini: ~$0.0001-0.0003 per request
- Typical game scan: $0.001-0.01 per scan
- **100 scans/month = ~$0.50-1.00**

---

## Production Checklist

- [ ] OPENAI_API_KEY is set and valid
- [ ] MONGO_URL is configured and accessible
- [ ] CORS_ORIGINS includes your frontend domain
- [ ] Backend service is healthy (green status)
- [ ] Frontend service is deployed
- [ ] Can sign up with email/password
- [ ] Can create and scan games
- [ ] AI analysis works (check backend logs for OpenAI calls)
- [ ] MongoDB stores data persistently

---

## Useful Railway Commands

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to existing Railway project
railway link <PROJECT_ID>

# View logs
railway logs --tail

# Set environment variables
railway variables set OPENAI_API_KEY=sk-...

# Deploy (if set up locally)
railway up
```

---

## Next Steps

1. Push code to GitHub
2. Connect GitHub to Railway
3. Add MongoDB (plugin or Atlas)
4. Set environment variables
5. Deploy and test
6. Share your deployed URL!

**Questions?** Check Railway docs: https://docs.railway.app/
