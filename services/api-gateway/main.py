"""
API Gateway - Central entry point for all microservices.
Routes /api/user/* to User Service
Routes /api/loan/* to Loan Service
Handles authentication, rate limiting, and request orchestration.
Runs on port 8000.
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Loan Management System - API Gateway",
    description="Unified API Gateway for Microservices",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001/api/user")
LOAN_SERVICE_URL = os.getenv("LOAN_SERVICE_URL", "http://localhost:8002/api/loan")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "api-gateway-jwt-secret")


class ServiceProxy:
    """Proxy requests to microservices."""
    
    def __init__(self, service_url: str, service_name: str):
        self.service_url = service_url
        self.service_name = service_name
    
    async def request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        json_data: dict = None,
        params: dict = None,
    ) -> dict:
        """
        Make a request to the service and return response.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: Request path (without service URL)
            headers: Request headers
            json_data: Request JSON body
            params: Query parameters
        
        Returns:
            Response JSON
        
        Raises:
            HTTPException: If service is unavailable or request fails
        """
        url = f"{self.service_url}{path}"
        
        if headers is None:
            headers = {}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params
                )
                
                if response.status_code >= 500:
                    logger.error(f"{self.service_name} error: {response.text}")
                    raise HTTPException(
                        status_code=503,
                        detail=f"{self.service_name} is unavailable"
                    )
                
                try:
                    return response.json()
                except Exception:
                    return {"message": response.text, "status_code": response.status_code}
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to {self.service_name}")
            raise HTTPException(
                status_code=503,
                detail=f"{self.service_name} is unavailable (timeout)"
            )
        except Exception as e:
            logger.error(f"Error connecting to {self.service_name}: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Cannot reach {self.service_name}"
            )


user_service = ServiceProxy(USER_SERVICE_URL, "User Service")
loan_service = ServiceProxy(LOAN_SERVICE_URL, "Loan Service")


# ============ Health & Status ============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "api-gateway"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Loan Management System - API Gateway",
        "version": "1.0.0",
        "services": {
            "user": USER_SERVICE_URL,
            "loan": LOAN_SERVICE_URL
        }
    }


# ============ User Service Routes ============

@app.post("/api/user/signup")
async def user_signup(request: Request):
    """POST /api/user/signup - Register a new user."""
    data = await request.json()
    return await user_service.request("POST", "/signup/", json_data=data)


@app.post("/api/user/login")
async def user_login(request: Request):
    """POST /api/user/login - Authenticate user."""
    data = await request.json()
    return await user_service.request("POST", "/login/", json_data=data)


@app.get("/api/user/profile")
async def user_profile(authorization: Optional[str] = Header(None)):
    """GET /api/user/profile - Get user profile."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    headers = {"Authorization": authorization}
    return await user_service.request("GET", "/profile/", headers=headers)


@app.post("/api/user/create-admin")
async def create_admin(request: Request, authorization: Optional[str] = Header(None)):
    """POST /api/user/create-admin - Create admin (admin-only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    data = await request.json()
    headers = {"Authorization": authorization}
    return await user_service.request("POST", "/create-admin/", headers=headers, json_data=data)


@app.get("/api/user/list-agents")
async def list_agents(authorization: Optional[str] = Header(None)):
    """GET /api/user/list-agents - List customers."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    headers = {"Authorization": authorization}
    return await user_service.request("GET", "/list-agents/", headers=headers)


@app.get("/api/user/list-users")
async def list_users(authorization: Optional[str] = Header(None)):
    """GET /api/user/list-users - List all users (admin-only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    headers = {"Authorization": authorization}
    return await user_service.request("GET", "/list-users/", headers=headers)


@app.get("/api/user/list-approvals")
async def list_approvals(authorization: Optional[str] = Header(None)):
    """GET /api/user/list-approvals - List pending approvals (admin-only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    headers = {"Authorization": authorization}
    return await user_service.request("GET", "/list-approvals/", headers=headers)


@app.put("/api/user/approve-delete/{user_id}")
async def approve_delete_agent(
    user_id: int,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """PUT /api/user/approve-delete/{user_id} - Approve/delete agent."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    data = await request.json()
    headers = {"Authorization": authorization}
    return await user_service.request("PUT", f"/approve-delete/{user_id}/", headers=headers, json_data=data)


@app.delete("/api/user/approve-delete/{user_id}")
async def delete_agent(user_id: int, authorization: Optional[str] = Header(None)):
    """DELETE /api/user/approve-delete/{user_id} - Delete agent."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    headers = {"Authorization": authorization}
    return await user_service.request("DELETE", f"/approve-delete/{user_id}/", headers=headers)


# ============ Loan Service Routes ============

@app.post("/api/loan/customer-loan")
async def request_loan(request: Request, authorization: Optional[str] = Header(None)):
    """POST /api/loan/customer-loan - Request a loan (agent-only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    data = await request.json()
    headers = {"Authorization": authorization}
    return await loan_service.request("POST", "/customer-loan/", headers=headers, json_data=data)


@app.put("/api/loan/approve-reject-loan/{loan_id}")
async def approve_reject_loan(
    loan_id: int,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """PUT /api/loan/approve-reject-loan/{loan_id} - Approve/reject loan (admin-only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    data = await request.json()
    headers = {"Authorization": authorization}
    return await loan_service.request("PUT", f"/approve-reject-loan/{loan_id}/", headers=headers, json_data=data)


@app.put("/api/loan/edit-loan/{loan_id}")
async def edit_loan(
    loan_id: int,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """PUT /api/loan/edit-loan/{loan_id} - Edit loan (agent-only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    data = await request.json()
    headers = {"Authorization": authorization}
    return await loan_service.request("PUT", f"/edit-loan/{loan_id}/", headers=headers, json_data=data)


@app.get("/api/loan/list-loans-admin-agent")
async def list_loans_admin_agent(
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """GET /api/loan/list-loans-admin-agent - List loans for admin/agent."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    headers = {"Authorization": authorization}
    params = {"status": status} if status else None
    return await loan_service.request("GET", "/list-loans-admin-agent/", headers=headers, params=params)


@app.get("/api/loan/list-loans-customer")
async def list_loans_customer(
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """GET /api/loan/list-loans-customer - List customer's loans."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    headers = {"Authorization": authorization}
    params = {"status": status} if status else None
    return await loan_service.request("GET", "/list-loans-customer/", headers=headers, params=params)


# ============ Error Handlers ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "False") == "True"
    )
