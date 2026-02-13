# Emergent Dependency Analysis & Removal Guide

## Overview
This application has **3 main Emergent dependencies** that need to be removed or replaced. Below is a complete breakdown.

---

## 1. **BACKEND DEPENDENCIES**

### A. `emergentintegrations` Python Package
**Location:** [backend/requirements.txt](backend/requirements.txt#L20)  
**Used in:** [backend/server.py](backend/server.py#L697-L704)  
**Purpose:** AI analysis using GPT-4o-mini via Emergent's LLM API

**What it does:**
```python
from emergentintegrations.llm.chat import LlmChat, UserMessage

chat = LlmChat(
    api_key=api_key,  # EMERGENT_LLM_KEY
    session_id=f"scan-{uuid.uuid4()}",
    system_message="..."
).with_model("openai", "gpt-4o-mini")

response = await chat.send_message(user_message)
```

**Environment Variable Required:** `EMERGENT_LLM_KEY`

**Replacement Option:** 
- Use **OpenAI API directly** with `openai` Python package
- You'll need your own OpenAI API key (sign up at openai.com)
- Similar cost (GPT-4o-mini is cheap)

**Files to Modify:**
- [backend/requirements.txt](backend/requirements.txt) - Remove `emergentintegrations==0.1.0`, add `openai>=1.0.0`
- [backend/server.py](backend/server.py#L697-L750) - Replace `LlmChat` with OpenAI client
- [backend/.env](backend/.env) - Replace `EMERGENT_LLM_KEY` with `OPENAI_API_KEY`

---

### B. Emergent Google OAuth Backend
**Location:** [backend/server.py](backend/server.py#L940-L970)  
**Purpose:** Validate Google OAuth sessions via Emergent's auth service

**What it does:**
```python
auth_response = await http_client.get(
    "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
    headers={"X-Session-ID": request.session_id}
)
```

**Replacement Option:**
- Use **Google APIs directly** to verify OAuth tokens
- Install: `google-auth` (already in requirements.txt)
- You'll need Google OAuth credentials (already shown in code - frontend must provide)

**Files to Modify:**
- [backend/server.py](backend/server.py#L940-L970) - Replace Emergent auth endpoint with Google token verification

---

## 2. **FRONTEND DEPENDENCIES**

### A. Emergent Google OAuth Frontend
**Location:** [frontend/src/App.js](frontend/src/App.js#L190)  
**Purpose:** Redirect user to Emergent's OAuth handler

**What it does:**
```javascript
window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
```

**Replacement Option:**
- Use **Google OAuth hosted flow directly** OR Firebase Authentication
- Can use `@react-oauth/google` package for a simpler flow
- You'll need Google OAuth Client ID (from Google Cloud Console)

**Files to Modify:**
- [frontend/src/App.js](frontend/src/App.js#L185-L195) - Replace Emergent redirect with Google OAuth flow
- [frontend/package.json](frontend/package.json) - Add `@react-oauth/google` or Firebase library

---

### B. Emergent UI Scripts & Assets
**Location:** [frontend/public/index.html](frontend/public/index.html#L20-L45)  
**Purpose:** Load Emergent frameworks and visual editing tools

**What it does:**
```html
<script src="https://assets.emergent.sh/scripts/emergent-main.js"></script>
<script src="https://assets.emergent.sh/scripts/debug-monitor.js"></script>
<a href="https://app.emergent.sh/?utm_source=emergent-badge">Made with Emergent</a>
```

**Replacement:** 
- Simply **remove** these - they're not essential for functionality
- The app uses Tailwind + Shadcn UI which work without Emergent

**Files to Modify:**
- [frontend/public/index.html](frontend/public/index.html) - Remove all Emergent script references and badge

---

### C. Dev Server CORS Whitelist
**Location:** [frontend/plugins/visual-edits/dev-server-setup.js](frontend/plugins/visual-edits/dev-server-setup.js#L357-L363)  
**Purpose:** Allow Emergent domains in dev server

**Replacement:**
- Remove or update CORS rules for local development

**Files to Modify:**
- [frontend/plugins/visual-edits/dev-server-setup.js](frontend/plugins/visual-edits/dev-server-setup.js) - Remove `emergent.sh` and `emergentagent.com` origin checks

---

## 3. **SUMMARY TABLE**

| Dependency | Type | Location | Replacement | Effort |
|-----------|------|----------|------------|--------|
| `emergentintegrations` | Python Package | backend/requirements.txt | `openai` package | Medium |
| Google OAuth verification | Backend API | backend/server.py | Google JWT verification | Medium |
| Google OAuth redirect | Frontend | frontend/src/App.js | `@react-oauth/google` | Medium |
| Emergent UI scripts | HTML/Assets | frontend/public/index.html | Delete | Easy |
| CORS whitelist | Dev config | frontend/plugins/visual-edits/dev-server-setup.js | Update/Delete | Easy |

---

## 4. **WHAT YOU NEED TO PROVIDE**

### Option A: Use OpenAI Directly
1. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
   - Set as `OPENAI_API_KEY` in backend/.env
   - Cost: ~$0.15 per 1M input tokens (GPT-4o-mini is very cheap)

### Option B: Use Google OAuth
1. **Google OAuth Client ID** - Get from Google Cloud Console
   - Create a project at https://console.cloud.google.com
   - Create OAuth 2.0 credentials
   - Add your frontend domain to authorized origins
   - Set `REACT_APP_GOOGLE_CLIENT_ID` in frontend/.env

### Current Auth Status:
- ✅ Email/Password auth: **No Emergent dependency** - works as-is
- ❌ Google OAuth: Needs replacement (both frontend & backend)

---

## 5. **NEXT STEPS**

1. Get OpenAI API key (if using their LLM)
2. Get Google OAuth credentials (if keeping Google OAuth)
3. I'll then update all files to remove Emergent dependencies
4. Test with local MongoDB setup

**Want me to proceed with the changes?** Just let me know:
- Keep Google OAuth or remove it?
- Use OpenAI directly or use a different AI service?
- Any preferences on authentication beyond Email/Password?
