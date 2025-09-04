# Deployment Guide

## Overview

This guide covers deploying the SABDA Scraper API to various cloud platforms. The application is configured for easy deployment with multiple options.

## Prerequisites

- Git repository with your code
- Environment variables configured
- API keys ready for production

## Platform Options

### 1. Render (Recommended)

Render offers excellent Python support with automatic deployments from Git.

#### Setup Steps

1. **Create Render Account**
   - Sign up at [render.com](https://render.com)
   - Connect your GitHub account

2. **Deploy from Dashboard**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Configure settings:
     - **Name:** `sabda-scraper-api`
     - **Environment:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn run:app`
     - **Instance Type:** `Free` or `Starter`

3. **Environment Variables**
   ```
   FLASK_ENV=production
   SECRET_KEY=your_super_secret_key_here_min_32_chars
   FLUTTER_API_KEY=sabda_flutter_2025_secure_key
   MOBILE_API_KEY=sabda_mobile_2025_secure_key
   PORT=10000
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy

#### Using render.yaml (Alternative)

The repository includes `render.yaml` for infrastructure-as-code deployment:

```bash
# Install Render CLI
npm install -g @render/cli

# Login to Render
render login

# Deploy using render.yaml
render deploy
```

### 2. Railway

Railway provides simple deployments with automatic scaling.

#### Setup Steps

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set FLASK_ENV=production
   railway variables set SECRET_KEY=your_super_secret_key_here_min_32_chars
   railway variables set FLUTTER_API_KEY=sabda_flutter_2025_secure_key
   railway variables set MOBILE_API_KEY=sabda_mobile_2025_secure_key
   ```

4. **Custom Domain (Optional)**
   ```bash
   railway domain add your-domain.com
   ```

### 3. Heroku

Classic platform with extensive documentation and add-ons.

#### Setup Steps

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Or download from heroku.com
   ```

2. **Create and Deploy**
   ```bash
   heroku login
   heroku create sabda-scraper-api
   
   # Set environment variables
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your_super_secret_key_here_min_32_chars
   heroku config:set FLUTTER_API_KEY=sabda_flutter_2025_secure_key
   heroku config:set MOBILE_API_KEY=sabda_mobile_2025_secure_key
   
   # Deploy
   git push heroku main
   ```

3. **Scale Dynos**
   ```bash
   heroku ps:scale web=1
   ```

### 4. Docker Deployment

For containerized deployments on any platform supporting Docker.

#### Build and Run Locally

```bash
# Build image
docker build -t sabda-scraper-api .

# Run container
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your_super_secret_key_here_min_32_chars \
  -e FLUTTER_API_KEY=sabda_flutter_2025_secure_key \
  -e MOBILE_API_KEY=sabda_mobile_2025_secure_key \
  sabda-scraper-api
```

#### Deploy to Cloud Platforms

**Google Cloud Run:**
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/sabda-scraper-api

# Deploy to Cloud Run
gcloud run deploy sabda-scraper-api \
  --image gcr.io/PROJECT_ID/sabda-scraper-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**AWS ECS/Fargate:**
```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag sabda-scraper-api:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/sabda-scraper-api:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/sabda-scraper-api:latest
```

### 5. DigitalOcean App Platform

Simple deployment with automatic scaling and monitoring.

#### Setup Steps

1. **Create App**
   - Go to DigitalOcean Control Panel
   - Click "Create" → "Apps"
   - Connect your GitHub repository

2. **Configure App**
   - **Name:** `sabda-scraper-api`
   - **Source:** Your repository
   - **Branch:** `main`
   - **Autodeploy:** Enabled

3. **Environment Variables**
   ```
   FLASK_ENV=production
   SECRET_KEY=your_super_secret_key_here_min_32_chars
   FLUTTER_API_KEY=sabda_flutter_2025_secure_key
   MOBILE_API_KEY=sabda_mobile_2025_secure_key
   ```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | JWT signing key (32+ chars) | `your_super_secret_key_here_min_32_chars` |
| `FLUTTER_API_KEY` | API key for Flutter apps | `sabda_flutter_2025_secure_key` |
| `MOBILE_API_KEY` | API key for mobile apps | `sabda_mobile_2025_secure_key` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `5000` |
| `SCRAPER_DELAY_MIN` | Min delay between requests | `1` |
| `SCRAPER_DELAY_MAX` | Max delay between requests | `3` |

### Generating Secure Keys

```bash
# Generate SECRET_KEY (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate SECRET_KEY (OpenSSL)
openssl rand -base64 32

# Generate API keys
python -c "import secrets; print('sabda_' + secrets.token_urlsafe(16))"
```

## Custom Domain Setup

### Render
1. Go to your service dashboard
2. Click "Settings" → "Custom Domains"
3. Add your domain and configure DNS

### Railway
```bash
railway domain add your-domain.com
```

### Heroku
```bash
heroku domains:add your-domain.com
```

## SSL/HTTPS

All recommended platforms provide automatic SSL certificates:
- **Render:** Automatic Let's Encrypt certificates
- **Railway:** Automatic SSL for custom domains
- **Heroku:** Automatic SSL with paid dynos
- **DigitalOcean:** Automatic SSL certificates

For API support, issues, or feature requests:
- **GitHub:** https://github.com/sabda-scraper/api
- **Email:** sabda-api@support.com
- **Documentation:** https://sabda-scrapper.onrender.com/docs

## Monitoring and Logging

### Health Checks

All platforms can monitor the `/api/health` endpoint:

**Render:**
- Automatic health checks on `/api/health`
- Configurable in `render.yaml`

**Railway:**
- Built-in health monitoring
- Custom health check paths supported

**Heroku:**
- Add health check in app.json or dashboard

### Logging

Access logs through platform dashboards:

```bash
# Render
render logs --service-id YOUR_SERVICE_ID

# Railway
railway logs

# Heroku
heroku logs --tail
```

## Performance Optimization

### Scaling

**Horizontal Scaling:**
- Render: Auto-scaling available on paid plans
- Railway: Auto-scaling with usage-based pricing
- Heroku: Manual or auto-scaling dynos

**Vertical Scaling:**
- Increase memory/CPU allocation in platform settings

### Caching

Consider adding Redis for caching scraped content:

```python
# Add to requirements.txt
redis==4.5.1

# Environment variable
REDIS_URL=redis://localhost:6379
```

### Rate Limiting

Implement rate limiting for production:

```python
# Add to requirements.txt
flask-limiter==3.1.0

# In app configuration
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## Troubleshooting

### Common Issues

**Build Failures:**
- Check Python version compatibility
- Verify requirements.txt syntax
- Ensure all dependencies are available

**Runtime Errors:**
- Check environment variables are set
- Verify SECRET_KEY length (32+ characters)
- Check application logs for specific errors

**Scraping Issues:**
- SABDA.org may block requests from cloud IPs
- Consider using proxy services
- Implement retry logic with exponential backoff

### Debug Commands

```bash
# Check environment variables
env | grep FLASK

# Test locally with production settings
FLASK_ENV=production python run.py

# Validate requirements
pip check

# Test API endpoints
curl https://sabda-scrapper.onrender.com/api/health
```

## Security Checklist

- [ ] Environment variables configured securely
- [ ] SECRET_KEY is 32+ characters and random
- [ ] API keys are unique and complex
- [ ] HTTPS enabled (automatic on most platforms)
- [ ] CORS configured appropriately
- [ ] Rate limiting implemented
- [ ] Error messages don't expose sensitive information
- [ ] Logs don't contain secrets

## Backup and Recovery

### Database Backup
If you add a database later:
- Enable automatic backups on your platform
- Test restore procedures regularly

### Code Backup
- Keep code in version control (Git)
- Tag releases for easy rollback
- Document deployment procedures

## Cost Optimization

### Free Tier Limits

**Render:** 750 hours/month, sleeps after 15 minutes of inactivity
**Railway:** $5 credit monthly, usage-based pricing
**Heroku:** 550-1000 dyno hours/month (with verification)

### Optimization Tips

1. **Use free tiers for development/testing**
2. **Scale down during low usage periods**
3. **Monitor usage dashboards regularly**
4. **Consider serverless options for sporadic usage**

## Next Steps

After successful deployment:

1. **Test all endpoints** with production URLs
2. **Update Flutter app** with production API URL
3. **Monitor performance** and error rates
4. **Set up alerts** for downtime or errors
5. **Document API usage** for your team
6. **Plan for scaling** as usage grows

## Support

For deployment issues:
- Check platform documentation
- Review application logs
- Test locally with production settings
- Contact platform support if needed
