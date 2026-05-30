# from flask import Flask, jsonify
# from pymongo import MongoClient
# from urllib.parse import quote_plus

# app = Flask(__name__)

# username = 'devanshn180_db_user'
# password = quote_plus('test1234')  # Encode if necessary

# MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.njdxavv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# client = MongoClient(MONGO_URI)

# # Replace with actual names from your Atlas
# db = client['devanshn180_db_user']          # Exact database name
# collection = db['users']    # Exact collection name

# @app.route('/')
# def index():
#     try:
#         sample_data = collection.insert_one({"name": "Test User"})
#         inserted_doc = collection.find_one({'name': "Test User"})

#         # Convert ObjectId to string for JSON serialization
#         inserted_doc['_id'] = str(inserted_doc['_id'])

#         return jsonify(inserted_doc)
#         return jsonify(sample_data)
#     except Exception as e:
#         return jsonify({"error": str(e)})

# if __name__ == '__main__':
#     app.run(debug=True)
