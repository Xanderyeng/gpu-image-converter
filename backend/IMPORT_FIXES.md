# Import Fixes Summary

## Issues Fixed

### 1. ✅ `pyvips.concurrency_set` AttributeError
**Problem:** `pyvips` module didn't expose the `concurrency_set` function on your installation.

**Fix:** Updated `backend/app/converter.py` to gracefully handle missing pyvips helper functions with a safe fallback pattern that tries multiple paths and logs warnings instead of crashing.

**Files changed:**
- `backend/app/converter.py` - Added `_safe_pyvips_call()` helper

### 2. ✅ Permission denied: '/app/uploads'
**Problem:** `app/main.py` hardcoded Docker paths (`/app/uploads`, `/app/outputs`) which don't exist and aren't writable in local development.

**Fix:** Updated path defaults to use relative paths in the backend directory while preserving Docker compatibility via environment variables.

**Files changed:**
- `backend/app/main.py` - Now defaults to `backend/uploads` and `backend/outputs` locally

## How to Test

### From your activated venv:

```bash
cd /home/lex/projects/gpu-image-converter/backend

# Make sure venv is activated (you should see (venv) in your prompt)
source venv/bin/activate  # or: source .venv/bin/activate

# Quick test
python -c "from app.main import app; print('✅ FastAPI OK')"

# Detailed test (using the helper script)
python test_import.py
```

### Expected output:
```
pyvips.concurrency_set not available; skipping
✅ FastAPI OK
```

(The "not available; skipping" warning is normal and harmless - it just means your pyvips build doesn't expose that helper, but the app will work fine.)

## New directories created
After the first successful import, you'll see:
```
backend/
  uploads/    <- created automatically
  outputs/    <- created automatically
```

## Environment Variables (optional)
You can override the paths via environment variables:
```bash
export UPLOAD_DIR=/custom/path/uploads
export OUTPUT_DIR=/custom/path/outputs
python -c "from app.main import app; print('✅ FastAPI OK')"
```

## Docker
In Docker, set these in your docker-compose.yml or Dockerfile:
```yaml
environment:
  - UPLOAD_DIR=/app/uploads
  - OUTPUT_DIR=/app/outputs
```

The Dockerfile already creates these directories, so no changes needed for Docker deployment.
