"""
FastAPI Layer - REST API endpoints for Fast6

This module provides the FastAPI REST API that runs on port 8000.
The FastAPI server is completely separate from the Streamlit UI (port 8501)
and can be developed/deployed independently.

Main Application:
    backend.api.fastapi_app: FastAPI application entry point

Configuration:
    backend.api.fastapi_config: Settings and environment management
    backend.api.fastapi_security: JWT and password utilities
    backend.api.fastapi_models: Pydantic request/response schemas
    backend.api.fastapi_dependencies: Dependency injection for auth/db

Routers:
    backend.api.routers.fastapi_auth: Authentication endpoints
    backend.api.routers.fastapi_users: User management endpoints

To run the API:
    uvicorn backend.api.fastapi_app:app --reload
"""
