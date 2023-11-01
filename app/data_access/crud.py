'''
Reusable functions to interact with the data in the database 
'''
from .database import projects_collection, projects_helper, projects_info_helper, media_collection, media_helper, users_collection
from bson.objectid import ObjectId
import datetime
from rx.subject import BehaviorSubject
import time
from ..data_access.schemas import UserLoginModel, CreateGlossaryEntryModel


mediaList = []
mediaSubject = BehaviorSubject([])

# PROJECTS


async def create_project(project_data):
    project_data['date'] = datetime.datetime.fromtimestamp(
        project_data['date']/1000)
    project = await projects_collection.insert_one(project_data)
    return str(project.inserted_id)


async def retrieve_projects():
    projects = []
    async for project in projects_collection.find():
        projects.append(projects_info_helper(project))
    return projects


async def retrieve_project(id: str):
    project = await projects_collection.find_one({"_id": ObjectId(id)})
    if project:
        return projects_helper(project)


async def delete_project_entry(id):
    project = await projects_collection.find_one({"_id": ObjectId(id)})
    if project:
        await projects_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False


async def add_media_to_project(id, mediadata):
    await projects_collection.update_one({
        "_id": ObjectId(id)
    }, {
        "$push": {"timeline.media": mediadata}
    })

# MEDIA


async def create_media_entry(media_entry):
    media_entry['processed'] = False
    media = await media_collection.insert_one(media_entry)
    # this code is for watchers
    if media and media.inserted_id:
        global mediaList, mediaSubject
        new_media_entry = media_entry
        new_media_entry["_id"] = str(media.inserted_id)
        mediaList.append(media_helper(new_media_entry))
        mediaSubject.on_next(mediaList)
    return str(media.inserted_id)


async def update_media_entry(id, update):
    media = await media_collection.find_one({"_id": ObjectId(id)})
    if media:
        updated_media = await media_collection.update_one({
            "_id": ObjectId(id)
        },
            {
                "$set": update
        }
        )
        if updated_media:
            # update our watcher
            global mediaList, mediaSubject
            new_media_object = media  # make a copy
            new_media_object.update(update)  # apply the update
            mediasnippet = media_helper(new_media_object)  # get a snippet
            index = [x['id']
                     for x in mediaList].index(id)  # find the item index
            mediaList[index] = mediasnippet  # replace it
            mediaSubject.on_next(mediaList)  # emit new list
            return True
        return False


async def update_media_agent_entry(id, agent, value):
    media = await media_collection.find_one({"_id": ObjectId(id)})
    print("update_media_agent_entry")
    if media:
        updated_media = await media_collection.update_one({
            "_id": ObjectId(id)
        },
            {
                "$set": {
                    "agents." + agent: value,
                }
        }
        )
        if updated_media:
            return True
    return False


async def get_media(project_id=None, media_id=None):
    if project_id:
        filter = {'project': project_id} if not project_id == None else None
        media_list = []
        async for media in media_collection.find(filter):
            media_obj = media_helper(media)
            media_list.append(media_obj)
        return media_list
    if media_id:
        print("getting media by media id")
        media = await media_collection.find_one({"_id": ObjectId(media_id)})
        return [media_helper(media)]


async def delete_media_entry(id):
    media = await media_collection.find_one({"_id": ObjectId(id)})
    if media:
        # remove from the media array in the project
        projectId = media['project']
        # projectData = projects_collection.find_one({"_id": ObjectId(projectId)})
        # breathgroups = [x['breath_groups'] for x in projectData['timeline']['media'] if x['_id' == id]][0]
        # for bg in breathgroups:
        #     if 'tokens' in bg:
        #         for token in bg['tokens']:
        #             delete_glossary_entry_token() # both glossary entry and the token? wtf?
        print('removing media', id, 'from project', projectId)
        await projects_collection.update_one(
            {"_id": ObjectId(projectId)},
            {
                "$pull": {"timeline.media": {"id": id}}
            })
        # delete from media collection
        await media_collection.delete_one({"_id": ObjectId(id)})
        #
        # To-do: THIS CODE SHOULD Iterate through the glosary
        #
        # this code is for watchers - delete item from medialist
        global mediaList, mediaSubject
        mediaList = [x for x in mediaList if x["id"] != id]
        mediaSubject.on_next(mediaList)
        return True
    return False

# USERS


async def initialize_users():
    default_users = [
        {"user_id": "wlane", "display_name": "William Lane"},
        {"user_id": "mbettinson", "display_name": "Mat Bettinson"}
    ]
    for user in default_users:
        await users_collection.insert_one(user)
    return True


async def getUser(uid: str):
    return await users_collection.find_one({"uid": uid})


async def createUser(user: UserLoginModel):
    now = int(round(time.time()*1000))
    ud = user.dict()
    ud['lastLogin'] = now
    ud['created'] = now
    return await users_collection.insert_one(ud)


async def updateUserLogin(uid):
    await users_collection.update_one({
        "uid": uid
    },
        {
        "$set": {
            "lastLogin": int(round(time.time()*1000))
        }
    })
    return True


async def watchMedia():
    global mediaSubject, mediaList
    async for media in media_collection.find():
        mediaList.append(media_helper(media))
    mediaSubject.on_next(mediaList)


def getMediaSubject():
    return mediaSubject


async def addMediaToProject(projectId, mediaData):
    await projects_collection.update_one({
        "id"
    })
