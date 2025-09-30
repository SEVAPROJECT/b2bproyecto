from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

class SignInIn(BaseModel):
    email: str
    password: str

@app.post("/test-login")
async def test_login(data: SignInIn):
    print(f"🔍 Test login recibido: {data.email}")
    
    token_data = {
        "access_token": "test_access_token_12345",
        "expires_in": 3600,
        "token_type": "bearer"
    }
    
    print(f"🔍 Enviando respuesta: {token_data}")
    return JSONResponse(content=token_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


