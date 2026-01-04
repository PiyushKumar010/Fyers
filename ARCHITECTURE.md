# 🏗️ Deployment Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER'S BROWSER                          │
│                     https://your-app.vercel.app                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTPS
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    VERCEL (Frontend)                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  React App (Static Files)                                  │ │
│  │  • HTML, CSS, JavaScript                                   │ │
│  │  • Components, Routing                                     │ │
│  │  • Charts, UI                                              │ │
│  │                                                            │ │
│  │  Environment Variables:                                    │ │
│  │    VITE_API_BASE_URL=https://backend.onrender.com         │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ API Requests
                     │ (HTTPS)
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                   RENDER (Backend)                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Application                                       │ │
│  │  • REST API Endpoints                                      │ │
│  │  • Authentication Logic                                    │ │
│  │  • Technical Indicators                                    │ │
│  │  • WebSocket Support                                       │ │
│  │                                                            │ │
│  │  Environment Variables:                                    │ │
│  │    FYERS_CLIENT_ID, FYERS_SECRET_KEY                      │ │
│  │    MONGO_URI, DB_NAME                                     │ │
│  │    ALLOWED_ORIGINS=https://your-app.vercel.app            │ │
│  └────────────────────┬───────────────────┬──────────────────┘ │
└─────────────────────┬─┴───────────────────┴─┬──────────────────┘
                      │                       │
            API Calls │                       │ Database Queries
                      │                       │
         ┌────────────▼──────────┐   ┌────────▼─────────────┐
         │   FYERS API           │   │  MongoDB Atlas       │
         │  api.fyers.in         │   │  (Cloud Database)    │
         │                       │   │                      │
         │  • Market Data        │   │  • User Tokens       │
         │  • Authentication     │   │  • OHLC Cache        │
         │  • Order Placement    │   │  • User Data         │
         │  • WebSocket Feeds    │   │  • Portfolio         │
         └───────────────────────┘   └──────────────────────┘
```

## Data Flow

### 1. User Authentication Flow
```
User → Frontend → Backend → Fyers API
                   ↓
              MongoDB (Store Token)
                   ↓
Backend → Frontend → User (Authenticated)
```

### 2. Market Data Request Flow
```
User → Frontend → Backend → Check MongoDB Cache
                              ↓
                         Cache Miss? → Fyers API
                              ↓
                         Store in MongoDB
                              ↓
                   Backend → Frontend → User (Display Chart)
```

### 3. Technical Analysis Flow
```
User → Frontend → Backend → Fetch OHLC Data
                              ↓
                         Calculate Indicators
                              ↓
                   Backend → Frontend → User (Show Signals)
```

## Deployment Components

### Frontend (Vercel)
- **Type**: Static Site (SPA)
- **Framework**: React + Vite
- **Build Time**: ~2 minutes
- **CDN**: Global Edge Network
- **Cost**: Free tier (100 GB bandwidth)
- **Auto-Deploy**: ✅ On git push

### Backend (Render)
- **Type**: Web Service
- **Runtime**: Python 3.12
- **Server**: Uvicorn (ASGI)
- **Build Time**: ~3-5 minutes
- **Hosting**: us-east region (configurable)
- **Cost**: Free tier (750 hours/month)
- **Auto-Deploy**: ✅ On git push
- **Sleep**: After 15 min inactivity
- **Wake-up**: ~30 seconds (cold start)

### Database (MongoDB Atlas)
- **Type**: Cloud Database (NoSQL)
- **Cluster**: M0 Free Tier
- **Storage**: 512 MB
- **Region**: Configurable
- **Hosting**: AWS/GCP/Azure
- **Cost**: Free tier
- **Backup**: Daily snapshots (paid)

## Network Security

### HTTPS/SSL
```
✅ Frontend: Automatic SSL (Vercel)
✅ Backend: Automatic SSL (Render)
✅ Database: TLS/SSL Connection (MongoDB)
```

### CORS Configuration
```python
# Backend allows these origins:
origins = [
    "http://localhost:5173",           # Local dev
    "https://your-app.vercel.app",     # Production frontend
]
```

### Environment Variables (Secrets)
```
Frontend (Vercel):
  • VITE_API_BASE_URL (public, embedded in JS)

Backend (Render):
  • FYERS_CLIENT_ID (secret)
  • FYERS_SECRET_KEY (secret)
  • MONGO_URI (secret)
  • DB_NAME (public)
  • ALLOWED_ORIGINS (public)
```

## Request/Response Flow

### Example: Fetch OHLC Data

```
1. User clicks "Load Chart" on Frontend
   └─> Component: OhlcDashboard.jsx

