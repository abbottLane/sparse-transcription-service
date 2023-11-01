from fastapi import APIRouter, HTTPException
from ..data_access.schemas import CreateGlossaryEntryModel, CreateGlossaryModel, ErrorResponseModel, ResponseModel
from ..data_access import crud, language

router = APIRouter(
    prefix="/glossary",
    tags=["Glossary"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_glossaries():
    """Fetches all glossaries from the glossary table

    Returns:
        List: List of glossaries
    """
    projects = await language.retrieve_glossaries()
    return ResponseModel(projects, "Retrieved glossaries")

@router.get("/{id}")
async def get_glossary(id: str):
    """Gets the glossary associated with a project id

    Returns:
        [type]: [description]
    """
    try:
        glossary = await language.retrieve_glossary(id)
    except Exception as e:
        print(e)
        return ErrorResponseModel(e, 400, "Failed to retrieve glossary, see this['error'] for details.")
    return ResponseModel(glossary, "Retrieved glossaries")

@router.post("/")
async def create_glossary(glossary: CreateGlossaryModel):
    """Creates an empty glossary to initialize along with a project
    """
    id = await language.create_glossary(glossary)
    return ResponseModel(id, "Created glossary")

@router.post("/entry/")
async def upsert_glossary_entry(entry: CreateGlossaryEntryModel):
    try:
        entry_id = await language.upsert_glossary_entry(entry)
    except Exception as e:
        print(e)
        return ErrorResponseModel(e, 400, "Failed to insert glossary entry")
    return ResponseModel(entry_id, "inserted the glossary entry successfully")

@router.delete("/entry/")
async def delete_glossary_entry_token(glossary_entry_id: str, token_id: str):
    try:
        deleted_id = await language.delete_glossary_entry_token(glossary_entry_id, token_id)
    except Exception as e:
        print(e)
        return ErrorResponseModel(e, 400, "Failed to delete glossary entry token")
    return ResponseModel(deleted_id, "Deleted the glossary entry token successfully")


@router.delete("/{id}")
async def delete_glossary_by_id(id: str):
    """Delete a Glossary by its ID

    Args:
        id (str): ID of glossary to delete
    """
    data_deleted = await language.delete_glossary(id)
    return ResponseModel(data_deleted, "Deleted glossary with id " + id)