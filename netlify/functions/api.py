import sys
import os

# Ensure the project root is in the path so 'app' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from serverless_wsgi import handle_request

# Create the Flask app instance
app = create_app()

def handler(event, context):
    return handle_request(app, event, context)
