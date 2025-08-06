import uvicorn
from app.router import app

uvicorn.run(app, host="127.0.0.1", port=8000)