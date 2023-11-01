'''
Define parameters and initiate sessions with a database which can be imported by the data access layer in crud.py
'''
import motor.motor_asyncio
import copy 

MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.sparzan
projects_collection = database.get_collection("projects")
media_collection = database.get_collection("media")
glossaries_collection = database.get_collection("glossaries")
entries_collection = database.get_collection("glossary_entries")
users_collection = database.get_collection("users")


# Helpers
def projects_info_helper(project) -> dict:
    return {
        "id": str(project["_id"]),
        "name": project['name'],
        "owner": project['owner'],
        "date": project['date'],
        "glossary_id": project['glossary_id'],
        "glossary_langs": project['glossary_langs'],
        "metadata": project['metadata'],
    }
def projects_helper(project) -> dict:
    return {
        "id": str(project["_id"]),
        "name": project['name'],
        "owner": project['owner'],
        "date": project['date'],
        "glossary_id": project['glossary_id'],
        "metadata": project['metadata']
        #"project_body": project['project_body']
    }

# Turns a generic mongo document into a plain dictionary suited for serialisation by 
# converting the ObjectId field to a regular id.
def doc2dict(document: dict) -> dict:
    newobj = copy.deepcopy(document)
    newobj["id"] = str(newobj["_id"])
    del newobj["_id"]
    return newobj

def media_helper(media) -> dict:
    media_obj= {
        "id" : str(media['_id']),
        "mimetype": media['mimetype'],
        "name": media['name'],
        "project": media['project'],
        "metadata": media['metadata'],
        "processed": media['processed'] if 'processed' in media else False
    }
    if media['timestamp']:
        media_obj['timestamp'] = media['timestamp']
    if 'agents' in media:
        media_obj['agents'] ={}
        media_obj['agents']['regions'] = media['agents']['regions']
    return media_obj
