# Render Deployment Guide - FastAPI + ML Project

## Problem Identified
Render is using native Python 3.14.3 instead of Docker, causing `scikit-learn` Cython compilation errors.

## Root Cause
- The existing Render service is configured as a native Python service
- `render.yaml` only works for NEW services created via IaC
- Python 3.14.3 has no wheels for scikit-learn 1.3.2, forcing source build which fails

## Solution: Deploy with Docker

### Step-by-Step Instructions

#### Option 1: Delete and Recreate Service (Recommended)

1. **On Render Dashboard:**
   - Go to your service dashboard
   - Click "Settings" → scroll to "Danger Zone"
   - Click "Delete Service"
   - Confirm deletion

2. **Create New Docker Service:**
   - Go to Render.com dashboard
   - Click "+ New" → "Web Service"
   - Connect GitHub repository
   - Render will auto-detect `render.yaml`
   - Select branch: `main`
   - Click "Create Web Service"

3. **Render will automatically:**
   - Use Docker runtime (from `Dockerfile`)
   - Build with Python 3.12-slim (no Cython compilation issues)
   - Install all dependencies from wheels (fast and reliable)
   - Start the app on the assigned $PORT

#### Option 2: Manual Configuration (If Render doesn't detect render.yaml)

1. **On Render Dashboard:**
   - Create new Web Service
   - Repository: GitHub repo URL
   - Branch: `main`
   - **Runtime: Docker** (select explicitly)
   - **Dockerfile**: `./Dockerfile`
   - **Docker Context**: `/` (leave blank = use root)

2. **Environment Variables:**
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   REDIS_URL=redis://user:pass@host:port/db
   ENVIRONMENT=production
   SECRET_KEY=<generate-32-char-random-string>
   JWT_SECRET=<generate-32-char-random-string>
   GROQ_API_KEY=<your-groq-key>
   ```

3. **Build/Start Commands:**
   - Leave both blank (Dockerfile handles them)

4. **Deploy:** Click "Create Web Service"

### Files in Place

- ✅ `Dockerfile` - Python 3.12-slim, pip/setuptools/wheel upgrade
- ✅ `render.yaml` - IaC configuration for new services
- ✅ `.dockerignore` - Optimize Docker build cache
- ✅ `backend/requirements.txt` - scikit-learn==1.3.2 (Python 3.12 compatible)

### What Happens During Docker Build

1. Base image: `python:3.12-slim` (300MB, fast)
2. Install build tools: pip, setuptools, wheel
3. Copy requirements.txt
4. Install dependencies (all from wheels - 2-3 minutes)
5. Copy app code
6. Start uvicorn on $PORT

**No Cython compilation. No metadata-generation-failed error.**

### Troubleshooting

If Render still shows Python 3.14:
- Confirm service type is "Docker"
- Check Dockerfile path is `./Dockerfile`
- Verify Dockerfile syntax with: `docker build . -t test`
- Clear Render's cache: Delete service → recreate

### Expected Success Indicators

After deployment:
- Build completes in 5-10 minutes (not 30+ minutes)
- No error messages mentioning "Cython" or "metadata-generation-failed"
- App shows "Running" status
- Health check returns: `{"status": "healthy"}`

### Local Testing (Optional)

Test locally before deploying:
```bash
docker build -t ml-app .
docker run -p 8000:10000 \
  -e DATABASE_URL=sqlite:///./local.db \
  -e REDIS_URL=redis://localhost:6379/0 \
  -e GROQ_API_KEY=test \
  ml-app
```

Then visit: `http://localhost:8000/api/health`
