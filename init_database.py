from app.data_access.schemas import CreateGlossaryEntryModel, CreateGlossaryModel
from app.data_access.crud import create_project
from app.data_access.language import IToken, create_glossary, delete_glossary_entry_token, insert_glossary_entry_token, upsert_glossary_entry
from resources.njamed import load_entries
from app.data_access.database import entries_collection
from pymongo import MongoClient, TEXT
import time 
import asyncio


# Create the DB
glossary = {
                "name": "KunwinjkuM",
                "language": [{"name": "kunwinjku", "iso639_2": "gup"}],
            }
glossary_entries = [
                        {
                            "glossary_id":"",
                            "form": "birri",
                            "gloss": "3pl.past",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },
                        {
                            "glossary_id":"",
                            "form": "birri",
                            "gloss": "3pl.past",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },
                        {
                            "glossary_id":"",
                            "form": "wurdurd",
                            "gloss": "children",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },
                        {
                            "glossary_id":"",
                            "form": "waken",
                            "gloss": "LOC",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },
                        {
                            "glossary_id":"",
                            "form":"ka",
                            "gloss": "3sg",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },
                        {
                            "glossary_id":"",
                            "form": "konda",
                            "gloss": "Here",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },

                        {
                            "glossary_id":"",
                            "form": "kore",
                            "gloss": "preposition",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },
                        {
                            "glossary_id":"",
                            "form": "bim",
                            "gloss": "painting",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        },
                        {
                            "glossary_id":"",
                            "form": "yime",
                            "gloss": "says",
                            "tokens":[],
                            "user":"userid123",
                            "canonical": False
                        }
                    ]


