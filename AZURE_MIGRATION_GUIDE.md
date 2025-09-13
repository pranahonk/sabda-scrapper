# Azure Migration Guide

This guide will help you migrate your SABDA Scraper from Render to Azure App Service.

## Prerequisites

1. **Azure CLI**: Install if not already available
   ```bash
   # macOS
   brew install azure-cli
   
   # Windows
   winget install Microsoft.AzureCLI
   ```

2. **Azure Account**: Ensure you have an active Azure subscription

## Migration Options

### Option 1: Quick Deployment (Recommended)

Use the automated deployment script:

```bash
# Make the script executable
chmod +x deploy-azure.sh

# Edit the script to add your subscription ID (optional)
# Then run the deployment
./deploy-azure.sh
```

### Option 2: Manual Azure CLI Deployment

1. **Login to Azure**:
   ```bash
   az login
   ```

2. **Create Resource Group**:
   ```bash
   az group create --name rg-sabda-scraper --location "Southeast Asia"
   ```

3. **Deploy Infrastructure**:
   ```bash
   az deployment group create \
     --resource-group rg-sabda-scraper \
     --template-file bicep/main.bicep \
     --parameters webAppName=sabda-scraper-go
   ```

4. **Build and Deploy App**:
   ```bash
   go build -o bin/server ./cmd/server
   zip -r deployment.zip bin/
   
   az webapp deployment source config-zip \
     --resource-group rg-sabda-scraper \
     --name sabda-scraper-go \
     --src deployment.zip
   ```

### Option 3: GitHub Actions CI/CD

1. **Set up Azure Service Principal**:
   ```bash
   az ad sp create-for-rbac --name "sabda-scraper-sp" \
     --role contributor \
     --scopes /subscriptions/{subscription-id}/resourceGroups/rg-sabda-scraper \
     --sdk-auth
   ```

2. **Add GitHub Secret**:
   - Go to your GitHub repository settings
   - Add a secret named `AZURE_CREDENTIALS`
   - Paste the JSON output from step 1

3. **Push to main branch** - the workflow will automatically deploy

## Environment Variables Migration

Your current Render environment variables will be automatically configured in Azure:

| Render Variable | Azure App Setting | Notes |
|----------------|-------------------|-------|
| `PORT` | `PORT` | Changed to 8080 (Azure default) |
| `SECRET_KEY` | `SECRET_KEY` | Auto-generated in Azure |

## Key Differences from Render

### Advantages of Azure App Service:
- **Better Monitoring**: Built-in Application Insights
- **Scaling**: Auto-scaling capabilities
- **Security**: Managed certificates, Azure AD integration
- **Networking**: VNet integration, private endpoints
- **Backup**: Automatic backups and restore points

### Configuration Changes:
- **Port**: Azure uses port 8080 by default (configurable)
- **Health Check**: Same endpoint `/api/health`
- **Startup Command**: `./bin/server` (same as Render)

## Post-Migration Steps

1. **Update DNS**: Point your domain to the new Azure URL
2. **Test Endpoints**: Verify all API endpoints work correctly
3. **Monitor**: Set up alerts in Application Insights
4. **Scale**: Configure auto-scaling rules if needed

## Costs Comparison

| Service | Render | Azure App Service B1 |
|---------|--------|---------------------|
| Monthly Cost | ~$7/month | ~$13/month |
| CPU | 0.5 CPU | 1 CPU |
| RAM | 512MB | 1.75GB |
| Storage | 1GB | 10GB |
| Bandwidth | 100GB | Unlimited |

## Rollback Plan

If you need to rollback to Render:
1. Keep your Render service running during migration
2. Test Azure thoroughly before DNS switch
3. Use the same environment variables
4. Monitor both services during transition

## Final Status - Azure for Students Limitations Encountered

**IMPORTANT:** The Azure for Students subscription has multiple limitations that prevent successful deployment:

### Issues Encountered:
1. ✅ **Regional Restrictions** - Resolved by using Indonesia Central
2. ✅ **Microsoft.Web Provider** - Successfully registered
3. ✅ **App Service Creation** - Successfully created in Indonesia Central
4. ❌ **Quota Exceeded** - The subscription hit resource quotas (state: QuotaExceeded)

### Azure for Students Limitations Summary:
- **Compute Quotas:** Limited vCPU hours and instances
- **Regional Restrictions:** Many regions blocked for App Service
- **Service Limitations:** Some Azure services not available
- **Resource Limits:** Storage, bandwidth, and compute quotas

### Recommended Alternative: Railway Deployment

Since Azure for Students has proven unreliable for production deployment, **Railway** is recommended as the primary deployment platform:

**Advantages of Railway:**
- ✅ No regional restrictions
- ✅ Simple Go application deployment
- ✅ Generous free tier (500 hours/month)
- ✅ Automatic HTTPS and custom domains
- ✅ Built-in monitoring and logs
- ✅ Easy environment variable management

### Next Steps
1. Deploy to Railway using the provided script: `./railway-deploy.sh`
2. Alternative: Deploy to Fly.io using: `./fly-deploy.sh`
3. Keep Render deployment as backup option

## Support

- **Railway Documentation**: https://docs.railway.app/
- **Fly.io Documentation**: https://fly.io/docs/
- **Azure Documentation**: https://docs.microsoft.com/en-us/azure/app-service/
- **Troubleshooting**: Check deployment logs in respective platform dashboards
