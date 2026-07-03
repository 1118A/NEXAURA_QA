import sys
import os

# Ensure the project root is in the path so 'app' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app

# Create the Flask app instance — Vercel uses this as the WSGI handler
app = create_app()

# Vercel expects a variable named 'app' (WSGI callable)
