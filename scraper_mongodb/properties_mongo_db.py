from pymongo import MongoClient
from .schema_validation import properties_validation_rules, saved_search_schema
from datetime import datetime
from typing import Dict, Any


# Connect to MongoDB
client: MongoClient = MongoClient("mongodb://localhost:27017/")
db = client["aruodas_apartments"]

# Collection names
collection_name: str = "properties"
saved_search_collection_name: str = "saved_searches"

# Define collections
collection = db[collection_name]
saved_search_collection = db[saved_search_collection_name]

# Get existing collections
existing_collections = db.list_collection_names()

# Apply schema validation to 'properties' collection
if collection_name in existing_collections:
    db.command(
        "collMod",
        collection_name,
        validator=properties_validation_rules
    )
    print(f"Schema validation applied to existing collection '{collection_name}'.")
else:
    db.create_collection(
        collection_name,
        validator=properties_validation_rules
    )
    print(f"Collection '{collection_name}' created with schema validation.")


def save_property(property_data: Dict[str, Any]) -> None:
    """
    Insert or update a property in the MongoDB 'properties' collection based on the property's URL.

    Args:
        property_data (Dict[str, Any]): A dictionary containing property details.
                                        Must include a 'url' key.

    Returns:
        None
    """
    collection.update_one(
        {"url": property_data["url"]},
        {"$set": property_data},
        upsert=True
    )


# Apply schema validation to 'saved_searches' collection
if saved_search_collection_name in existing_collections:
    db.command(
        "collMod",
        saved_search_collection_name,
        validator=saved_search_schema
    )
    print(f"Schema validation applied to existing collection '{saved_search_collection_name}'.")
else:
    db.create_collection(
        saved_search_collection_name,
        validator=saved_search_schema
    )
    print(f"Collection '{saved_search_collection_name}' created with schema validation.")


def save_search(user_id: str, name: str, query: Dict[str, Any]) -> None:
    """
    Save or update a user's saved search in the MongoDB 'saved_searches' collection.

    Args:
        user_id (str): The ID of the user saving the search.
        name (str): The name given to the saved search.
        query (Dict[str, Any]): The query parameters used in the search.

    Returns:
        None
    """
    saved_search_collection.update_one(
        {"user_id": user_id, "name": name},
        {"$set": {
            "query": query,
            "timestamp": datetime.utcnow()
        }},
        upsert=True
    )