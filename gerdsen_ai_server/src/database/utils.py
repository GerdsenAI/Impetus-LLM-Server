#!/usr/bin/env python3
"""
Database utility functions for the GerdsenAI application.
"""

from .models import db

def init_db(app):
    """
    Initializes the database and creates all tables.
    """
    with app.app_context():
        db.create_all()
