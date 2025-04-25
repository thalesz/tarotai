from datetime import datetime
from fastapi import HTTPException, Request
from jose import JWTError, jwt, ExpiredSignatureError
from app.core.configs import settings
from app.services.token import TokenAccessSchema, TokenInfoSchema

# Token configurations
SECRET_KEY = settings.ACCESS_SECRET_KEY
ALGORITHM = settings.ALGORITHM


# Function to extract the token from the Authorization header
def get_token_from_header(request: Request) -> str:
    token = request.headers.get("Authorization")
    # print(f"Authorization header: {token}")  # Debugging line to check the token
    if token is None:
        raise HTTPException(status_code=401, detail="Authentication token missing")
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Malformed token")
    return token.split("Bearer ")[1]  # Remove the 'Bearer ' prefix and return the token


# Function to verify the JWT token
def verify_jwt(request: Request):
    try:
        # Extract the token from the Authorization header of the request
        token = get_token_from_header(request)

        # Decode the token payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(
            f"Decoded payload: {payload}"
        )  # Debugging line to check the decoded payload

        # Check the token expiration
        exp_time = datetime.fromtimestamp(payload.get("exp", 0))
        if datetime.now() > exp_time:
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Store the information in request.state
        token_info = TokenInfoSchema(
            **payload
        )  # Populate TokenInfoSchema with all attributes from the payload

        request.state.token_info = (
            token_info  # Save the information globally in the request
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
