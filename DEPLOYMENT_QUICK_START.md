# 🚀 Quick Deployment Checklist

Use this checklist to deploy your Fyers Trading Platform to production.

## ✅ Pre-Deployment Checklist

- [ ] Code is committed to GitHub
- [ ] All tests pass locally
- [ ] Frontend builds successfully (`npm run build`)
- [ ] Backend runs without errors
- [ ] Environment variables documented

## 📋 Deployment Order

### 1️⃣ MongoDB Atlas (Database) - DO THIS FIRST
```
✓ Create account at mongodb.com/cloud/atlas
✓ Create free M0 cluster
✓ Add database user (username + password)
✓ Whitelist all IPs (0.0.0.0/0)
✓ Get connection string
```

**Connection string format:**
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

---

### 2️⃣ Backend Deployment (Render)

**Service Configuration:**
```
Name:           fyers-backend
Runtime:        Python 3
Root Directory: fyers-ohlc-backend
Build Command:  pip install -r requirements.txt
Start Command:  uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables (copy these to Render):**
```bash
FYERS_CLIENT_ID=<get_from_fyers_dashboard>
FYERS_SECRET_KEY=<get_from_fyers_dashboard>
FYERS_REDIRECT_URI=https://YOUR-APP-NAME.onrender.com/auth/callback
MONGO_URI=<mongodb_connection_string_from_step_1>
DB_NAME=fyers_ohlc
ALLOWED_ORIGINS=
REFRESH_BUFFER_SECONDS=60
REFRESH_CHECK_INTERVAL=300
DISABLE_TOKEN_REFRESHER=false
DISABLE_LIVE_DATA_STORAGE=true
LIVE_DATA_THRESHOLD_DAYS=1
```

**After deployment:**
- [ ] Copy your backend URL (e.g., `https://fyers-backend-xxxx.onrender.com`)
- [ ] Test: Visit `https://YOUR-APP.onrender.com/health`
- [ ] Should return: `{"status":"ok"}`

---

### 3️⃣ Frontend Deployment (Vercel)

**Project Configuration:**
```
Framework:      Vite
Root Directory: fyers-frontend
Build Command:  npm run build
Output Dir:     dist
```

**Environment Variables (set in Vercel):**
```bash
VITE_API_BASE_URL=https://YOUR-BACKEND-APP.onrender.com
```
⚠️ **Replace with your actual Render backend URL from Step 2**

**After deployment:**
- [ ] Copy your frontend URL (e.g., `https://your-app.vercel.app`)

---

### 4️⃣ Update Backend CORS

**Option A: Using Environment Variable (Recommended)**
Add to Render environment variables:
```bash
ALLOWED_ORIGINS=https://your-app.vercel.app
```

**Option B: Code Change**
Edit `fyers-ohlc-backend/app/main.py` and add your Vercel URL to the origins list.

Then redeploy (Render auto-deploys on git push).

---

### 5️⃣ Update Fyers API Settings

**Go to:** https://myapi.fyers.in/dashboard

**Add Redirect URI:**
```
https://YOUR-BACKEND-APP.onrender.com/auth/callback
```

---

## 🧪 Post-Deployment Testing

### Backend Health Check
```bash
curl https://YOUR-BACKEND-APP.onrender.com/health
# Expected: {"status":"ok"}
```

### Backend API Docs
Visit: `https://YOUR-BACKEND-APP.onrender.com/docs`

### Frontend Access
Visit: `https://YOUR-FRONTEND-APP.vercel.app`

### Test Authentication Flow
1. Click "Login" on frontend
2. Should redirect to Fyers
3. After login, should redirect back to your app
4. Should show authenticated status

---

## 🔧 Environment Variable Summary

### Frontend (Vercel)
| Variable | Example | Required |
|----------|---------|----------|
| `VITE_API_BASE_URL` | `https://backend.onrender.com` | Yes |

### Backend (Render)
| Variable | Example | Required |
|----------|---------|----------|
| `FYERS_CLIENT_ID` | `ABC123XYZ` | Yes |
| `FYERS_SECRET_KEY` | `SECRET123` | Yes |
| `FYERS_REDIRECT_URI` | `https://backend.onrender.com/auth/callback` | Yes |
| `MONGO_URI` | `mongodb+srv://...` | Yes |
| `DB_NAME` | `fyers_ohlc` | Yes |
| `ALLOWED_ORIGINS` | `https://app.vercel.app` | Recommended |
| `REFRESH_BUFFER_SECONDS` | `60` | Optional |
| `REFRESH_CHECK_INTERVAL` | `300` | Optional |
| `DISABLE_TOKEN_REFRESHER` | `false` | Optional |
| `DISABLE_LIVE_DATA_STORAGE` | `true` | Optional |
| `LIVE_DATA_THRESHOLD_DAYS` | `1` | Optional |

---

## 🐛 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| **Backend build fails** | Check `requirements.txt` syntax |
| **Backend crashes on start** | Verify MongoDB connection string |
| **CORS errors** | Add frontend URL to `ALLOWED_ORIGINS` |
| **401 on auth** | Update Fyers redirect URI |
| **Cold start delays** | Normal on Render free tier (~30s) |
| **Frontend can't reach API** | Check `VITE_API_BASE_URL` |

---

## 💰 Free Tier Limits

| Service | Limit | Note |
|---------|-------|------|
| **MongoDB Atlas** | 512 MB | More than enough |
| **Render** | 750 hrs/month | Auto-sleeps after 15 min |
| **Vercel** | 100 GB bandwidth | Plenty for most apps |

---

## 📱 Important URLs to Save

After deployment, save these URLs:

```
✅ Frontend:     https://_________________.vercel.app
✅ Backend:      https://_________________.onrender.com
✅ API Docs:     https://_________________.onrender.com/docs
✅ Health Check: https://_________________.onrender.com/health
```

---

## 🔄 Continuous Deployment

Both platforms support auto-deploy:

**On every push to `main`:**
- ✅ Vercel rebuilds frontend automatically
- ✅ Render rebuilds backend automatically

**To disable:**
- Vercel: Settings → Git → Disable "Production Branch"
- Render: Service Settings → Disable "Auto-Deploy"

---

## 📞 Need Help?

**Check these resources:**
1. [Full Deployment Guide](./DEPLOYMENT.md)
2. [Project README](./README.md)
3. Backend logs: Render Dashboard → Your Service → Logs
4. Frontend logs: Vercel Dashboard → Deployments → [Latest] → Logs

**Useful commands:**
```bash
# Test backend locally
cd fyers-ohlc-backend
uvicorn app.main:app --reload

# Test frontend locally
cd fyers-frontend
npm run dev

# Build frontend locally (test)
npm run build

# Check backend syntax
python -m compileall app
```

---

## ✨ You're All Set!

After completing all steps, your application should be:
- ✅ Accessible via public URLs
- ✅ Connected to MongoDB Atlas
- ✅ Authenticated with Fyers API
- ✅ Auto-deploying on git push

**Next steps:**
- Set up custom domain (optional)
- Enable monitoring/alerts
- Add analytics
- Optimize performance
