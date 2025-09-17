"""
Entry point for the WhatsApp Sentinel application
"""

import uvicorn
from src.utils import check_environment
from src.core.config import settings

def main():
    # Validate environment
    if not check_environment():
        print("Environment validation failed. Please check your .env file.")
        return
    
    # Run the application
    uvicorn.run(
        "src.core.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload for development
    )

if __name__ == "__main__":
    main()
