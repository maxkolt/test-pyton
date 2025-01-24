from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.api.v1.products import router as products_router
from app.core.scheduler import start_scheduler
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

app = FastAPI()

app.include_router(products_router, dependencies=[Depends(get_current_user)])

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_scheduler())