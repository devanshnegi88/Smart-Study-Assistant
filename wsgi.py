"""WSGI entrypoint for Railway/production.

Gunicorn will import `app` from this module.
"""

from app import create_app

app = create_app()

