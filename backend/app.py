from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Security
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import sqlite3
import requests
import os
from fastapi_sso.sso.google import GoogleSSO
from jose import JWTError, jwt
from fastapi.security import APIKeyCookie
import httpx

app = FastAPI()

# CORS configuration
origins = ["*"]  # Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security settings
JWT_SECRET_KEY = os.environ.get("JWT_SECRET", "supersecretkey")  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_KEY_COOKIE = APIKeyCookie(name="token")

# Database settings
DB_FILE = "database.db"
PRIVATE_SERVER = "http://192.168.1.137:15678"  # Change this to your private server IP

# Google SSO settings
CLIENT_ID = os.environ.get("ID_CLIENTE")
CLIENT_SECRET = os.environ.get("SECRETO_CLIENTE")
GOOGLE_CALLBACK_URL = "https://app.opoai.es:5000/google/callback"

google_sso = GoogleSSO(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=GOOGLE_CALLBACK_URL)

# --- Database Functions ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user(db, email: str):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cursor.fetchone()

def create_user(db, email: str, role: str):
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (email, role) VALUES (?, ?)", (email, role))
    db.commit()
    return get_user(db, email)

def update_user_role(db, email: str, role: str):
    cursor = db.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
    db.commit()
    return get_user(db, email)

# --- Initialize database ---
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            role TEXT NOT NULL
        )
    """)
    conn.commit()

    # Create admin user if not exists
    if not get_user(conn, "juansebasmontes@gmail.com"):
        create_user(conn, "juansebasmontes@gmail.com", "admin")
    conn.close()

init_db()

# --- Security Functions ---
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Security(API_KEY_COOKIE)):
    """Get user's JWT stored in cookie 'token', parse it and return the user's OpenID."""
    try:
        payload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials") from error

async def get_current_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    return user

# --- Google SSO Endpoints ---
@app.get("/google/login")
async def google_login():
    return await google_sso.get_login_redirect()

@app.get("/google/callback")
async def google_callback(request: Request):
    try:
        user = await google_sso.verify_and_process(request)
        email = user.email

        # Connect to the database
        db = get_db_connection()

        # Check if the user already exists
        existing_user = get_user(db, email)

        if not existing_user:
            # Create the user with default role "user"
            create_user(db, email, "user")
        
        role = get_user(db, email)["role"]
        db.close()

        # Create access token
        access_token = create_access_token(data={"sub": email, "role": role})
        response= RedirectResponse(url="https://app.opoai.es:3434/auth-callback", status_code=302)
        # Set cookie
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=True, # set to True in production
        )

        print(access_token)

        # Redirect to protected endpoint
        return RedirectResponse(url="https://app.opoai.es:3434/auth-callback", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- Check Auth Endpoint ---
@app.get("/check-auth")
async def check_auth(current_user: dict = Depends(get_current_user)):
    return JSONResponse({
        "email": current_user["sub"],
        "role": current_user["role"]
    })

# --- Temas Endpoint ---
@app.get("/temas")
async def get_temas(current_user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post("https://192.168.1.137:5678/webhook/temas")
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not connect to the private server: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Private server returned an error: {e}")

# --- Change Role Endpoint ---
@app.post("/change_role")
async def change_role(email: str, role: str, current_user: dict = Depends(get_current_admin)):
    # Connect to the database
    db = get_db_connection()

    # Update the user's role
    updated_user = update_user_role(db, email, role)
    db.close()

    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": f"Role for user {email} updated to {role}"}