async def init_db():
    mongo_client = MongoClient('mongodb://localhost:27017')
    print("Checking list of local DBs, deleting Sparzan if extant ...")
    database_list = mongo_client.list_database_names()
    # print the databases and the length of the list
    print ("database_list:", database_list)
    print ("number of db:", len(database_list))
    # Specify db to delete, then delete it
    if "sparzan" in database_list:
        db = mongo_client['sparzan']
        mongo_client.drop_database(db)
    
    # create glossary, get its id
    print("Creating glossary ...")
    glossary_object = CreateGlossaryModel.parse_obj(glossary)
    glossary_id = await create_glossary(glossary_object)
    print("Glossary created.")

    # token to delete later
    del_tok = ""
    del_gloss_entry = ""

    # insert glossary entries
    
    for i, entry in enumerate(glossary_entries):
        entry['glossary_id'] = glossary_id
        entry_object = CreateGlossaryEntryModel.parse_obj(entry)
        entry_id = await upsert_glossary_entry(entry_object)

        # Some glossary entries will be given tokens
        if i == 0: 
            print("SURFACEFORM: " + str(entry))
            token: IToken = {
                "breath_group_id": "bg123",
                "timeline_id": "timeline123",
                "project_id": "project123"
            }
            token_id = await insert_glossary_entry_token(token, entry_id=entry_id)
        if i == 1: 
            token: IToken = {
                "breath_group_id": "bg994",
                "timeline_id": "timeline123",
                "project_id": "project123"
            }
            token_id = await insert_glossary_entry_token(token, entry_id=entry_id)
        if i == 2: 
            token: IToken = {
                "breath_group_id": "bg888",
                "timeline_id": "timeline123",
                "project_id": "project123"
            }
            token_id = await insert_glossary_entry_token(token, entry_id=entry_id)
        
        if i == 3: 
            token: IToken = {
                "breath_group_id": "bg889",
                "timeline_id": "timeline123",
                "project_id": "project123"
            }
            token_id = await insert_glossary_entry_token(token, entry_id=entry_id)
            del_tok = token_id
            del_gloss_entry = entry_id
    print("Creating 'form' index on glossary entries collection")
    await entries_collection.create_index('form')
    # insert glossary entries from njamed.com
    print("Populate Glossary with entries from Njamed.com")
    njamed_entries = load_entries(glossary_id=glossary_id, user="njamed", canonical=True)
    for entry in njamed_entries:
        entry_object = CreateGlossaryEntryModel.parse_obj(entry)
        entry_id = await upsert_glossary_entry(entry_object)

    # delete a token
    if await delete_glossary_entry_token(del_gloss_entry, del_tok):
        print("DELETED A TOKEN")

    project = {
                    "name": "My Kunwinjku Tours project",
                    "owner": "William Lane",
                    "glossary_id": glossary_id,
                    "glossary_langs": [{"name": "kunwinjku", "iso639_2": "gup"}],
                    "metadata": {},
                    "timeline":{
                        "media": [
                            {
                                "id": "media_id_1",
                                "breath_groups": [
                                {"id": "bgid123",
                                "start": 1,
                                "end": 12.3,
                                "duration": 11.3,
                                "tokens": [
                                        "tokenid123",
                                        "tokenid125",
                                        "tokenid129",
                                        "tokenid130"
                                    ]
                                },
                                {"id": "bgid124",
                                "start": 14,
                                "end": 16.1,
                                "duration": 2.1,
                                "tokens": [
                                        "tokenid7445",
                                        "tokenid546454",
                                        "tokenid546",
                                        "tokenid789"
                                    ]
                                },
                                {"id": "bgid125",
                                "start": 18.4,
                                "end": 22.1,
                                "duration": 4.7,
                                "tokens": [
                                        "tokenid7325",
                                        "tokenid5444",
                                        "tokenid95836",
                                        "tokenid73893"
                                    ]
                                }, 
                                ],
                            },
                            {"id": "media_id_2",
                                "breath_groups": [
                                    {"id": "bgid123",
                                    "start": 1,
                                    "end": 12.3,
                                    "duration": 11.3,
                                    "tokens": [
                                            "tokenid123",
                                            "tokenid125",
                                            "tokenid129",
                                            "tokenid130"
                                        ]
                                    },
                                    {"id": "bgid124",
                                    "start": 14,
                                    "end": 16.1,
                                    "duration": 2.1,
                                    "tokens": [
                                            "tokenid7445",
                                            "tokenid546454",
                                            "tokenid546",
                                            "tokenid789"
                                        ]
                                    },
                                    {"id": "bgid125",
                                    "start": 18.4,
                                    "end": 22.1,
                                    "duration": 4.7,
                                    "tokens": [
                                            "tokenid7325",
                                            "tokenid5444",
                                            "tokenid95836",
                                            "tokenid73893"
                                        ]
                                    }, 
                                    ],},
                            {"id": "media_id_3",
                                "breath_groups": [
                                    {"id": "bgid123",
                                    "start": 1,
                                    "end": 12.3,
                                    "duration": 11.3,
                                    "tokens": [
                                            "tokenid123",
                                            "tokenid125",
                                            "tokenid129",
                                            "tokenid130"
                                        ]
                                    },
                                    {"id": "bgid124",
                                    "start": 14,
                                    "end": 16.1,
                                    "duration": 2.1,
                                    "tokens": [
                                            "tokenid7445",
                                            "tokenid546454",
                                            "tokenid546",
                                            "tokenid789"
                                        ]
                                    },
                                    {"id": "bgid125",
                                    "start": 18.4,
                                    "end": 22.1,
                                    "duration": 4.7,
                                    "tokens": [
                                            "tokenid7325",
                                            "tokenid5444",
                                            "tokenid95836",
                                            "tokenid73893"
                                        ]
                                    }, 
                                ],}
                        ],
                        "interpretations": [
                            "translation of the audio in timeline",
                            "notes taken by user on the timeline",
                            "etc"
                        ]
                    },
                    "date": 161369422282,
                    "timestamp": int(round(time.time()*1000))
                }
    print("Creating project ...")
    await create_project(project)
    print("Project created.")


    # print("Creating user collection")
    # await initialize_users()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())