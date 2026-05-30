from dotenv import load_dotenv
import os
from app import create_app
# from waitress import serve

# Load environment variables — use explicit path so CWD doesn't matter
_env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_env_path, override=True)

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

# from dotenv import load_dotenv
# import os
# from app import create_app
# # from waitress import serve

# # Load environment variables from .env file
# load_dotenv()

# app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True)

# # Gunicorn entry point for Render deployment
# # if __name__ == "__main__":
# #     serve(app, host="0.0.0.0", port=5000)

