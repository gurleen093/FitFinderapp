# FitFinder Deployment Guide

## 🚀 Deploy to Render.com

### Prerequisites
- Docker account
- Render.com account
- Git repository (GitHub, GitLab, etc.)

### Step 1: Prepare Your Repository
1. **Push code to Git repository** (GitHub recommended for Render)
2. **Ensure all files are committed**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

### Step 2: Environment Variables
Create a `.env` file for local testing (not committed to Git):
```env
OPENAI_API_KEY=your_openai_api_key_here
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here
```

### Step 3: Deploy on Render
1. **Go to [Render.com](https://render.com)**
2. **Sign up/Login** with your GitHub account
3. **Click "New +"** → **"Web Service"**
4. **Connect your repository**
5. **Configure deployment**:
   - **Name**: `fitfinder-app`
   - **Environment**: `Docker`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Dockerfile Path**: `./Dockerfile` (default)

6. **Set Environment Variables**:
   - `OPENAI_API_KEY` = your OpenAI API key
   - `ADZUNA_APP_ID` = your Adzuna app ID  
   - `ADZUNA_APP_KEY` = your Adzuna app key

7. **Advanced Settings**:
   - **Port**: `8501`
   - **Health Check Path**: `/_stcore/health`
   - **Auto-Deploy**: `Yes`

8. **Click "Create Web Service"**

### Step 4: Custom Domain (Optional)
1. **Go to Settings** → **Custom Domains**
2. **Add your domain**
3. **Update DNS records** as instructed

## 🐳 Local Docker Testing

### Build and Run Locally
```bash
# Build the Docker image
docker build -t fitfinder .

# Run the container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  -e ADZUNA_APP_ID=your_id \
  -e ADZUNA_APP_KEY=your_key \
  fitfinder

# Access at http://localhost:8501
```

### With Docker Compose (Optional)
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  fitfinder:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ADZUNA_APP_ID=${ADZUNA_APP_ID}
      - ADZUNA_APP_KEY=${ADZUNA_APP_KEY}
    restart: unless-stopped
```

Run with:
```bash
docker-compose up
```

## 🔧 Troubleshooting

### Common Issues
1. **Build fails**: Check requirements.txt for version conflicts
2. **App won't start**: Verify environment variables are set
3. **404 errors**: Ensure port 8501 is exposed correctly
4. **Import errors**: Check all files are included in Docker image

### Render-Specific
- **Logs**: Check Render dashboard for build/runtime logs
- **Health checks**: App must respond to `/_stcore/health`
- **Memory**: Render free tier has 512MB limit
- **Sleep**: Free apps sleep after 15 minutes of inactivity

### Performance Optimization
- **Use .dockerignore** to reduce image size
- **Multi-stage builds** for production (optional)
- **Environment-specific configs**

## 🌐 API Keys Setup

### OpenAI API
1. Go to [OpenAI Platform](https://platform.openai.com)
2. Create API key
3. Add to Render environment variables

### Adzuna API
1. Go to [Adzuna Developer](https://developer.adzuna.com)
2. Create account and app
3. Get App ID and Key
4. Add to Render environment variables

## 📊 Monitoring
- **Render Dashboard**: Monitor app status, logs, metrics
- **Health checks**: Automatic monitoring via `/_stcore/health`
- **Logs**: Real-time logs available in Render dashboard

## 🔄 Updates
- **Auto-deploy**: Enabled by default on main branch pushes
- **Manual deploy**: Use Render dashboard "Manual Deploy" button
- **Rollback**: Available in Render dashboard

Your app will be available at: `https://your-app-name.onrender.com`