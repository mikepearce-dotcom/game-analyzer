# Railway Quick Start

Deploy your Sentient Tracker app to Railway in 5 minutes!

## 1. Push to GitHub
```bash
git init
git add .
git commit -m "Deploy to Railway"
git remote add origin https://github.com/YOUR_USERNAME/game-analyzer.git
git push -u origin main
```

## 2. Create Railway Project
- Go to https://railway.app/
- Click "New Project" → "Deploy from GitHub"
- Select your `game-analyzer` repository
- Railway auto-detects the Python backend from `Procfile`

## 3. Add MongoDB
- In Railway project: **+ Add Service** → Search **MongoDB**
- Railway auto-sets `MONGO_URL` environment variable

## 4. Set Environment Variables
In Railway dashboard → **Variables**, add:
```
OPENAI_API_KEY = sk-your-key-here
DB_NAME = sentient_tracker
CORS_ORIGINS = https://your-domain.railway.app
```

## 5. Deploy Frontend (Optional)
**Option A (Separate service):**
- New Railway service from `frontend/` directory
- Build: `npm install && npm run build`
- Start: `npm start`
- Set `REACT_APP_BACKEND_URL` to your backend Railway URL

**Option B (Same service):**
- Modify Procfile to serve static frontend
- More complex, see `RAILWAY_DEPLOYMENT.md` for details

## 6. Test
- Visit your backend URL: `https://your-backend.railway.app/api`
- Should see: `{"message":"Sentient Tracker API"}`
- Deploy frontend if separate, test auth and game creation

## Files Used by Railway
- `Procfile` - How to start your app ✅
- `railway.json` - Environment variable templates ✅
- `.railwayignore` - Files to skip during deployment ✅
- `requirements.txt` - Python dependencies ✅

## Costs
- Railway: ~$5-10/month (compute + MongoDB)
- OpenAI: ~$0.01-0.05 per game scan
- **Total: ~$15-20/month for small usage**

## Issues?
See full guide: `RAILWAY_DEPLOYMENT.md`
