@description('The name of the web app')
param webAppName string = 'sabda-scraper-go'

@description('The location for all resources')
param location string = resourceGroup().location

@description('The SKU of the App Service Plan')
param appServicePlanSku string = 'B1'

@description('Environment variables for the app')
param environmentVariables object = {
  PORT: '8080'
  SECRET_KEY: newGuid()
  FLUTTER_API_KEY: 'sabda_flutter_2025_secure_key'
  MOBILE_API_KEY: 'sabda_mobile_2025_secure_key'
  JWT_EXPIRATION_HOURS: '24'
  CACHE_TTL: '3600'
  MAX_REQUESTS_PER_MINUTE: '60'
  ALLOWED_ORIGINS: '*'
  GO_DEBUG: 'false'
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${webAppName}-plan'
  location: location
  sku: {
    name: appServicePlanSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'GO|1.21'
      appCommandLine: './server'
      healthCheckPath: '/api/health'
      appSettings: [for key in items(environmentVariables): {
        name: key.key
        value: key.value
      }]
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
    }
    httpsOnly: true
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${webAppName}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
  }
}

// Configure App Insights for the web app
resource webAppAppSettings 'Microsoft.Web/sites/config@2022-03-01' = {
  parent: webApp
  name: 'appsettings'
  properties: union(environmentVariables, {
    APPINSIGHTS_INSTRUMENTATIONKEY: appInsights.properties.InstrumentationKey
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  })
}

output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
