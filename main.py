from app import app
from auth import auth_bp
import routes
import api
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints with unique names
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == "__main__":
    try:
        # Get required API keys from environment
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        openweathermap_api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
        flask_secret_key = os.environ.get('FLASK_SECRET_KEY')
        
        if not all([openai_api_key, openweathermap_api_key, flask_secret_key]):
            logger.error("Required API keys not configured!")
            missing_keys = []
            if not openai_api_key:
                missing_keys.append('OPENAI_API_KEY')
            if not openweathermap_api_key:
                missing_keys.append('OPENWEATHERMAP_API_KEY')
            if not flask_secret_key:
                missing_keys.append('FLASK_SECRET_KEY')
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
        
        # Configure Flask app
        app.config['OPENAI_API_KEY'] = openai_api_key
        app.config['OPENWEATHERMAP_API_KEY'] = openweathermap_api_key
        
        # Get port from environment or default to 5000
        port = int(os.environ.get('PORT', 5000))
        
        # Set debug mode based on environment
        debug_mode = os.environ.get('FLASK_ENV') != 'production'
        
        logger.info(f"Starting Flask server in {'production' if not debug_mode else 'development'} mode...")
        app.run(host="0.0.0.0", port=port, debug=debug_mode)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise
