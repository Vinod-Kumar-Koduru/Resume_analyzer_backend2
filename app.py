from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

from routes import resume_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.register_blueprint(resume_bp, url_prefix='/api/resumes')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)