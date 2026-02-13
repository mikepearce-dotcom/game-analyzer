from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import time
import hashlib
import secrets
import math
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== CONSTANTS ==============
SESSION_EXPIRY_DAYS = 7
CACHE_TTL_SECONDS = 600  # 10 minutes for posts and comments
THROTTLE_SECONDS = 30  # Minimum time between scans
COMMENT_FETCH_DELAY = 0.2  # 200ms delay between comment fetches
TOP_POSTS_FOR_COMMENTS = 15  # Fetch comments for top N posts
MAX_COMMENTS_PER_POST = 10  # Keep up to N comments per post
COMMENT_BODY_TRUNCATE = 400  # Max chars per comment body
POST_SELFTEXT_TRUNCATE = 500  # Max chars for selftext in AI input
MAX_POSTS_FINAL = 100  # Max posts after filtering (Arctic Shift API limit)
MAX_POSTS_PER_AUTHOR = 3  # Diversity cap
MAX_NO_COMMENT_POSTS = 20  # Diversity cap for 0-comment posts
MIN_RECENT_POSTS = 20  # Try to include at least N posts from last 3 days

# ============== IN-MEMORY CACHE ==============
reddit_cache: Dict[str, dict] = {}
comments_cache: Dict[str, dict] = {}  # Cache for comments by post_id

# ============== AUTH MODELS ==============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = ""
    auth_provider: str = "email"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

# ============== GAME MODELS ==============

class TrackedGame(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Owner of the game
    name: str
    subreddit: str
    keywords: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TrackedGameCreate(BaseModel):
    name: str
    subreddit: str
    keywords: Optional[str] = ""

class TrackedGameUpdate(BaseModel):
    name: Optional[str] = None
    subreddit: Optional[str] = None
    keywords: Optional[str] = None

class DebugInfo(BaseModel):
    subreddit_normalized: str = ""
    posts_url: str = ""
    posts_status: Optional[int] = None
    raw_post_count: int = 0
    after_quality_filter: int = 0
    final_post_count: int = 0
    comments_fetched_for: int = 0
    total_comments: int = 0
    window_used: str = ""  # e.g. "8d..36h" or "8d..12h" or "8d..0h"
    error_details: Optional[str] = None
    data_source: str = "arctic-shift"

class ScanResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tracked_game_id: str
    user_id: str  # Owner of the scan
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    post_count: int = 0
    posts_last_7_days: int = 0
    comments_sampled: int = 0  # New: count of comment samples included
    sentiment_label: str = "Unknown"
    sentiment_summary: str = ""
    themes: List[str] = []
    pain_points: List[dict] = []  # Changed: now includes evidence links
    wins: List[dict] = []  # Changed: now includes evidence links
    source_posts: List[dict] = []
    error: Optional[str] = None
    cached: bool = False
    debug_info: Optional[DebugInfo] = None

# ============== PASSWORD HASHING ==============

def hash_password(password: str) -> str:
    """Hash password with salt using SHA-256"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, hashed = stored_hash.split(":")
        return hashlib.sha256((password + salt).encode()).hexdigest() == hashed
    except (ValueError, AttributeError):
        return False

# ============== AUTH HELPERS ==============

async def get_current_user(request: Request) -> User:
    """Extract and validate user from session token (cookie or header)"""
    # Try cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry with timezone handling
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Find user
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Handle datetime
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return User(**user_doc)

async def create_session(user_id: str, response: Response) -> str:
    """Create a new session for a user"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
    
    session = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.insert_one(session)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=SESSION_EXPIRY_DAYS * 24 * 60 * 60
    )
    
    return session_token

# ============== SUBREDDIT NORMALIZATION ==============

def normalize_subreddit(input_str: str) -> str:
    if not input_str:
        return ""
    normalized = input_str.strip()
    url_pattern = r'(?:https?://)?(?:www\.)?reddit\.com/r/([^/\s?]+)'
    url_match = re.match(url_pattern, normalized, re.IGNORECASE)
    if url_match:
        return url_match.group(1)
    if normalized.lower().startswith('r/'):
        normalized = normalized[2:]
    normalized = normalized.rstrip('/')
    return normalized

# ============== ARCTIC SHIFT FETCHING ==============

ARCTIC_SHIFT_BASE = "https://arctic-shift.photon-reddit.com"

