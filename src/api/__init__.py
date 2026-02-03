"""
FastAPI Layer - REST API endpoints for Fast6

This module provides the FastAPI REST API that runs on port 8000.
The FastAPI server is completely separate from the Streamlit UI (port 8501)
and can be developed/deployed independently.

Main Application:
    src.api.fastapi_app: FastAPI application entry point

Configuration:
    src.api.fastapi_config: Settings and environment management
    src.api.fastapi_security: JWT and password utilities
    src.api.fastapi_models: Pydantic request/response schemas
    src.api.fastapi_dependencies: Dependency injection for auth/db

Routers:
    src.api.routers.fastapi_auth: Authentication endpoints
    src.api.routers.fastapi_users: User management endpoints

To run the API:
    uvicorn src.api.fastapi_app:app --reload
"""
