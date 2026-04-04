from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
import json
import uuid
from passlib.hash import pbkdf2_sha256

router = APIRouter(prefix="/api/auth")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
USERS_DIR = os.path.join(DATA_DIR, "users")

# Ensure user management directory exists
os.makedirs(USERS_DIR, exist_ok=True)

# -----------------
# Pydantic Models
# -----------------
class UserBase(BaseModel):
    name: str
    email: str
    role: str = "Candidate"
    company: str = ""

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# -----------------
# Endpoints
# -----------------

@router.post("/signup")
async def signup(user: UserCreate):
    email_filename = f"{user.email.replace('@', '_').replace('.', '_')}.json"
    file_path = os.path.join(USERS_DIR, email_filename)
    
    if os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_data = user.dict()
    user_data["id"] = str(uuid.uuid4())
    # Hash password (secure storage)
    user_data["password_hash"] = pbkdf2_sha256.hash(user.password)
    del user_data["password"]
    
    with open(file_path, "w") as f:
        json.dump(user_data, f, indent=2)
    
    return {"status": "success", "user": {
        "id": user_data["id"],
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "company": user.company
    }}

@router.post("/signin")
async def signin(login: UserLogin):
    email_filename = f"{login.email.replace('@', '_').replace('.', '_')}.json"
    file_path = os.path.join(USERS_DIR, email_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Email not found")
    
    with open(file_path, "r") as f:
        user_data = json.load(f)
    
    if not pbkdf2_sha256.verify(login.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Auto-generate ID for legacy users
    if "id" not in user_data:
        user_data["id"] = str(uuid.uuid4())
        with open(file_path, "w") as f:
            json.dump(user_data, f, indent=2)

    # Return user details without the hash
    return {
        "status": "success",
        "user": {
            "id": user_data["id"],
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data["role"],
            "company": user_data.get("company", "")
        }
    }

# -----------------
# Admin Seeding
# -----------------
def seed_admin():
    admin_email = "admin@platform.ai"
    email_filename = f"{admin_email.replace('@', '_').replace('.', '_')}.json"
    file_path = os.path.join(USERS_DIR, email_filename)
    
    if not os.path.exists(file_path):
        admin_user = {
            "name": "Super Admin",
            "email": admin_email,
            "role": "Admin",
            "company": "System Core",
            "password_hash": pbkdf2_sha256.hash("admin123")
        }
        with open(file_path, "w") as f:
            json.dump(admin_user, f, indent=2)
        print(f"[AUTH] Admin account created: {admin_email} / admin123")

seed_admin()
