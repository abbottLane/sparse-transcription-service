import os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from .routers import projects, agents, glossaries, media, users
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import rx.operators as ops
from .evil import hacks
from .data_access import crud
from .session.spannotate import SpannotateSession

if "DEPLOYMENT_ENV" in os.environ:
    if os.environ['DEPLOYMENT_ENV'] == "dev":
        print("Initializing dev FastAPI service ...")
        sparzan = FastAPI() # WHEN DEVING LOCALLY, USE THIS INSTEAD, it allows docs to work.
    else:
        print("Initializing prod FastAPI service ...")
        sparzan = FastAPI(root_path="/api") # Use this one for prod, it accounts for reverse proxy configuration
else:
    raise Exception("DEPLOYMENT_ENV is not set")

origins = [
    "http://localhost:4200",
]

sparzan.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sparzan.include_router(projects.router)
sparzan.include_router(agents.router) 
sparzan.include_router(glossaries.router)
sparzan.include_router(media.router)
sparzan.include_router(users.router)
if "DEPLOYMENT_ENV" in os.environ and os.environ['DEPLOYMENT_ENV'] == "dev":
    sparzan.mount("/media/files", StaticFiles(directory="/media/storage"), name="static")

@sparzan.get("/")
async def root(request: Request):
    return {
        "message": "Root dummy service", 
        "root_path": request.scope.get("root_path")
        }

# Cannot bind web socket to router so this has to go here
@sparzan.websocket("/media/project/ws/{project_id}")
async def wsProject(websocket: WebSocket, project_id: str):
    await websocket.accept()
    o = crud.getMediaSubject().pipe(
        ops.map(lambda x: [i for i in x if i["project"] == project_id])
    )
    #o = media.getMediaSubject()
    gen = hacks.observer2asyncgen(o, loop) # convert an observable to an async generator
    async for msg in gen:
        await websocket.send_json(msg)

@sparzan.websocket("/session/{project_id}/{media_id}")
async def wsSession(websocket: WebSocket, project_id: str, media_id: str):
    print('new ws connect', project_id, media_id)
    sesh = SpannotateSession(project_id, media_id)
    await sesh.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_json()
            await sesh.process(msg)
    except WebSocketDisconnect:
        print('websocket disconnected')

loop = asyncio.get_event_loop()
