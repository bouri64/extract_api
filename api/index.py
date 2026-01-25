# api/index.py
from mangum import Mangum
from main import app  # or from app.main import app

handler = Mangum(app)