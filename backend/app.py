from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import sqlite3
import requests
import os
from fastapi_sso.sso.google import GoogleSSO

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

# Database settings
PRIVATE_SERVER = "http://192.168.1.137:15678"  # Change this to your private server IP

# Google SSO settings
CLIENT_ID = os.environ.get("ID_CLIENTE")
CLIENT_SECRET = os.environ.get("SECRETO_CLIENTE")
GOOGLE_CALLBACK_URL = "https://app.opoai.es:5000/google/callback"

google_sso = GoogleSSO(CLIENT_ID, CLIENT_SECRET, GOOGLE_CALLBACK_URL)

# --- Google SSO Endpoints ---
@app.get("/google/login")
async def google_login():
    return await google_sso.get_login_redirect()

@app.get("/google/callback")
async def google_callback(request: Request):
    try:
        user = await google_sso.verify_and_process(request)
        # Assign role based on email
        role = "user"
        if user.email == "juansebasmontes@gmail.com":
            role = "admin"

        # Return user info with role
        return JSONResponse({
            "id": user.id,
            "picture": user.picture,
            "display_name": user.display_name,
            "email": user.email,
            "provider": user.provider,
            "role": role
        })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- Proxy Endpoint ---
@app.get("/proxy")
async def proxy(current_user: dict):
    print(f"Authenticated user: {current_user['email']} is accessing the private server.")
    try:
        response = requests.get(PRIVATE_SERVER)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except requests.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not connect to the private server: {e}")
