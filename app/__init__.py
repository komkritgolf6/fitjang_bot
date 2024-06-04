from flask import Flask
from config import Config
from .models import db
from .api import bp as api_bp
import redis


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(api_bp)
    

    return app