2. Frontend calls API service
   └─> File: src/api/fyersApi.js
   └─> Request: GET /ohlc/?symbol=NSE:TCS-EQ&from_date=2026-01-01&...

3. Request reaches Backend
   └─> Route: app/routes/ohlc.py
   └─> Endpoint: get_ohlc_data()

4. Backend checks MongoDB cache
   └─> Service: app/database.py
   └─> Collection: ohlc_cache

5a. Cache Hit → Return cached data
5b. Cache Miss → Query Fyers API

6. Fyers API returns data
   └─> Service: app/services/fyers.py
   └─> Store in MongoDB

7. Backend returns JSON to Frontend
   └─> Format: {candles: [...], count: 75, source: "fyers"}

8. Frontend renders chart
   └─> Component: CandlestickChart.jsx
   └─> Library: Recharts
```

## Monitoring & Observability

### Application Logs

**Frontend (Vercel):**
```
Dashboard → Project → Deployments → [Latest] → Logs
```

**Backend (Render):**
```
Dashboard → Service → Logs (Real-time)
```

### Health Checks

**Backend Health Endpoint:**
```bash
GET https://your-backend.onrender.com/health
Response: {"status": "ok"}
```

**Automatic Health Check:**
- Render pings `/health` every 5 minutes
- If fails → Service marked unhealthy
- Automatic restart after 3 failures

### Performance Monitoring

**Frontend:**
- Vercel Analytics (optional, paid)
- Browser DevTools → Network Tab
- Lighthouse scores

**Backend:**
- Render Metrics Dashboard
- Response times visible in logs
- CPU/Memory usage graphs

## Scaling Considerations

### Current Setup (Free Tier)
```
Concurrent Users:    ~10-50
Request Rate:        ~10 req/sec
Database Size:       512 MB
Uptime:              Best effort (cold starts)
```

### When to Upgrade

**Frontend (Vercel Pro - $20/mo):**
- Exceeded 100 GB bandwidth
- Need commercial support
- Want advanced analytics

**Backend (Render Starter - $7/mo):**
- Need 24/7 uptime (no cold starts)
- More CPU/RAM required
- Higher traffic volume

**Database (MongoDB M10 - $57/mo):**
- Exceeded 512 MB storage
- Need automated backups
- Require better performance

## Disaster Recovery

### Backup Strategy

**Database:**
```
MongoDB Atlas:
  • Daily snapshots (paid feature)
  • Manual backup: mongodump
  • Restore: mongorestore
```

**Code:**
```
GitHub:
  • All code version controlled
  • Deploy from any commit
  • Roll back in seconds
```

### Recovery Procedures

**Backend Outage:**
1. Check Render logs for errors
2. Verify environment variables
3. Redeploy from working commit
4. Check MongoDB connectivity

**Frontend Outage:**
1. Check Vercel build logs
2. Verify environment variables
3. Redeploy from working commit
4. Clear CDN cache if needed

**Database Outage:**
1. Check MongoDB Atlas status
2. Verify network access settings
3. Check connection string
4. Restore from backup if needed

## Cost Estimation

### Free Tier (Current Setup)
```
MongoDB Atlas M0:     $0/month
Render Free:          $0/month (with cold starts)
Vercel Free:          $0/month

Total: $0/month ✅
```

### Production Tier (Recommended for business)
```
MongoDB Atlas M10:    $57/month
Render Starter:       $7/month
Vercel Pro:           $20/month

Total: $84/month
```

### Enterprise Tier (High traffic)
```
MongoDB Atlas M30:    $200/month
Render Standard:      $25/month
Vercel Pro:           $20/month

Total: $245/month
```

## URLs Reference

After deployment, save these:

```
┌─────────────────────────────────────────────────────────────┐
│  PRODUCTION URLS (Fill in after deployment)                 │
├─────────────────────────────────────────────────────────────┤
│  Frontend:                                                   │
│    https://________________________________.vercel.app       │
│                                                              │
│  Backend:                                                    │
│    https://________________________________.onrender.com     │
│                                                              │
│  API Docs:                                                   │
│    https://________________________________.onrender.com/docs│
│                                                              │
│  Health Check:                                               │
│    https://________________________________.onrender.com/health│
│                                                              │
│  MongoDB:                                                    │
│    mongodb+srv://________________________________________    │
└─────────────────────────────────────────────────────────────┘
```

---

**This architecture provides:**
- ✅ Scalable infrastructure
- ✅ Global CDN for frontend
- ✅ Automatic SSL/HTTPS
- ✅ Auto-deployment pipeline
- ✅ Free tier to start
- ✅ Easy to upgrade when needed
