from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from SEOLinkedInPoster import SEOLinkedInPoster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize the SEO LinkedIn Poster
poster = SEOLinkedInPoster(
    groq_api_key=os.getenv('GROQ_API_KEY'),
    linkedin_access_token=os.getenv('LINKEDIN_ACCESS_TOKEN')
)

def create_daily_post():
    """Function to create daily LinkedIn post"""
    try:
        logger.info("Starting daily post creation...")
        result = poster.create_seo_post(max_attempts=3)
        
        if result.get('success'):
            logger.info(f"Successfully created post with ID: {result.get('post_id')}")
        else:
            logger.error(f"Failed to create post: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in create_daily_post: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    create_daily_post,
    'cron',
    hour=10,  # Posts at 10 AM UTC
    minute=0
)

# Basic health check endpoint required by Render
@app.route('/')
def health_check():
    return 'Server is running', 200

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start()
    logger.info("Started background scheduler")
    
    # Run the server
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)