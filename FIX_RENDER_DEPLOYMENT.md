# Fix Render Deployment - Step by Step Guide

## Problem
Render is not deploying new code from GitHub. Manual deploys and cache clearing didn't work.

## Root Cause
Render service is either:
1. Not connected to GitHub repository
2. Auto-deploy is disabled
3. Watching wrong branch
4. Using old cached deployment configuration

---

## Solution: Manual Steps in Render Dashboard

### Step 1: Access Your Service
1. Go to: **https://dashboard.render.com**
2. Click on your service: **fyers-backend-7kee**

### Step 2: Check Repository Connection
1. Look at the top of the dashboard - you should see:
   - Repository: `PiyushKumar010/Fyers`
   - Branch: `main`
   
2. **If repository is NOT shown or shows "Not Connected":**
   - This is the problem!
   - You need to reconnect or recreate the service
   - See "Option A: Reconnect Repository" below

### Step 3: Check Auto-Deploy Settings
1. Click **Settings** tab (left sidebar)
2. Scroll to **Build & Deploy** section
3. Check these settings:
   - **Auto-Deploy**: Should be **Yes** (not "No")
   - **Branch**: Should be **main**
4. If wrong, click **Edit** and fix them
5. Click **Save Changes**

### Step 4: Trigger Fresh Deployment
1. Go back to main dashboard view
2. Click **Manual Deploy** button (blue button, top right)
3. Select **"Clear build cache & deploy"**
4. Confirm the deployment

### Step 5: Monitor Deployment
1. Click **Logs** tab
2. Watch for:
   ```
   ==> Building from GitHub repo 'PiyushKumar010/Fyers' branch 'main' commit '3e546a74'
   ==> Installing dependencies
   ==> pip install -r requirements.txt
   ==> Starting uvicorn
   ```
3. Deployment takes 2-3 minutes

### Step 6: Verify Deployment Success
After "Your service is live 🎉" message appears, run:
```powershell
powershell -ExecutionPolicy Bypass -File check_deployment.ps1
```

You should see:
- ✅ NEW CODE DEPLOYED
- Response includes `timezone` and `utc_time` fields
- Logs show `[MARKET STATUS]` debug output

---

## Option A: Reconnect Repository (If Disconnected)

### Method 1: Edit Service Settings
1. Settings → Build & Deploy
2. Look for "Repository" field
3. Click "Connect Repository" or "Change Repository"
4. Authorize GitHub if prompted
5. Select: `PiyushKumar010/Fyers`
6. Branch: `main`
7. Save

### Method 2: Recreate Service (If Above Fails)
1. **Export environment variables first!**
   - Settings → Environment → Copy all variables
2. Delete current service
3. Create New Web Service
4. Connect to GitHub: `PiyushKumar010/Fyers`
5. Settings:
   - Name: `fyers-backend`
   - Branch: `main`
   - Root Directory: `fyers-ohlc-backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add all environment variables (paste from step 1)
7. Click "Create Web Service"

---

## Option B: Check for Deployment Errors

### 1. Check Events Tab
- Click **Events** tab
- Look for recent deploy attempts
- Check for error messages

### 2. Check Build Logs
- Logs → Build
- Look for errors in:
  - Git clone
  - Pip install
  - Python version issues

### 3. Common Issues
**"Failed to clone repository"**
- GitHub connection lost
- Need to reconnect repository

**"Build failed"**
- Check requirements.txt
- Check Python version (should be 3.12)

**"Service not responding"**
- Check start command
- Check PORT environment variable

---

## Verification Commands

### Check if new code is deployed:
```powershell
# Check for new fields
curl https://fyers-backend-7kee.onrender.com/market/status | ConvertFrom-Json

# Should have:
# - timezone: "Asia/Kolkata"  
# - utc_time: "2026-01-08T..."
```

### Check commit hash in Render:
1. Logs tab
2. Look for "Building commit 3e546a74" or "Building commit 4e1cbef5"
3. If shows old commit (before 4e1cbef5), not pulling latest code

---

## Expected Logs After Successful Deployment

```
Your service is live 🎉
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

[MARKET STATUS] UTC: 2026-01-08 05:55:00+00:00, IST: 2026-01-08 11:25:00+05:30, Is Open: True, Reason: Market is open
INFO:     61.14.206.70:0 - "GET /market/status HTTP/1.1" 200 OK
```

The `[MARKET STATUS]` line is the debug logging added in commit 4e1cbef5. If you DON'T see it, the new code isn't running.

---

## Still Not Working?

If after ALL the above steps it still shows old code:

### Nuclear Option: Fresh Service with render.yaml
1. Commit the updated render.yaml:
   ```powershell
   git add render.yaml
   git commit -m "Update render.yaml with auto-deploy settings"
   git push origin main
   ```

2. In Render dashboard:
   - Create New → Blueprint
   - Connect to repository: `PiyushKumar010/Fyers`
   - Select `render.yaml`
   - Click "Apply"

This will create a fresh service from scratch using the configuration file.

---

## Contact Information
If none of this works, the issue might be:
- Render account limitations
- GitHub webhook issues
- Render platform bug

Check Render status page: https://status.render.com
