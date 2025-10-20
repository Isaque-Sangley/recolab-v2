"""
Serving Package

Model serving layer para production.
"""

from .model_server import ModelServer

__all__ = [
    'ModelServer',
]