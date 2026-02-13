# Sentient Tracker - Product Requirements Document

## Original Problem Statement
Build a super basic MVP web app called Sentient Tracker (Game Community Pulse). A simple tool for game studios/community managers to track what Reddit is saying about a game and get an AI summary of common themes and sentiment.

## User Choices
- **LLM**: GPT-4o-mini (budget-friendly)
- **Reddit Data**: Arctic Shift API (Reddit data mirror - avoids server IP blocks)
- **Theme**: Dark cyberpunk gaming aesthetic
- **Authentication**: Both Google OAuth + Email/Password

## User Personas
1. **Game Studios** - Track community sentiment for their released/upcoming games
2. **Community Managers** - Monitor Reddit discussions and identify pain points
3. **Indie Developers** - Understand player feedback without manual Reddit browsing

## Core Requirements (Static)
- User authentication (Google OAuth + Email/Password)
- Add/edit/delete tracked games per user
- Fetch Reddit posts via Arctic Shift API
- AI-powered sentiment analysis (Positive/Mixed/Negative)
- Extract top themes, pain points, and community wins
- Display source posts with Reddit links
- Clean, mobile-first dark UI

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB + Motor (async)
- **AI**: OpenAI GPT-4o-mini via emergentintegrations
- **Reddit Data**: Arctic Shift API (arctic-shift.photon-reddit.com)
- **Auth**: Emergent Google OAuth + Custom Email/Password with sessions

## What's Been Implemented

### Phase 1 - MVP (Complete)
- [x] Dashboard with tracked games list
- [x] Add/edit/delete tracked games
- [x] Game detail page with subreddit info
- [x] Run Scan functionality (Reddit fetch + AI analysis)
- [x] Sentiment analysis display (label + summary)
- [x] Top themes extraction (5-10 bullets)
- [x] Pain points extraction (5 bullets)
- [x] Community wins extraction (5 bullets)
- [x] Source posts list with Reddit links
- [x] Loading states and error handling
- [x] Dark cyberpunk UI theme

### Phase 2 - Authentication & Multi-user (Complete)
- [x] Email/Password signup and login
- [x] Google OAuth via Emergent Auth
- [x] Session management with localStorage
- [x] Protected routes with auth checks
- [x] User-scoped games and scan results
- [x] Edit game functionality
- [x] User profile display in header
- [x] Logout functionality

### Phase 3 - High-Signal Scan Improvements (Complete - Feb 2026)
- [x] POST SELECTION with Arctic Shift API
  - Time window: 8d..36h (with fallbacks to 12h and 0h)
  - Quality filtering: removes posts with (num_comments==0 AND score<=1 AND short content)
  - Ranking algorithm: engagement = ln(score+1) + 2*ln(num_comments+1) + 0.35*text_bonus
  - Diversity caps: max 3 posts per author, max 20 no-comment posts
  - Recency: tries to include 20+ posts from last 3 days
- [x] COMMENT SAMPLING
  - Fetch comments for top 15 posts via /api/comments/search
  - Keep up to 10 comments per post (highest score/longest body)
  - Truncate comment body to 400 chars
  - Remove usernames from AI input
- [x] AI SUMMARIZATION with evidence
  - Pain points include 1-2 evidence links (Reddit permalinks)
  - Wins include 1-2 evidence links
  - Toxicity handling: AI ignores slurs/abuse
- [x] PERFORMANCE/SAFETY
  - 10-minute cache for posts and comments
  - 30-second throttle between scans per subreddit
  - 200ms delay between comment API calls
- [x] ERROR HANDLING
  - Clear messages for: no posts, timeout, rate limit
  - Debug panel shows all fetch details

## Database Schema

### Users Collection
- user_id: string (custom UUID)
- email: string (unique)
- name: string
- picture: string (optional, from Google)
- auth_provider: "email" | "google"
- password_hash: string (for email auth)
- created_at: datetime

### Tracked Games Collection
- id: string (UUID)
- user_id: string (owner)
- name: string
- subreddit: string
- keywords: string (optional)
- created_at: datetime

### Scan Results Collection
- id: string (UUID)
- tracked_game_id: string
- user_id: string (owner)
- post_count: int
- posts_last_7_days: int
- comments_sampled: int (NEW)
- sentiment_label: string
- sentiment_summary: string
- themes: array[string]
- pain_points: array[{text, evidence[]}] (UPDATED)
- wins: array[{text, evidence[]}] (UPDATED)
- source_posts: array
- debug_info: object (UPDATED with window_used, raw_post_count, etc.)
- cached: boolean
- created_at: datetime

## Key API Endpoints

### Auth
- POST /api/auth/signup - Email registration
- POST /api/auth/login - Email login
- POST /api/auth/google/session - Google OAuth exchange
- GET /api/auth/me - Get current user
- POST /api/auth/logout - Logout

### Games
- GET /api/games - List user's games
- POST /api/games - Create game
- GET /api/games/{id} - Get game
- PUT /api/games/{id} - Update game
- DELETE /api/games/{id} - Delete game

### Scans
- POST /api/games/{id}/scan - Run Reddit scan
- GET /api/games/{id}/results - Get scan history
- GET /api/games/{id}/latest-result - Get most recent scan
- GET /api/cache-status/{subreddit} - Check cache status

## Known Limitations
- Arctic Shift API has 100 post limit per request
- Arctic Shift data may be delayed vs real-time Reddit
- No password reset functionality yet
- No scan scheduling

## Prioritized Backlog

### P0 (Critical) - COMPLETED
- All P0 items completed

### P1 (Important)
- [ ] Password reset via email
- [ ] Scan history view (compare sentiment over time)
- [ ] Email verification

### P2 (Nice to Have)
- [ ] Multiple subreddits per game
- [ ] Scheduled automatic scans
- [ ] Email alerts for sentiment changes
- [ ] Discord/Twitter integration
- [ ] Export results to CSV/PDF
