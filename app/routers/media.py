from app.agents.phone_alignment.alignment_service import wordspotting
from app.data_access.schemas import CreateMediaModel, ResponseModel
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.datastructures import UploadFile
from fastapi.params import File
from ..data_access import crud
import shutil
import os, time
from asyncio import create_task
from app.agents.media_processing.muncher import media_processing_background_task
import re

router = APIRouter(
    prefix="/media",
    tags=["Media"],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def create_media_entry(media: CreateMediaModel):
    media_entry_dict = media.dict()
    media_entry_dict['timestamp'] = int(round(time.time()*1000)) # convert to milliseconds
    id = await crud.create_media_entry(media_entry_dict)
    if id:
        return ResponseModel(id, "Created media")
    raise HTTPException(status_code=404, detail="Media entry not created")

@router.post("/upload/{id}")
async def upload_media_file(id: str, background_tasks: BackgroundTasks, media: UploadFile = File(...)):
    filepath = os.path.join("/media", "storage", id+".wav")
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(media.file, buffer)
    except:
        raise Exception("Could not write file to server location: " + filepath)
    ###############
    ### CALLBACKS
    ###############

    # 1: update the filepath in the media entry after the file has been uploaded
    response = await crud.update_media_entry(id, {"filepath": filepath})
    # 2: set up a background task to process the media
    background_tasks.add_task(mediaUploadTask, filepath, re.sub("\.wav", ".resampled.wav", filepath), id)
    return ResponseModel(response, "Uploaded media successfully")

async def mediaUploadTask(filepath, resample_path, id):
    # do allosaurus first (writes data to the db itself)
    await media_processing_background_task(filepath, resample_path, id)
    # now do the word spotting (also writes to the db itself)
    #await wordspotting(id)
    # media entry is now 'processed'
    await crud.update_media_entry(id, {"processed": True})

@router.delete("/delete/{id}")
async def delete_media_file(id: str):
    # delete entry from the db first
    data_deleted = await crud.delete_media_entry(id)
    if data_deleted:
        # delete from data store
        filepath = os.path.join("/media", "storage", id + ".wav")
        if os.path.isfile(filepath):
            os.remove(filepath)
        return ResponseModel(True, "Removed media from db and filestore")
    else: 
        return ResponseModel(True, "Data wasn't deleted, <shrug>")

@router.get("/project/{project_id}")
async def get_media_by_projectid(project_id: str):
    media = await crud.get_media(project_id=project_id)
    return ResponseModel(media, "Retrieved media with project id: " + project_id)

@router.get("/{media_id}")
async def get_media_by_media_id(media_id: str):
    media = await crud.get_media(media_id=media_id)
    return ResponseModel(media, "Retrieved media with media id: " + media_id)

@router.on_event("startup")
async def startup_event():
    await crud.watchMedia()
