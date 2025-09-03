#!/usr/bin/env python3
"""
SABDA Scraper API - Entry Point
"""
import os
from app import create_app
from app.config import config

# Get configuration from environment
config_name = os.environ.get('FLASK_ENV', 'default')
app = create_app(config[config_name])

def main():
    """Main application entry point"""
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
