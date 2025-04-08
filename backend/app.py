from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
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
DB_FILE = "database.db"
PRIVATE_SERVER = "http://192.168.1.137:15678"  # Change this to your private server IP

# Bcrypt context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Google SSO settings
CLIENT_ID = os.environ.get("ID_CLIENTE")
CLIENT_SECRET = os.environ.get("SECRETO_CLIENTE")
GOOGLE_CALLBACK_URL = "https://app.opoai.es:5000/google/callback"

google_sso = GoogleSSO(CLIENT_ID, CLIENT_SECRET, GOOGLE_CALLBACK_URL)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    conn.commit()

    # Create default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        hashed_password = pwd_context.hash("admin123")
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hashed_password, "admin"))
        conn.commit()
    conn.close()

init_db()

# --- Google SSO Endpoints ---
@app.get("/google/login")
async def google_login():
    return await google_sso.get_login_redirect()

@app.get("/google/callback")
async def google_callback(request: Request):
    try:
        user = await google_sso.verify_and_process(request)
        # Here you should create or update user in your database
        # and then create a session for the user
        # For now, just return the user info
        return JSONResponse(user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- Authentication ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # You might want to fetch user details from the database here
        return {"username": username, "role": payload.get("role", "user")}
    except JWTError:
        raise credentials_exception

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    user = cursor.fetchone()
    conn.close()

    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Registration ---
@app.post("/register")
async def register(username: str, password: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    hashed_password = pwd_context.hash(password)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, hashed_password, "user"))
        conn.commit()
        conn.close()
        return JSONResponse({"message": "User registered successfully"}, status_code=status.HTTP_201_CREATED)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

# --- Proxy Endpoint ---
@app.get("/proxy")
async def proxy(current_user: dict = Depends(get_current_user)):
    print(f"Authenticated user: {current_user['username']} is accessing the private server.")
    try:
        response = requests.get(PRIVATE_SERVER)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except requests.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not connect to the private server: {e}")
