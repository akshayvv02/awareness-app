from flask import Flask
from app.routes import api  # Import the blueprint
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from .tasks import call_endpoint  # Importing the function
from flask_cors import CORS

scheduler = None  # Global variable to hold the scheduler

def create_app():
    global scheduler
    logging.info('-- app called now --')
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Configuration settings for the app
    app.config['MYSQL_HOST'] = 'mysql'
    app.config['MYSQL_USER'] = 'myuser'
    app.config['MYSQL_PASSWORD'] = 'mypassword'
    app.config['MYSQL_DB'] = 'mydatabase'

    
    # Register the routes blueprint
    app.register_blueprint(api)

    # Initialize the scheduler only if it's not already initialized
    if scheduler is None:
        logging.info('--------- Initializing scheduler ---------')
        scheduler = BackgroundScheduler()
        scheduler.add_job(call_endpoint, 'interval', seconds=3600)  # Adjust the interval as needed
        scheduler.start()
        logging.info('---------- Scheduler Set now ----------')
        
    return app

if __name__ == '__main__':
    logging.info('-- app started --')
    logging.info('-- calling create app --')
    app = create_app()
    try:
        app.run(host='0.0.0.0', port=5001)  # Disable debug mode
    finally:
        if scheduler is not None:
            scheduler.shutdown()
