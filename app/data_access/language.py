from app.data_access.schemas import CreateGlossaryEntryModel, CreateGlossaryModel, RemoveTokenModel, UpsertTokenModel
from .database import glossaries_collection, entries_collection, projects_collection
from bson.objectid import ObjectId
from typing import TypedDict, List, Optional
from pymongo import ReturnDocument


class IGlossaryEntry(TypedDict):
    form: str
    gloss: str
    tokens: List
    user: str
    canonical: bool
    glossary_id: str
    lexical_entry: Optional[dict]


class IToken(TypedDict):
    breath_group_id: str
    timeline_id: str
    project_id: str


class ITokenID(IToken, total=False):
    token_id: str


def glossaries_helper(glossary) -> dict:
    return {
        "id": str(glossary["_id"]),
        "name": glossary['name'],
        "language": glossary['language'],
        "entries": glossary['entries']
    }


async def retrieve_glossary(id: str):
    try:
        glossary = await glossaries_collection.find_one({"_id": ObjectId(id)})
        return glossaries_helper(glossary)
    except Exception as e:
        raise ValueError(e)


async def retrieve_glossaries():
    glossaries = []
    async for glossary in glossaries_collection.find():
        glossaries.append(glossaries_helper(glossary))
    return glossaries


async def create_glossary(glossary_data: CreateGlossaryModel) -> str:
    glossary = await glossaries_collection.insert_one(glossary_data.dict())
    return str(glossary.inserted_id)


async def upsert_glossary_entry(glossary_entry_data: CreateGlossaryEntryModel) -> str:
    # If there exists a glossary entry by the same user with the same surface form, just update that one
    user = glossary_entry_data['user']
    form = glossary_entry_data['form']
    entry_exists = await entries_collection.find_one(
        {"user": user, "form": form}
    )
    if entry_exists:
        glossary_entry_id = str(entry_exists['_id'])
        for token in glossary_entry_data['tokens']:
            token['token_id'] = str(ObjectId())
            await entries_collection.update_one(
                {"_id": ObjectId(glossary_entry_id)},
                {
                    "$push": {"tokens": token}
                }
            )
    else:
        # Otherwise, create a new entry
        glossary_entry_dict = glossary_entry_data.dict()
        for token in glossary_entry_dict['tokens']:
            token['token_id'] = str(ObjectId())
        insert_result = await entries_collection.insert_one(
            glossary_entry_dict
        )
        glossary_entry_id = str(insert_result.inserted_id)
    return glossary_entry_id


async def insert_glossary_entry_token(token_data: IToken, entry_id: str) -> str:
    #
    # Generate and insert a token_id
    new_token_data = {
        "token_id": str(ObjectId()),
        "breath_group_id": token_data["breath_group_id"],
        "timeline_id": token_data["timeline_id"],
        "project_id": token_data["project_id"]
    }
    #
    # Find the glossary entry and insert token into the entry
    entry_exists = await entries_collection.find_one(
        {"_id": ObjectId(entry_id)}
    )
    if entry_exists:
        print("Entry exists! Will push token: " + str(new_token_data))
        await entries_collection.update_one(
            {"_id": ObjectId(entry_id)},
            {
                "$push": {"tokens": new_token_data}
            }
        )
    return new_token_data['token_id']


async def delete_glossary_entry_token(glossary_entry_id: str, token_id: str) -> str:
    entry_exists = await entries_collection.find_one(
        {"_id": ObjectId(glossary_entry_id)}
    )
    if entry_exists:
        glossary_entry_id = entry_exists['_id']
        await entries_collection.update_one(
            {"_id": glossary_entry_id},
            {
                "$pull": {"tokens": {"token_id": token_id}}
            }
        )
        entry = await entries_collection.find_one_and_update(
            {"_id": glossary_entry_id},
            {
                "$pull": {"tokens": {"token_id": token_id}}
            },
            return_document=ReturnDocument.AFTER
        )
        if entry['canonical'] == False and len(entry['tokens']) == 0:
            await entries_collection.delete_one({"_id": glossary_entry_id})
            return ''
    return str(glossary_entry_id)


async def delete_glossary(id: str) -> bool:
    glossary = await glossaries_collection.find_one({"_id": ObjectId(id)})
    if glossary:
        await glossaries_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False


async def upsert_token(apidata: UpsertTokenModel):
    # make a new token
    newtoken = {
        "breath_group_id": apidata.breath_group_id,
        "project_id": apidata.project_id,
        "token_id": str(ObjectId())
    }
    # let's see if we have a glossary entry
    gentry_exists = await entries_collection.find_one(
        {"user": apidata.user, "form": apidata.form,
            "glossary_id": apidata.glossary_id}
    )
    glossary_entry_id: str
    if gentry_exists:
        glossary_entry_id = str(gentry_exists['_id'])
        await entries_collection.update_one(
            {"_id": ObjectId(glossary_entry_id)},
            {
                "$push": {"tokens": newtoken}
            }
        )
    else:
        # Otherwise, create a new entry
        glossary_entry = {
            "form": apidata.form,
            "gloss": "",
            "user": apidata.user,
            "glossary_id": apidata.glossary_id,
            "canonical": apidata.canonical,
            "tokens": [newtoken]
        }
        insert_result = await entries_collection.insert_one(
            glossary_entry
        )
        glossary_entry_id = str(insert_result.inserted_id)
    # make the token entry for a breathgroup
    projecttoken = {
        "token_id": newtoken['token_id'],
        "glossary_entry_id": glossary_entry_id
    }
    # update project breathgroup
    tokenpush = projecttoken if not apidata.position else {
        "$each": [projecttoken],
        "$position": apidata.position
    }
    project_document = await projects_collection.find_one_and_update(
        {"_id": ObjectId(apidata.project_id)},
        {"$push": {"timeline.media.$[updateMedia].breath_groups.$[updateBG].tokens": tokenpush}}, arrayFilters=[
            {"updateMedia.id": apidata.media_id},
            {"updateBG.id": apidata.breath_group_id}
        ],
        return_document=ReturnDocument.AFTER
    )
    glossary_entry = await entries_collection.find_one({"_id": ObjectId(glossary_entry_id)})
    del glossary_entry['_id']
    glossary_entry['id'] = glossary_entry_id
    media = [x for x in project_document['timeline']['media'] if x['id'] == apidata.media_id][0]
    breath_group = [x for x in media['breath_groups'] if x['id'] == apidata.breath_group_id][0]
    return {
        "glossary_entry": glossary_entry,
        "breath_group": breath_group
    }


async def remove_token(apidata: RemoveTokenModel):
    await delete_glossary_entry_token(apidata.glossary_entry_id, apidata.token_id)
    retval = await projects_collection.find_one_and_update(
        {"_id": ObjectId(apidata.project_id)},
        {"$pull": {"timeline.media.$[updateMedia].breath_groups.$[updateBG].tokens": {"token_id": apidata.token_id}}},
        array_filters=[
            {"updateMedia.id": apidata.media_id},
            {"updateBG.id": apidata.breath_group_id}
        ],
        projection={'_id': False},
        return_document=ReturnDocument.AFTER
    )
    media = [x for x in retval['timeline']['media'] if x['id'] == apidata.media_id][0]
    breathgroup = [x for x in media['breath_groups'] if x['id'] == apidata.breath_group_id][0]
    return {
        "breath_group": breathgroup,
        "removed_token_id": apidata.token_id
    }
