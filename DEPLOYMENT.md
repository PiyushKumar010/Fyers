# Deployment Guide

## Prerequisites
- GitHub account
- Vercel account (for frontend)
- Render account (for backend)
- MongoDB Atlas account (for database)

---

## Part 1: MongoDB Atlas Setup (Do this first)

1. **Create MongoDB Atlas Account**
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up for a free account

2. **Create a Cluster**
   - Click "Build a Database"
   - Choose "M0 Free" tier
   - Select a cloud provider and region (choose one close to your users)
   - Click "Create Cluster"

3. **Create Database User**
   - Go to "Database Access" in the left sidebar
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Set username and password (save these!)
   - Set privileges to "Read and write to any database"
   - Click "Add User"

4. **Whitelist IP Addresses**
   - Go to "Network Access" in the left sidebar
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (for development)
   - Click "Confirm"

5. **Get Connection String**
   - Go to "Database" in the left sidebar
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (looks like: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`)
   - Replace `<username>` and `<password>` with your database user credentials

---

## Part 2: Backend Deployment to Render

### Step 1: Prepare Your Repository
1. **Push your code to GitHub** (if not already done):
   ```bash
   cd C:\coding\Projects\fyers-ohlc
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

### Step 2: Deploy to Render
1. **Go to Render Dashboard**
   - Visit https://render.com
   - Sign up or log in with GitHub

2. **Create a New Web Service**
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository `fyers-ohlc`
   - Or paste repository URL if public

3. **Configure the Service**
   - **Name**: `fyers-backend` (or any name you prefer)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `fyers-ohlc-backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables**
   Click "Advanced" and add these environment variables:
   
   ```
   FYERS_CLIENT_ID=<your_fyers_client_id>
   FYERS_SECRET_KEY=<your_fyers_secret_key>
   FYERS_REDIRECT_URI=https://your-app-name.onrender.com/auth/callback
   MONGO_URI=<your_mongodb_connection_string_from_step_1>
   DB_NAME=fyers_ohlc
   REFRESH_BUFFER_SECONDS=60
   REFRESH_CHECK_INTERVAL=300
   DISABLE_TOKEN_REFRESHER=false
   DISABLE_LIVE_DATA_STORAGE=true
   LIVE_DATA_THRESHOLD_DAYS=1
   ```
   
   **Important Notes:**
   - Replace `<your_fyers_client_id>` with your actual Fyers client ID
   - Replace `<your_fyers_secret_key>` with your actual Fyers secret key
   - Replace `your-app-name` in the redirect URI with your actual Render app name
   - Use the MongoDB connection string from Part 1

5. **Select Free Plan**
   - Choose "Free" plan (good for testing)
   - Click "Create Web Service"

6. **Wait for Deployment**
   - Render will build and deploy your app
   - This takes 5-10 minutes
   - Watch the logs for any errors

7. **Copy Your Backend URL**
   - Once deployed, copy the URL (e.g., `https://your-app-name.onrender.com`)
   - You'll need this for the frontend

8. **Update CORS in Backend** (if needed later)
   - After deploying frontend, add your frontend URL to the CORS origins in `app/main.py`

---

## Part 3: Frontend Deployment to Vercel

### Step 1: Update Frontend Configuration
1. **Create Environment File**
   - In `fyers-frontend` folder, create a `.env.production` file:
   ```
   VITE_API_BASE_URL=https://your-backend-app.onrender.com
   ```
   - Replace `your-backend-app` with your actual Render backend URL from Part 2

### Step 2: Deploy to Vercel
1. **Go to Vercel Dashboard**
   - Visit https://vercel.com
   - Sign up or log in with GitHub

2. **Import Your Repository**
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Or click "Import Git Repository" and paste URL

3. **Configure Project**
   - **Framework Preset**: Vite
   - **Root Directory**: `fyers-frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

4. **Set Environment Variables**
   - Click "Environment Variables"
   - Add:
     ```
     VITE_API_BASE_URL=https://your-backend-app.onrender.com
     ```
   - Replace with your actual Render backend URL

5. **Deploy**
   - Click "Deploy"
   - Wait 2-5 minutes for deployment
   - Vercel will show you the live URL (e.g., `https://your-app.vercel.app`)

### Step 3: Update Backend CORS
1. **Add Frontend URL to Backend**
   - Go to your backend code: `fyers-ohlc-backend/app/main.py`
   - Find the `origins` list (around line 20)
   - Add your Vercel URL:
   ```python
   origins = [
       "http://localhost:5173",
       "http://127.0.0.1:5173",
       "https://your-app.vercel.app",  # Add this line
   ]
   ```
   - Commit and push changes
   - Render will automatically redeploy

---

## Part 4: Update Fyers Redirect URI

1. **Go to Fyers API Dashboard**
   - Visit https://myapi.fyers.in/dashboard
   - Log in with your Fyers account

2. **Update Redirect URI**
   - Go to your app settings
   - Add your production backend callback URL:
     ```
     https://your-backend-app.onrender.com/auth/callback
     ```
   - Save changes

---

## Part 5: Test Your Deployment

1. **Visit Your Frontend**
   - Open your Vercel URL in a browser
   - Test the authentication flow
   - Check if data loads correctly

2. **Check Backend Health**
   - Visit `https://your-backend-app.onrender.com/health`
   - Should return `{"status": "ok"}`

3. **Check API Docs**
   - Visit `https://your-backend-app.onrender.com/docs`
   - Should show FastAPI Swagger UI

---

## Troubleshooting

### Backend Issues
- **Check Render Logs**: Go to your Render service → "Logs" tab
- **Environment Variables**: Verify all variables are set correctly
- **MongoDB Connection**: Test connection string in MongoDB Compass
- **Port Binding**: Ensure `--host 0.0.0.0 --port $PORT` is in start command

### Frontend Issues
- **Check Vercel Logs**: Go to your Vercel project → "Deployments" → Click deployment → "Logs"
- **Environment Variables**: Verify `VITE_API_BASE_URL` is set
- **CORS Errors**: Add frontend URL to backend CORS origins
- **Build Errors**: Check if `npm run build` works locally

### Common Errors
1. **"Failed to fetch"** - Check if backend is running and URL is correct
2. **CORS errors** - Add frontend URL to backend CORS origins
3. **401 Unauthorized** - Check Fyers credentials and redirect URI
4. **MongoDB connection failed** - Verify connection string and whitelist IP

---

## Auto-Deployment (Continuous Deployment)

Both Vercel and Render support automatic deployment:
- **Vercel**: Automatically deploys on every push to `main` branch
- **Render**: Automatically deploys on every push to `main` branch

To disable auto-deploy:
- **Vercel**: Go to project settings → Git → Disable "Production Branch"
- **Render**: Go to service settings → Disable "Auto-Deploy"

---

## Cost Considerations

### Free Tier Limits:
- **MongoDB Atlas**: 512 MB storage (enough for development)
- **Render**: 750 hours/month, apps spin down after 15 min inactivity (cold start ~30s)
- **Vercel**: 100 GB bandwidth, unlimited deployments

### Tips to Stay Free:
- Use MongoDB Atlas M0 free tier
- Accept Render cold starts or upgrade to paid plan
- Optimize bundle size to stay under Vercel limits

---

## Security Best Practices

1. **Never commit sensitive data**:
   - Keep `.env` files in `.gitignore`
   - Use environment variables for all secrets

2. **Use HTTPS only** in production:
   - Both Vercel and Render provide free SSL

3. **Restrict CORS** to your domains:
   - Don't use `"*"` in production CORS settings

4. **Rotate credentials** regularly:
   - Change Fyers API credentials periodically
   - Update MongoDB passwords

---

## Monitoring

### Backend Monitoring (Render)
- Check logs: Service → Logs
- Monitor uptime: Service → Metrics
- Set up health checks: Service → Settings → Health Check Path = `/health`

### Frontend Monitoring (Vercel)
- Check logs: Project → Deployments → [Deployment] → Logs
- Monitor analytics: Project → Analytics (paid feature)

---

## Scaling

When you outgrow free tiers:

### Backend (Render)
- Upgrade to paid plan (~$7/month) for:
  - No cold starts
  - More RAM and CPU
  - Auto-scaling

### Frontend (Vercel)
- Upgrade to Pro plan (~$20/month) for:
  - More bandwidth
  - Advanced analytics
  - Team collaboration

### Database (MongoDB Atlas)
- Upgrade to M10 cluster (~$57/month) for:
  - More storage
  - Better performance
  - Automated backups

---

## Summary

✅ **What you did:**
1. Created MongoDB database
2. Deployed backend to Render
3. Deployed frontend to Vercel
4. Connected everything together

✅ **URLs to save:**
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-backend-app.onrender.com`
- API Docs: `https://your-backend-app.onrender.com/docs`

✅ **Next steps:**
- Test all features
- Monitor logs
- Set up custom domain (optional)
- Add analytics (optional)
