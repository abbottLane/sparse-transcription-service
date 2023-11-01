from fastapi import APIRouter, HTTPException
from starlette.responses import Response
from ..data_access.schemas import CreateProjectModel, ResponseModel
from ..data_access import crud
import time

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def create_project(project: CreateProjectModel) -> ResponseModel:
    project_dict = project.dict()
    project_dict['timestamp'] = int(round(time.time()*1000)) # convert to milliseconds
    id = await crud.create_project(project_dict)
    if id:
        return ResponseModel(id, "Created project")
    raise HTTPException(status_code=404, detail="Project not created")

@router.get("/")
async def get_projects() -> ResponseModel:
    """Retrieves project header data for all projects in the collection

    Returns:
        ResponseModel: A list of project data along with the http response info
    """
    projects = await crud.retrieve_projects()
    return ResponseModel(projects, "Retrieved Projects")

@router.get("/{id}")
async def get_project_by_id(id: str):
    """Retrieve a project by its ID

    Args:
        id (str): The project id of the Project you want to retrieve
    """
    project = await crud.retrieve_project(id)
    return ResponseModel(project, "Retrieved project with id " + id)

@router.delete("/{id}")
async def delete_project_by_id(id: str):
    """Delete a project by its ID

    Args:
        id (str): ID of project to delete
    """
    data_deleted = await crud.delete_project_entry(id)
    return ResponseModel(data_deleted, "Deleted project with id " + id)

