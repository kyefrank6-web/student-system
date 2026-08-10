"""WSGI entry point for production servers (gunicorn, waitress, etc.)."""

from app import app

if __name__ == "__main__":
    app.run()
