from fastapi import APIRouter, HTTPException
from ..data_access.schemas import ResponseModel, UserLoginModel
from ..data_access import crud

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login")
async def loginUser(user: UserLoginModel) -> ResponseModel:
    """Logs in a user to the app, creates a database entry if the user doesn't exist

    Returns:
        ResponseModel: Nothing
    """
    fetchuser = await crud.getUser(user.uid) # We can use an attribute because user is a model
    if fetchuser == None:
        newuser = await crud.createUser(user)
        return ResponseModel(True, "Created new user")
    else:
        userupdate = await crud.updateUserLogin(fetchuser['uid']) # from the db, can't use attribute
        return ResponseModel(True, "Logged in user")

@router.get("/{id}")
async def getUser(userid: str):
    user = await crud.getUser(userid)
    return ResponseModel(user, "Retrieved user with id " + userid)
