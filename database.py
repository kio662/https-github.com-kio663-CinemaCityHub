from datetime import datetime
from pymongo import MongoClient, TEXT, DESCENDING
from config import MONGO_URI

client     = MongoClient(MONGO_URI)
db         = client["cinemacityhub"]
files_col  = db["files"]
users_col  = db["users"]
banned_col = db["banned"]
req_col    = db["requests"]
stats_col  = db["stats"]

# ── Indexes ───────────────────────────────────────────────────────────────────
files_col.create_index([("file_name_lower", TEXT)])
files_col.create_index([("language", 1)])
files_col.create_index([("quality", 1)])
users_col.create_index([("user_id", 1)], unique=True)
banned_col.create_index([("user_id", 1)], unique=True)
req_col.create_index([("user_id", 1)])


# ─────────────────────────────────────────────────────────────────────────────
# FILE OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def save_file(file_id, file_name, file_unique_id, language="unknown", quality="unknown"):
    if files_col.find_one({"file_unique_id": file_unique_id}):
        return False
    files_col.insert_one({
        "file_id":         file_id,
        "file_name":       file_name,
        "file_name_lower": file_name.lower(),
        "file_unique_id":  file_unique_id,
        "language":        language.lower(),
        "quality":         quality.lower(),
        "added_on":        datetime.utcnow(),
        "downloads":       0,
    })
    return True


def search_files(movie_name: str, language: str = None, quality: str = None):
    query = {"file_name_lower": {"$regex": movie_name.lower(), "$options": "i"}}
    if language and language.lower() != "all":
        query["language"] = {"$regex": language.lower(), "$options": "i"}
    if quality and quality.lower() != "all":
        query["quality"] = quality.lower()
    from config import MAX_RESULTS
    return list(files_col.find(query).limit(MAX_RESULTS))


def get_languages(movie_name: str):
    results = files_col.find({"file_name_lower": {"$regex": movie_name.lower(), "$options": "i"}})
    return sorted(set(r.get("language", "unknown") for r in results))


def increment_download(file_unique_id: str):
    files_col.update_one({"file_unique_id": file_unique_id}, {"$inc": {"downloads": 1}})


def get_total_files():
    return files_col.count_documents({})


def get_recent_files(limit=5):
    return list(files_col.find().sort("added_on", DESCENDING).limit(limit))


def delete_file_by_id(file_unique_id: str):
    files_col.delete_one({"file_unique_id": file_unique_id})


def delete_all_files():
    files_col.delete_many({})


# ─────────────────────────────────────────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def save_user(user_id: int, first_name: str, username: str = None):
    users_col.update_one(
        {"user_id": user_id},
        {"$set":  {"first_name": first_name, "username": username},
         "$setOnInsert": {"joined_on": datetime.utcnow(), "user_id": user_id}},
        upsert=True
    )


def get_total_users():
    return users_col.count_documents({})


def get_all_user_ids():
    return [u["user_id"] for u in users_col.find({}, {"user_id": 1})]


def get_recent_users(limit=5):
    return list(users_col.find().sort("joined_on", DESCENDING).limit(limit))


# ─────────────────────────────────────────────────────────────────────────────
# BAN / UNBAN
# ─────────────────────────────────────────────────────────────────────────────

def ban_user(user_id: int, reason: str = "No reason"):
    banned_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "reason": reason, "banned_on": datetime.utcnow()}},
        upsert=True
    )


def unban_user(user_id: int):
    banned_col.delete_one({"user_id": user_id})


def is_banned(user_id: int) -> bool:
    return banned_col.find_one({"user_id": user_id}) is not None


def get_all_banned():
    return list(banned_col.find())


# ─────────────────────────────────────────────────────────────────────────────
# MOVIE REQUESTS
# ─────────────────────────────────────────────────────────────────────────────

def add_request(user_id: int, username: str, movie_name: str):
    req_col.insert_one({
        "user_id":    user_id,
        "username":   username,
        "movie_name": movie_name,
        "status":     "pending",
        "requested_on": datetime.utcnow(),
    })


def get_pending_requests():
    return list(req_col.find({"status": "pending"}).sort("requested_on", DESCENDING))


def get_user_requests(user_id: int):
    return list(req_col.find({"user_id": user_id}).sort("requested_on", DESCENDING).limit(5))


def update_request_status(request_id, status: str):
    from bson import ObjectId
    req_col.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": status}})


# ─────────────────────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────────────────────

def log_search(movie_name: str):
    stats_col.update_one(
        {"movie_name": movie_name.lower()},
        {"$inc": {"count": 1}, "$set": {"last_searched": datetime.utcnow()}},
        upsert=True
    )


def get_top_searches(limit=10):
    return list(stats_col.find().sort("count", DESCENDING).limit(limit))
