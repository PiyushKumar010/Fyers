# How to Restart the Backend Server

The timezone fixes have been applied to the code, but your backend server needs to be restarted to pick up these changes.

## Steps to Restart:

### Option 1: If running in a terminal
1. Find the terminal window where the backend is running
2. Press `Ctrl+C` to stop it
3. Restart it with:
   ```bash
   cd c:\coding\Projects\fyers-ohlc\fyers-ohlc-backend
   ..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: If running as a service/background process
1. Find and stop the Python process running the backend
2. Restart it using the command above

### Option 3: Quick test without full restart
You can test the API endpoint directly in your browser:
- Open: `http://localhost:8000/market/status`
- You should see: `"is_open": true` (during market hours)

## What Changed?
- The backend now correctly uses IST (Indian Standard Time) for all market hour checks
- Market hours: 9:15 AM - 3:30 PM IST, Monday-Friday (excluding holidays)
- All timestamps in OHLC data now display in IST

## Verification
After restarting, refresh your frontend and you should see:
- ✅ "Market is Open" during trading hours (9:15 AM - 3:30 PM IST, Mon-Fri)
- ✅ Timestamps in IST (matching your local time)
- ✅ Correct market status on the dashboard
