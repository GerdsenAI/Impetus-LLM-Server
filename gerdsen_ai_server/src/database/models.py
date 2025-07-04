#!/usr/bin/env python3
"""
Database models for the GerdsenAI application.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Model(db.Model):
    """
    Represents an AI model in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    framework = db.Column(db.String(64), nullable=False)
    compute_device = db.Column(db.String(64), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    parameters = db.Column(db.Integer, nullable=False)
    quantization = db.Column(db.String(64), nullable=False)
    optimization_level = db.Column(db.String(64), nullable=False)
    apple_silicon_optimized = db.Column(db.Boolean, default=False)
    neural_engine_compatible = db.Column(db.Boolean, default=False)
    metal_accelerated = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, nullable=True)
    access_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        """
        Returns a dictionary representation of the model.
        """
        return {
            'id': self.id,
            'model_id': self.model_id,
            'name': self.name,
            'path': self.path,
            'framework': self.framework,
            'compute_device': self.compute_device,
            'size_bytes': self.size_bytes,
            'parameters': self.parameters,
            'quantization': self.quantization,
            'optimization_level': self.optimization_level,
            'apple_silicon_optimized': self.apple_silicon_optimized,
            'neural_engine_compatible': self.neural_engine_compatible,
            'metal_accelerated': self.metal_accelerated,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count
        }