async def fetch_arctic_shift_posts(subreddit: str, after: str, before: str) -> tuple[List[dict], Optional[int], Optional[str]]:
    """
    Fetch posts from Arctic Shift API with relative date formats.
    after/before use relative formats like "8d", "36h", "12h", "0h"
    Arctic Shift API has a limit of 100 posts per request.
    """
    fields = "id,title,selftext,created_utc,score,num_comments,author"
    url = f"{ARCTIC_SHIFT_BASE}/api/posts/search?subreddit={subreddit}&after={after}&before={before}&sort=desc&limit=100&fields={fields}"
    
    headers = {
        "User-Agent": "SentientTrackerMVP/1.0",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(url, headers=headers, follow_redirects=True)
            status = response.status_code
            
            # Parse retry-after header if rate limited
            retry_after = response.headers.get("Retry-After")
            
            if status == 404:
                return [], status, "Subreddit not found. Check spelling."
            elif status == 429:
                retry_msg = f" (retry after {retry_after}s)" if retry_after else ""
                return [], status, f"Rate limited{retry_msg}. Try again later."
            elif status == 403:
                return [], status, "Access forbidden."
            elif status == 400:
                try:
                    error_data = response.json()
                    logger.warning(f"Arctic Shift 400 error: {error_data.get('error', 'Unknown')}")
                except (json.JSONDecodeError, Exception):
                    pass
                return [], status, "Bad request. Check subreddit name."
            elif status == 502 or status == 503:
                return [], status, "Arctic Shift service temporarily unavailable. Try again later."
            elif status == 504:
                return [], status, "Request timed out. Try reducing the time window."
            elif status != 200:
                return [], status, f"Arctic Shift returned HTTP {status}."
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                return [], status, "Invalid JSON response from Arctic Shift."
            
            if not isinstance(data, dict):
                return [], status, "Unexpected response format."
            
            posts_data = data.get("data", [])
            if not isinstance(posts_data, list):
                return [], status, "Unexpected response. 'data' is not an array."
            
            posts = []
            for post_data in posts_data:
                if not isinstance(post_data, dict):
                    continue
                
                post_id = post_data.get("id", "")
                if not post_id:
                    continue
                
                # Construct permalink from post ID
                permalink = f"https://www.reddit.com/comments/{post_id}"
                
                posts.append({
                    "id": post_id,
                    "title": post_data.get("title", "") or "",
                    "selftext": post_data.get("selftext", "") or "",
                    "score": post_data.get("score", 0) or 0,
                    "created_utc": post_data.get("created_utc", 0) or 0,
                    "num_comments": post_data.get("num_comments", 0) or 0,
                    "author": post_data.get("author", "") or "",
                    "permalink": permalink
                })
            
            return posts, status, None
            
    except httpx.TimeoutException:
        return [], None, "Request timed out. Try again or reduce time window."
    except httpx.ConnectError:
        return [], None, "Could not connect to Arctic Shift. Check connection."
    except Exception as e:
        logger.error(f"Error fetching Arctic Shift posts: {e}")
        return [], None, f"Network error: {str(e)}"


async def fetch_arctic_shift_comments(post_id: str) -> tuple[List[dict], Optional[str]]:
    """
    Fetch top-level comments for a post from Arctic Shift API.
    """
    # Check cache first
    current_time = time.time()
    cache_key = f"comments_{post_id}"
    
    if cache_key in comments_cache:
        cache_entry = comments_cache[cache_key]
        if current_time - cache_entry["timestamp"] < CACHE_TTL_SECONDS:
            return cache_entry["data"], None
    
    fields = "id,body,created_utc,score,author,link_id,parent_id"
    url = f"{ARCTIC_SHIFT_BASE}/api/comments/search?link_id=t3_{post_id}&sort=desc&limit=100&fields={fields}"
    
    headers = {
        "User-Agent": "SentientTrackerMVP/1.0",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.get(url, headers=headers, follow_redirects=True)
            
            if response.status_code != 200:
                return [], f"Failed to fetch comments (HTTP {response.status_code})"
            
            data = response.json()
            comments_data = data.get("data", [])
            
            # Filter to top-level comments only (parent_id starts with t3_ or is empty)
            comments = []
            for c in comments_data:
                if not isinstance(c, dict):
                    continue
                
                parent_id = c.get("parent_id", "")
                # Top-level comments have parent_id = t3_<post_id> (the post itself)
                # or sometimes no parent_id at all
                if parent_id and not parent_id.startswith("t3_"):
                    continue  # Skip replies to other comments
                
                body = c.get("body", "") or ""
                # Skip deleted/removed comments
                if body in ["[deleted]", "[removed]", ""]:
                    continue
                
                comments.append({
                    "id": c.get("id", ""),
                    "body": body,
                    "score": c.get("score", 0) or 0,
                    "created_utc": c.get("created_utc", 0) or 0,
                    "author": c.get("author", "") or ""
                })
            
            # Cache the results
            comments_cache[cache_key] = {
                "data": comments,
                "timestamp": current_time
            }
            
            return comments, None
            
    except Exception as e:
        logger.error(f"Error fetching comments for post {post_id}: {e}")
        return [], str(e)


def apply_quality_filter(posts: List[dict]) -> List[dict]:
    """
    Drop low-quality posts:
    - num_comments == 0 AND score <= 1 AND (selftext empty OR < 80 chars) AND title < 25 chars
    """
    filtered = []
    for post in posts:
        num_comments = post.get("num_comments", 0)
        score = post.get("score", 0)
        selftext = post.get("selftext", "") or ""
        title = post.get("title", "") or ""
        
        # Quality filter condition
        is_low_quality = (
            num_comments == 0 and
            score <= 1 and
            (len(selftext) == 0 or len(selftext) < 80) and
            len(title) < 25
        )
        
        if not is_low_quality:
            filtered.append(post)
    
    return filtered


def calculate_post_rank(post: dict) -> float:
    """
    Calculate ranking score for a post:
    engagement = ln(score+1) + 2*ln(num_comments+1)
    text_bonus = min(len(selftext)/500, 1)
    total_rank = engagement + 0.35*text_bonus
    """
    score = max(0, post.get("score", 0))
    num_comments = max(0, post.get("num_comments", 0))
    selftext = post.get("selftext", "") or ""
    
    engagement = math.log(score + 1) + 2 * math.log(num_comments + 1)
    text_bonus = min(len(selftext) / 500, 1.0)
    total_rank = engagement + 0.35 * text_bonus
    
    return total_rank


def apply_diversity_and_recency(posts: List[dict]) -> List[dict]:
    """
    Apply diversity caps and ensure recency:
    - Max 3 posts per author
    - Max 25 posts with num_comments == 0
    - Try to include at least 30 posts from last 3 days
    """
    # Sort by rank
    for post in posts:
        post["_rank"] = calculate_post_rank(post)
    
    posts_sorted = sorted(posts, key=lambda p: p["_rank"], reverse=True)
    
    # Track diversity constraints
    author_count: Dict[str, int] = {}
    no_comment_count = 0
    
    # Current time for recency check
    now = time.time()
    three_days_ago = now - (3 * 24 * 60 * 60)
    
    # First pass: select posts while respecting diversity caps
    selected = []
    recent_in_selection = 0
    deferred_recent = []  # Recent posts that were skipped due to caps
    
    for post in posts_sorted:
        if len(selected) >= MAX_POSTS_FINAL:
            break
        
        author = post.get("author", "unknown")
        num_comments = post.get("num_comments", 0)
        created_utc = post.get("created_utc", 0)
        is_recent = created_utc > three_days_ago
        
        # Check diversity caps
        author_posts = author_count.get(author, 0)
        if author_posts >= MAX_POSTS_PER_AUTHOR:
            if is_recent:
                deferred_recent.append(post)
            continue
        
        if num_comments == 0 and no_comment_count >= MAX_NO_COMMENT_POSTS:
            if is_recent:
                deferred_recent.append(post)
            continue
        
        # Add post
        selected.append(post)
        author_count[author] = author_posts + 1
        if num_comments == 0:
            no_comment_count += 1
        if is_recent:
            recent_in_selection += 1
    
    # Second pass: try to ensure MIN_RECENT_POSTS from last 3 days
    if recent_in_selection < MIN_RECENT_POSTS and deferred_recent:
        # Sort deferred by recency
        deferred_recent.sort(key=lambda p: p.get("created_utc", 0), reverse=True)
        
        for post in deferred_recent:
            if recent_in_selection >= MIN_RECENT_POSTS:
                break
            if len(selected) >= MAX_POSTS_FINAL:
                # Replace lowest-ranked non-recent post
                for i in range(len(selected) - 1, -1, -1):
                    existing = selected[i]
                    if existing.get("created_utc", 0) <= three_days_ago:
                        selected[i] = post
                        recent_in_selection += 1
                        break
            else:
                selected.append(post)
                recent_in_selection += 1
    
    # Clean up temporary rank field
    for post in selected:
        post.pop("_rank", None)
    
    return selected[:MAX_POSTS_FINAL]


def select_best_comments(comments: List[dict], max_count: int = MAX_COMMENTS_PER_POST) -> List[dict]:
    """
    Select best comments, preferring higher score, then longer body, then more recent.
    Truncate body and remove usernames.
    """
    # Sort by score (desc), then body length (desc), then created_utc (desc)
    sorted_comments = sorted(
        comments,
        key=lambda c: (c.get("score", 0), len(c.get("body", "")), c.get("created_utc", 0)),
        reverse=True
    )
    
    selected = []
    for c in sorted_comments[:max_count]:
        body = c.get("body", "")
        # Truncate body
        if len(body) > COMMENT_BODY_TRUNCATE:
            body = body[:COMMENT_BODY_TRUNCATE] + "..."
        
        # Remove specific usernames (replace /u/username patterns)
        import re
        body = re.sub(r'/?u/[A-Za-z0-9_-]+', '[user]', body)
        
        selected.append({
            "id": c.get("id", ""),
            "body": body,
            "score": c.get("score", 0)
        })
    
    return selected


async def fetch_reddit_posts(subreddit: str) -> tuple[List[dict], List[dict], Optional[str], bool, DebugInfo]:
    """
    Fetch and filter Reddit posts from Arctic Shift with the new high-signal algorithm.
    Returns: (posts, post_comments, error, used_cache, debug_info)
    post_comments is a list of {post_id, comments: [...]} for top posts
    """
    normalized = normalize_subreddit(subreddit)
    
    if not normalized:
        debug = DebugInfo(subreddit_normalized="", error_details="Empty subreddit after normalization")
        return [], [], "Invalid subreddit name.", False, debug
    
    debug = DebugInfo(
        subreddit_normalized=normalized,
        data_source="arctic-shift"
    )
    
    current_time = time.time()
    subreddit_lower = normalized.lower()
    
    # Check posts cache first
    if subreddit_lower in reddit_cache:
        cache_entry = reddit_cache[subreddit_lower]
        cache_age = current_time - cache_entry["timestamp"]
        
        if cache_age < CACHE_TTL_SECONDS:
            logger.info(f"Using cached data for r/{normalized} (age: {cache_age:.0f}s)")
            debug.error_details = f"Using cached data (age: {int(cache_age)}s)"
            cached_data = cache_entry["data"]
            return cached_data["posts"], cached_data.get("comments", []), None, True, debug
    
    # Try different time windows: 8d..36h, then 8d..12h, then 8d..0h
    windows = [
        ("8d", "36h"),
        ("8d", "12h"),
        ("8d", "0h")
    ]
    
    posts = []
    used_window = ""
    
    for after, before in windows:
        window_str = f"{after}..{before}"
        url = f"{ARCTIC_SHIFT_BASE}/api/posts/search?subreddit={normalized}&after={after}&before={before}&sort=desc&limit=500"
        debug.posts_url = url
        
        fetched_posts, status, error = await fetch_arctic_shift_posts(normalized, after, before)
        debug.posts_status = status
        
        if error:
            debug.error_details = error
            # If it's a rate limit or server error, don't try other windows
            if status in [429, 502, 503, 504]:
                return [], [], error, False, debug
            continue
        
        debug.raw_post_count = len(fetched_posts)
        
        # Apply quality filter
        filtered_posts = apply_quality_filter(fetched_posts)
        debug.after_quality_filter = len(filtered_posts)
        
        # Check if we have enough posts
        if len(filtered_posts) >= 150:
            posts = filtered_posts
            used_window = window_str
            break
        elif len(filtered_posts) > len(posts):
            posts = filtered_posts
            used_window = window_str
            # Continue to try wider windows if we don't have enough
    
    debug.window_used = used_window
    
    if not posts:
        debug.error_details = "No posts found in any time window"
        return [], [], f"No posts found for r/{normalized}. The subreddit may be empty, private, or the name may be incorrect.", False, debug
    
    # Apply diversity and recency rules
    final_posts = apply_diversity_and_recency(posts)
    debug.final_post_count = len(final_posts)
    
    logger.info(f"Fetched {len(final_posts)} posts for r/{normalized} (window: {used_window})")
    
    # Fetch comments for top 15 posts
    post_comments = []
    
    # Re-rank to get top posts for comment fetching
    ranked_for_comments = sorted(final_posts, key=calculate_post_rank, reverse=True)[:TOP_POSTS_FOR_COMMENTS]
    
    total_comments_fetched = 0
    for post in ranked_for_comments:
        post_id = post.get("id")
        if not post_id:
            continue
        
        comments, comment_error = await fetch_arctic_shift_comments(post_id)
        
        if comments:
            best_comments = select_best_comments(comments)
            if best_comments:
                post_comments.append({
                    "post_id": post_id,
                    "post_title": post.get("title", ""),
                    "comments": best_comments
                })
                total_comments_fetched += len(best_comments)
        
        # Small delay between requests to be nice to the API
        await asyncio.sleep(COMMENT_FETCH_DELAY)
    
    debug.comments_fetched_for = len(post_comments)
    debug.total_comments = total_comments_fetched
    
    # Cache the results
    reddit_cache[subreddit_lower] = {
        "data": {
            "posts": final_posts,
            "comments": post_comments
        },
        "timestamp": current_time
    }
    
    return final_posts, post_comments, None, False, debug

# ============== AI ANALYSIS ==============

async def analyze_posts_with_ai(posts: List[dict], post_comments: List[dict], game_name: str, keywords: str = "") -> dict:
    from openai import OpenAI
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {
            "sentiment_label": "Unknown",
            "sentiment_summary": "AI analysis unavailable - no API key configured",
            "themes": [],
            "pain_points": [],
            "wins": []
        }
    
    # Build post summaries with truncated selftext
    post_summaries = []
    post_id_to_link = {}  # Map post IDs to their Reddit links for evidence
    
    for post in posts[:MAX_POSTS_FINAL]:
        post_id = post.get("id", "")
        title = post.get("title", "")
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        selftext = (post.get("selftext", "") or "")[:POST_SELFTEXT_TRUNCATE]
        
        # Store link for evidence
        post_id_to_link[post_id] = f"https://www.reddit.com/comments/{post_id}/"
        
        summary = f"[POST:{post_id}] [{score} pts, {num_comments} comments] {title}"
        if selftext and selftext not in ["[removed]", "[deleted]"]:
            selftext_clean = selftext.replace('\n', ' ').strip()
            summary += f"\n  Content: {selftext_clean}"
        post_summaries.append(summary)
    
    posts_text = "\n".join(post_summaries)
    
    # Build comment samples text
    comments_text = ""
    total_comments = 0
    if post_comments:
        comment_sections = []
        for pc in post_comments:
            post_id = pc.get("post_id", "")
            post_title = pc.get("post_title", "")[:100]
            comments = pc.get("comments", [])
            
            if comments:
                comment_lines = [f"\n--- Comments on [POST:{post_id}] {post_title} ---"]
                for c in comments:
                    body = c.get("body", "")
                    comment_score = c.get("score", 0)
                    comment_lines.append(f"  [{comment_score} pts] {body}")
                    total_comments += 1
                comment_sections.append("\n".join(comment_lines))
        
        if comment_sections:
            comments_text = "\n\nCOMMENT SAMPLES FROM TOP POSTS:\n" + "\n".join(comment_sections)
    
    keyword_note = f"\nKeywords to watch for: {keywords}" if keywords else ""
    
    prompt = f"""Analyze these {len(posts)} Reddit posts (and {total_comments} comment samples) about the game "{game_name}" and provide a community sentiment analysis.

IMPORTANT INSTRUCTIONS:
- Ignore any slurs, toxic language, or personal attacks in your analysis. Summarize themes professionally without quoting toxic content.
- For pain_points and wins, include 1-2 evidence links using the POST IDs provided in square brackets.
- The evidence format should reference posts like: "https://www.reddit.com/comments/POST_ID/"

REQUIRED OUTPUT (JSON format):
1. sentiment_label: "Positive", "Mixed", or "Negative"
2. sentiment_summary: 2-3 sentences explaining the overall community mood
3. themes: Array of 5-10 common discussion topics (strings)
4. pain_points: Array of exactly 5 objects, each with:
   - "text": the complaint/frustration description
   - "evidence": array of 1-2 Reddit links (use https://www.reddit.com/comments/POST_ID/ format)
5. wins: Array of exactly 5 objects, each with:
   - "text": the praise/positive aspect description  
   - "evidence": array of 1-2 Reddit links (use https://www.reddit.com/comments/POST_ID/ format)
{keyword_note}

Reddit Posts ({len(posts)} total):
{posts_text}
{comments_text}

Respond ONLY with valid JSON in this exact format:
{{
    "sentiment_label": "Positive" or "Mixed" or "Negative",
    "sentiment_summary": "2-3 sentence explanation of community mood",
    "themes": ["theme1", "theme2", ...],
    "pain_points": [
        {{"text": "complaint description", "evidence": ["https://www.reddit.com/comments/abc123/", "https://www.reddit.com/comments/def456/"]}},
        ...
    ],
    "wins": [
        {{"text": "praise description", "evidence": ["https://www.reddit.com/comments/xyz789/"]}},
        ...
    ]
}}"""

    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert gaming community analyst. Analyze Reddit posts and comments to extract sentiment, themes, complaints, and praise. Always respond with valid JSON only, no markdown. Be professional and ignore toxic content."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        
        # Validate and normalize pain_points and wins
        for field in ["pain_points", "wins"]:
            if field not in result or not isinstance(result[field], list):
                result[field] = []
            else:
                # Normalize: handle both string format (old) and dict format (new)
                normalized = []
                for item in result[field]:
                    if isinstance(item, str):
                        normalized.append({"text": item, "evidence": []})
                    elif isinstance(item, dict):
                        normalized.append({
                            "text": item.get("text", str(item)),
                            "evidence": item.get("evidence", [])
                        })
                result[field] = normalized[:5]  # Ensure max 5
        
        # Ensure themes is a list
        if "themes" not in result or not isinstance(result["themes"], list):
            result["themes"] = []
        
        # Ensure sentiment fields
        if "sentiment_label" not in result:
            result["sentiment_label"] = "Unknown"
        if "sentiment_summary" not in result:
            result["sentiment_summary"] = ""
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        return {
            "sentiment_label": "Unknown",
            "sentiment_summary": "AI analysis completed but response parsing failed. Try scanning again.",
            "themes": [],
            "pain_points": [],
            "wins": []
        }
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return {
            "sentiment_label": "Unknown",
            "sentiment_summary": f"AI analysis failed: {str(e)}",
            "themes": [],
            "pain_points": [],
            "wins": []
        }

# ============== THROTTLE CHECK ==============

last_scan_times: Dict[str, float] = {}

def check_throttle(subreddit: str) -> tuple[bool, int]:
    normalized = normalize_subreddit(subreddit).lower()
    current_time = time.time()
    
    if normalized in last_scan_times:
        elapsed = current_time - last_scan_times[normalized]
        if elapsed < THROTTLE_SECONDS:
            return True, int(THROTTLE_SECONDS - elapsed)
    
    return False, 0

def update_scan_time(subreddit: str):
    normalized = normalize_subreddit(subreddit).lower()
    last_scan_times[normalized] = time.time()

# ============== AUTH ROUTES ==============

@api_router.post("/auth/signup")
async def email_signup(request: EmailSignupRequest, response: Response):
    """Sign up with email and password"""
    # Check if email already exists
    existing = await db.users.find_one({"email": request.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    password_hash = hash_password(request.password)
    
    user_doc = {
        "user_id": user_id,
        "email": request.email,
        "name": request.name,
        "picture": "",
        "auth_provider": "email",
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create session
    session_token = await create_session(user_id, response)
    
    return {
        "user_id": user_id,
        "email": request.email,
        "name": request.name,
        "session_token": session_token
    }

@api_router.post("/auth/login")
async def email_login(request: EmailLoginRequest, response: Response):
    """Login with email and password"""
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if user_doc.get("auth_provider") != "email":
        raise HTTPException(status_code=400, detail="Please use Google to sign in")
    
    if not verify_password(request.password, user_doc.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    session_token = await create_session(user_doc["user_id"], response)
    
    return {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "name": user_doc["name"],
        "session_token": session_token
    }

@api_router.get("/auth/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "auth_provider": user.auth_provider
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    
    return {"message": "Logged out successfully"}

# ============== GAME ROUTES (PROTECTED) ==============

@api_router.get("/")
async def root():
    return {"message": "Sentient Tracker API"}

@api_router.get("/games", response_model=List[TrackedGame])
async def get_games(user: User = Depends(get_current_user)):
    """Get all tracked games for the current user"""
    games = await db.tracked_games.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    
    for game in games:
        if isinstance(game.get('created_at'), str):
            game['created_at'] = datetime.fromisoformat(game['created_at'])
    
    return games

@api_router.post("/games", response_model=TrackedGame)
async def create_game(input: TrackedGameCreate, user: User = Depends(get_current_user)):
    """Create a new tracked game"""
    normalized_sub = normalize_subreddit(input.subreddit)
    game = TrackedGame(
        user_id=user.user_id,
        name=input.name,
        subreddit=normalized_sub,
        keywords=input.keywords
    )
    doc = game.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.tracked_games.insert_one(doc)
    return game

@api_router.get("/games/{game_id}", response_model=TrackedGame)
async def get_game(game_id: str, user: User = Depends(get_current_user)):
    """Get a single tracked game"""
    game = await db.tracked_games.find_one(
        {"id": game_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if isinstance(game.get('created_at'), str):
        game['created_at'] = datetime.fromisoformat(game['created_at'])
    return game

@api_router.put("/games/{game_id}", response_model=TrackedGame)
async def update_game(game_id: str, input: TrackedGameUpdate, user: User = Depends(get_current_user)):
    """Update a tracked game"""
    game = await db.tracked_games.find_one(
        {"id": game_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Build update dict
    update_data = {}
    if input.name is not None:
        update_data["name"] = input.name
    if input.subreddit is not None:
        update_data["subreddit"] = normalize_subreddit(input.subreddit)
    if input.keywords is not None:
        update_data["keywords"] = input.keywords
    
    if update_data:
        await db.tracked_games.update_one(
            {"id": game_id, "user_id": user.user_id},
            {"$set": update_data}
        )
    
    # Fetch updated game
    updated_game = await db.tracked_games.find_one(
        {"id": game_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if isinstance(updated_game.get('created_at'), str):
        updated_game['created_at'] = datetime.fromisoformat(updated_game['created_at'])
    
    return updated_game

@api_router.delete("/games/{game_id}")
async def delete_game(game_id: str, user: User = Depends(get_current_user)):
    """Delete a tracked game and its scan results"""
    result = await db.tracked_games.delete_one(
        {"id": game_id, "user_id": user.user_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Game not found")
    await db.scan_results.delete_many({"tracked_game_id": game_id, "user_id": user.user_id})
    return {"message": "Game deleted successfully"}

# ============== SCAN ROUTES (PROTECTED) ==============

@api_router.post("/games/{game_id}/scan", response_model=ScanResult)
async def run_scan(game_id: str, user: User = Depends(get_current_user)):
    """Run a Reddit scan for a tracked game"""
    game = await db.tracked_games.find_one(
        {"id": game_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    subreddit = game['subreddit']
    
    should_throttle, seconds_remaining = check_throttle(subreddit)
    if should_throttle:
        debug = DebugInfo(
            subreddit_normalized=normalize_subreddit(subreddit),
            error_details=f"Throttled: {seconds_remaining}s remaining",
            data_source="arctic-shift"
        )
        return ScanResult(
            tracked_game_id=game_id,
            user_id=user.user_id,
            error=f"Please wait {seconds_remaining} seconds before scanning r/{subreddit} again.",
            debug_info=debug
        )
    
    posts, post_comments, error, used_cache, debug = await fetch_reddit_posts(subreddit)
    update_scan_time(subreddit)
    
    if error:
        scan_result = ScanResult(
            tracked_game_id=game_id,
            user_id=user.user_id,
            error=error,
            debug_info=debug
        )
        doc = scan_result.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.scan_results.insert_one(doc)
        return scan_result
    
    if len(posts) == 0:
        debug.error_details = "No posts found for this subreddit"
        scan_result = ScanResult(
            tracked_game_id=game_id,
            user_id=user.user_id,
            error=f"No posts found for r/{subreddit}. The subreddit may be empty, private, or the name may be incorrect.",
            debug_info=debug
        )
        doc = scan_result.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.scan_results.insert_one(doc)
        return scan_result
    
    now = datetime.now(timezone.utc).timestamp()
    seven_days_ago = now - (7 * 24 * 60 * 60)
    posts_last_7_days = sum(1 for p in posts if p.get('created_utc', 0) > seven_days_ago)
    
    # Count total comments sampled
    total_comments_sampled = sum(len(pc.get("comments", [])) for pc in post_comments)
    
    ai_result = await analyze_posts_with_ai(posts, post_comments, game['name'], game.get('keywords', ''))
    
    source_posts = [
        {
            "id": p.get('id', ''),
            "title": p.get('title', ''),
            "score": p.get('score', 0),
            "created_utc": p.get('created_utc', 0),
            "permalink": p.get('permalink', f"https://www.reddit.com/comments/{p.get('id', '')}/"),
            "num_comments": p.get('num_comments', 0),
            "selftext_preview": (p.get('selftext', '') or '')[:200]
        }
        for p in posts
    ]
    
    scan_result = ScanResult(
        tracked_game_id=game_id,
        user_id=user.user_id,
        post_count=len(posts),
        posts_last_7_days=posts_last_7_days,
        comments_sampled=total_comments_sampled,
        sentiment_label=ai_result.get('sentiment_label', 'Unknown'),
        sentiment_summary=ai_result.get('sentiment_summary', ''),
        themes=ai_result.get('themes', []),
        pain_points=ai_result.get('pain_points', []),
        wins=ai_result.get('wins', []),
        source_posts=source_posts,
        cached=used_cache,
        debug_info=debug
    )
    
    doc = scan_result.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.scan_results.insert_one(doc)
    
    return scan_result

@api_router.get("/games/{game_id}/results", response_model=List[ScanResult])
async def get_scan_results(game_id: str, limit: int = 10, user: User = Depends(get_current_user)):
    """Get scan results for a tracked game"""
    results = await db.scan_results.find(
        {"tracked_game_id": game_id, "user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    for result in results:
        if isinstance(result.get('created_at'), str):
            result['created_at'] = datetime.fromisoformat(result['created_at'])
    
    return results

@api_router.get("/games/{game_id}/latest-result", response_model=Optional[ScanResult])
async def get_latest_scan_result(game_id: str, user: User = Depends(get_current_user)):
    """Get the most recent scan result"""
    result = await db.scan_results.find_one(
        {"tracked_game_id": game_id, "user_id": user.user_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if result and isinstance(result.get('created_at'), str):
        result['created_at'] = datetime.fromisoformat(result['created_at'])
    
    return result

@api_router.get("/cache-status/{subreddit}")
async def get_cache_status(subreddit: str):
    normalized = normalize_subreddit(subreddit).lower()
    current_time = time.time()
    
    if normalized in reddit_cache:
        cache_entry = reddit_cache[normalized]
        cache_age = current_time - cache_entry["timestamp"]
        is_valid = cache_age < CACHE_TTL_SECONDS
        return {
            "cached": True,
            "valid": is_valid,
            "age_seconds": int(cache_age),
            "expires_in": max(0, int(CACHE_TTL_SECONDS - cache_age)),
            "post_count": len(cache_entry["data"])
        }
    
    return {"cached": False, "valid": False}

# ============== ACCOUNT MANAGEMENT ==============

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@api_router.put("/account/profile")
async def update_profile(request: UpdateProfileRequest, user: User = Depends(get_current_user)):
    """Update user profile"""
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": update_data}
    )
    
    # Return updated user
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return user_doc

@api_router.post("/account/change-password")
async def change_password(request: ChangePasswordRequest, user: User = Depends(get_current_user)):
    """Change password for email-authenticated users"""
    # Get user with password hash
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_doc.get("auth_provider") != "email":
        raise HTTPException(status_code=400, detail="Password change only available for email accounts")
    
    # Verify current password
    if not verify_password(request.current_password, user_doc.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    # Update password
    new_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"password_hash": new_hash}}
    )
    
    return {"message": "Password changed successfully"}

@api_router.get("/account/sessions")
async def get_sessions(user: User = Depends(get_current_user)):
    """Get all active sessions for the current user"""
    sessions = await db.user_sessions.find(
        {"user_id": user.user_id},
        {"_id": 0, "session_token": 0}  # Don't expose tokens
    ).to_list(100)
    
    # Add a simple ID for each session
    for i, session in enumerate(sessions):
        session["session_id"] = i + 1
        if isinstance(session.get("created_at"), str):
            session["created_at"] = datetime.fromisoformat(session["created_at"])
        if isinstance(session.get("expires_at"), str):
            session["expires_at"] = datetime.fromisoformat(session["expires_at"])
    
    return sessions

@api_router.delete("/account/sessions")
async def revoke_other_sessions(request: Request, user: User = Depends(get_current_user)):
    """Revoke all sessions except the current one"""
    current_token = request.cookies.get("session_token")
    if not current_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            current_token = auth_header[7:]
    
    # Delete all sessions except current
    result = await db.user_sessions.delete_many({
        "user_id": user.user_id,
        "session_token": {"$ne": current_token}
    })
    
    return {"message": f"Revoked {result.deleted_count} other sessions"}

@api_router.delete("/account")
async def delete_account(user: User = Depends(get_current_user)):
    """Delete user account and all associated data"""
    user_id = user.user_id
    
    # Delete all user data
    await db.scan_results.delete_many({"user_id": user_id})
    await db.tracked_games.delete_many({"user_id": user_id})
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.users.delete_one({"user_id": user_id})
    
    return {"message": "Account deleted successfully"}

@api_router.get("/account/stats")
async def get_account_stats(user: User = Depends(get_current_user)):
    """Get account statistics"""
    games_count = await db.tracked_games.count_documents({"user_id": user.user_id})
    scans_count = await db.scan_results.count_documents({"user_id": user.user_id})
    
    return {
        "games_count": games_count,
        "scans_count": scans_count
    }

# ============== SCAN HISTORY WITH TREND DATA ==============

@api_router.get("/games/{game_id}/history")
async def get_scan_history(game_id: str, limit: int = 20, user: User = Depends(get_current_user)):
    """Get scan history with trend data for charts"""
    # Verify game belongs to user
    game = await db.tracked_games.find_one(
        {"id": game_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get historical scans (exclude source_posts for lighter response)
    results = await db.scan_results.find(
        {"tracked_game_id": game_id, "user_id": user.user_id, "error": None},
        {"_id": 0, "source_posts": 0}
    ).sort("created_at", -1).to_list(limit)
    
    # Convert sentiment to numeric for charting
    sentiment_map = {"Positive": 1, "Mixed": 0, "Negative": -1, "Unknown": 0}
    
    trend_data = []
    for result in reversed(results):  # Oldest first for chart
        if isinstance(result.get('created_at'), str):
            result['created_at'] = datetime.fromisoformat(result['created_at'])
        
        trend_data.append({
            "id": result.get("id"),
            "created_at": result.get("created_at").isoformat() if result.get("created_at") else None,
            "sentiment_label": result.get("sentiment_label", "Unknown"),
            "sentiment_value": sentiment_map.get(result.get("sentiment_label", "Unknown"), 0),
            "post_count": result.get("post_count", 0),
            "comments_sampled": result.get("comments_sampled", 0),
            "themes_count": len(result.get("themes", [])),
            "pain_points_count": len(result.get("pain_points", [])),
            "wins_count": len(result.get("wins", []))
        })
    
    return {
        "game": game,
        "trend_data": trend_data,
        "total_scans": len(trend_data)
    }

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
