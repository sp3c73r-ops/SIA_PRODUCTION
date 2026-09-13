from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.api import dashboard_router
from app.api.phase_router import router as phase_router
from app.api.document_router import router as document_router
from app.api.document_type_router import router as document_type_router
from app.api.circonscription_router import (
    router as circonscription_router,
)
from app.api.bureau_router import router as bureau_router
from app.api.movement_router import router as movement_router
from app.api.user_router import router as user_router
from app.api.auth_router import router as auth_router
from app.api.attachment_router import (
    router as attachment_router,
)
from app.api.document_field_router import (
    router as document_field_router,
)
from app.api.permission_request_router import (
    router as permission_request_router,
)
from app.api.notification_router import (
    router as notification_router,
)


bearer_scheme = HTTPBearer()


app = FastAPI(
    title="GED Archives API",
    version="1.0.0",
    description="API de Gestion Electronique des Documents",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)


# ==========================
# CORS
# ==========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# Routers
# ==========================

app.include_router(document_router)
app.include_router(document_type_router)
app.include_router(phase_router)
app.include_router(circonscription_router)
app.include_router(bureau_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(attachment_router)
app.include_router(document_field_router)
app.include_router(movement_router)
app.include_router(permission_request_router)
app.include_router(notification_router)
app.include_router(
    dashboard_router.router
)

# ==========================
# Routes système
# ==========================

@app.get("/")
def root():
    return {
        "message": "GED API"
    }


@app.get("/health")
def health():
    return {
        "status": "OK"
    }