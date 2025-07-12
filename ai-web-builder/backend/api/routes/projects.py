from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_projects():
    return {"message": "Projects list - TODO: implement project management"}

@router.post("/")
async def create_project():
    return {"message": "Create project - TODO: implement project creation"}