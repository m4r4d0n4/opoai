# backend/config/config.py
import os

class Config:
    SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
    DB_NAME = os.getenv("DB_NAME", "chatdb")
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASS = os.getenv("DB_PASS", "password")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("DB_PORT", "5432")
