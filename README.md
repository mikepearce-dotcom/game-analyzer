# Sentient Tracker - Game Community Pulse

A simple tool for game studios and community managers to track what Reddit is saying about a game and get AI-powered sentiment analysis.

## Features

- **Track Games**: Add games by name and subreddit
- **Reddit Scanning**: Fetches posts (up to 150) via Arctic Shift API (Reddit data mirror)
- **AI Sentiment Analysis**: GPT-4o-mini powered analysis of community sentiment
- **Dashboard Insights**:
  - Post volume (total + last 7 days)
  - Sentiment label (Positive/Mixed/Negative) with explanation
  - Top themes (5-10 bullet points)
  - Pain points (common complaints)
  - Community wins (common praise)
  - Source posts with Reddit links

## Tech Stack

- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB
- **AI**: OpenAI GPT-4o-mini
- **Reddit Data**: Arctic Shift API (public Reddit data mirror - avoids server IP blocks)

## Environment Variables

### Backend (`/backend/.env`)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
OPENAI_API_KEY=your-openai-api-key
```

### Frontend (`/frontend/.env`)
```
REACT_APP_BACKEND_URL=http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/games` | List all tracked games |
| POST | `/api/games` | Add new tracked game |
| GET | `/api/games/{id}` | Get single game |
| DELETE | `/api/games/{id}` | Delete game |
| POST | `/api/games/{id}/scan` | Run Reddit scan + AI analysis |
| GET | `/api/games/{id}/results` | Get scan results history |
| GET | `/api/games/{id}/latest-result` | Get latest scan result |

## Usage

1. Open the dashboard
2. Click "ADD GAME" to track a new game
3. Enter game name and subreddit (without r/, or paste full Reddit URL)
4. Optionally add keywords to watch for
5. Click "RUN SCAN" on the game page
6. View sentiment analysis, themes, pain points, and wins

## Data Source

This MVP uses **Arctic Shift** (arctic-shift.photon-reddit.com) as the Reddit data source:
- Avoids rate limiting issues from Reddit's official API blocking server IPs
- Fetches recent posts + top posts from last 7 days
- Combines and deduplicates results, capped at 150 posts
- 10-minute cache to avoid repeated API calls
- 30-second throttle between scans for same subreddit

## Notes

- AI analysis requires a valid OPENAI_API_KEY
- Source posts link to Reddit - full content is not stored
- Debug info available in expandable panel for troubleshooting

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install

# Start MongoDB
mongod

# Run backend
cd backend && python -m uvicorn server:app --reload

# Run frontend (new terminal)
cd frontend && npm start
```

### Deploy to Railway
See [RAILWAY_QUICK_START.md](RAILWAY_QUICK_START.md) for a 5-minute deployment guide.

Full deployment docs: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
