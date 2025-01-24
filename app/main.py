from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.api.v1.products import router as products_router
from app.core.scheduler import start_scheduler
from app.core.db import Base
import asyncio

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def fake_decode_token(token: str):
    if token == "secrettoken":
        return {"sub": "authorized_user"}
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    return fake_decode_token(token)

# Initialize FastAPI application
app = FastAPI(title="My FastAPI App")

# Include router with dependency injection for authentication
app.include_router(
    products_router,
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(get_current_user)]
)

@app.on_event("startup")
async def startup_event():
    print("Starting scheduler...")
    asyncio.create_task(start_scheduler())
    print("Scheduler started successfully!")

@app.get("/")
async def root():
    return {"message": "Welcome to the API!"}
