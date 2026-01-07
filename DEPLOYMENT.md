# Deployment Guide - AnyGraph to Production

## ✅ Changes Made

Your application has been updated to remove Docker dependency! This allows deployment to free hosting platforms.

### What Changed:
- ✅ Replaced Docker container execution with secure subprocess-based code execution
- ✅ Added security validation to prevent dangerous code
- ✅ Maintained timeout and error handling
- ✅ Added matplotlib, seaborn, scikit-learn as direct dependencies
- ✅ Updated health check endpoint
- ✅ All existing functionality preserved

## 🚀 Deployment Options (Free Tier)

### Option 1: Render (Recommended - Easiest)

**Cost:** Free tier available (750 hours/month)

**Steps:**
1. Push your code to GitHub (already done!)
2. Go to [render.com](https://render.com) and sign up
3. Click "New +" → "Web Service"
4. Connect your GitHub account and select `anygraph_backend` repository
5. Render will auto-detect the `render.yaml` configuration
6. Add environment variables:
   - `NEONDB_URL`: Your Neon database connection string
   - `GEMINI_API_KEY`: Your Google Gemini API key
7. Click "Create Web Service"
8. Wait for deployment (5-10 minutes)
9. Copy your service URL (e.g., `https://anygraph-backend.onrender.com`)

**Note:** Free tier services spin down after 15 minutes of inactivity and take ~30 seconds to wake up.

### Option 2: Railway

**Cost:** $5 credit/month free, then pay-as-you-go

**Steps:**
1. Go to [railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `anygraph_backend` repository
4. Railway auto-detects Python and installs dependencies
5. Add environment variables in the "Variables" tab:
   - `NEONDB_URL`
   - `GEMINI_API_KEY`
6. Add a start command in Settings:
   ```
   uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```
7. Railway will generate a public URL

### Option 3: Fly.io

**Cost:** Free tier (3 shared-cpu VMs)

**Steps:**
1. Install flyctl: `brew install flyctl` (macOS)
2. Sign up: `flyctl auth signup`
3. In your backend directory:
   ```bash
   cd /Users/noahwolk/anygraph2/anygraph_backend
   flyctl launch
   ```
4. Follow prompts (don't deploy yet)
5. Set secrets:
   ```bash
   flyctl secrets set NEONDB_URL="your_neon_url"
   flyctl secrets set GEMINI_API_KEY="your_gemini_key"
   ```
6. Deploy: `flyctl deploy`

## 🎨 Frontend Deployment (Vercel)

**Cost:** Free tier (generous limits)

**Steps:**
1. Go to [vercel.com](https://vercel.com) and sign up with GitHub
2. Click "Add New" → "Project"
3. Import `anygraph_frontend` repository
4. Vercel auto-detects Next.js configuration
5. Add environment variables:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: (from your `.env`)
   - `CLERK_SECRET_KEY`: (from your `.env`)
   - `UPLOADTHING_TOKEN`: (from your `.env`)
   - `NEXT_PUBLIC_API_URL`: Your backend URL from step 1 (e.g., `https://anygraph-backend.onrender.com`)
6. Click "Deploy"
7. Wait 2-3 minutes
8. Your site will be live at `https://your-project.vercel.app`

## 🔧 Post-Deployment Configuration

### 1. Update CORS in Backend
After deploying frontend, update [src/main.py](src/main.py) line 24:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",  # Your Vercel URL
        "http://localhost:3000"  # Keep for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push:
```bash
git add src/main.py
git commit -m "Update CORS for production"
git push
```

Render/Railway will auto-redeploy.

### 2. Update Clerk Redirect URLs
1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Select your application
3. Go to "Paths" or "Domains"
4. Add your production URL: `https://your-frontend.vercel.app`
5. Update redirect URLs to include production domain

### 3. Update UploadThing Domains (if needed)
1. Go to [UploadThing Dashboard](https://uploadthing.com/dashboard)
2. Add your production domain if required

## 📊 Verify Deployment

### Test Backend:
```bash
curl https://your-backend-url.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "executor": "available",
  "timestamp": "..."
}
```

### Test Frontend:
1. Visit your Vercel URL
2. Sign in with Clerk
3. Upload a dataset
4. Run a query

## 🔍 Monitoring & Debugging

### Backend Logs (Render):
- Dashboard → Your Service → "Logs" tab
- Real-time streaming logs

### Backend Logs (Railway):
- Project → Deployments → Click deployment → "View Logs"

### Frontend Logs (Vercel):
- Project → Deployments → Click deployment → "Runtime Logs"

### Common Issues:

**Backend won't start:**
- Check environment variables are set correctly
- Verify Neon database URL is accessible
- Check logs for Python errors

**Frontend can't connect to backend:**
- Verify `NEXT_PUBLIC_API_URL` is set to your backend URL
- Check CORS configuration in backend
- Verify backend is healthy: `curl https://backend-url/health`

**Code execution fails:**
- Check backend logs for execution errors
- Verify matplotlib/pandas are installed (check deployment logs)
- Test locally first

## 💰 Cost Estimates

**Current Setup (All Free Tiers):**
- Frontend (Vercel): Free ✅
- Backend (Render): Free ✅
- Database (Neon): Free ✅
- Auth (Clerk): Free up to 10k users ✅
- File Storage (UploadThing): Free up to 2GB ✅
- Gemini API: Free tier available ✅

**Total:** $0/month for moderate usage!

**Scaling Considerations:**
- Render free tier: 750 hours/month, spins down after inactivity
- If you need 24/7 uptime: Render Starter ($7/month)
- Railway: $5 free credit/month, then ~$5-10/month
- Vercel: Pro plan only needed for teams ($20/month)

## 🎯 Next Steps

1. **Deploy Backend** → Choose Render (easiest) and follow steps above
2. **Deploy Frontend** → Deploy to Vercel with backend URL
3. **Update CORS** → Restrict to production domain
4. **Test Everything** → Sign in, upload, query
5. **Share Your App!** 🎉

## 📝 Additional Resources

- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Neon Docs](https://neon.tech/docs)

---

**Note:** All services mentioned have generous free tiers suitable for side projects and MVP launches. You can always upgrade later as usage grows!
