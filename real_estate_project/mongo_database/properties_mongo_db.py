from pymongo import MongoClient
from schema_validation import properties_validation_rules, saved_search_schema
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["aruodas_apartments"]
collection_name = "properties"
collection = db[collection_name]
dblist = client.list_database_names()

# Apply schema validation
existing_collections = db.list_collection_names()
if collection_name in existing_collections:
    db.command(
        "collMod",
        collection_name,
        validator= properties_validation_rules
    )
    print(f"Schema validation applied to existing collection '{collection_name}'.")
else:
    db.create_collection(
        collection_name,
        validator= properties_validation_rules
    )
    print(f"Collection '{collection_name}' created with schema validation.")

def save_property(property_data):
    #Insert or update property by URL.
    collection.update_one(
        {"url": property_data["url"]},
        {"$set": property_data},
        upsert=True
    )

#Saved searches
saved_search_collection_name = "saved_searches"
saved_search_collection = db[saved_search_collection_name]

if saved_search_collection_name in existing_collections:
    db.command(
        "collMod",
        saved_search_collection_name,
        validator= saved_search_schema
    )
    print(f"Schema validation applied to existing collection '{saved_search_collection_name}'.")
else:
    db.create_collection(
        saved_search_collection_name,
        validator= saved_search_schema
    )
    print(f"Collection '{saved_search_collection_name}' created with schema validation.")

def save_search(user_id, name, query):
    saved_search_collection.update_one(
        {"user_id": user_id, "name": name},
        {"$set": {
            "query": query,
            "timestamp": datetime.utcnow()
        }},
        upsert=True
    )
