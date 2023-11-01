from bson.objectid import ObjectId
from app.data_access.schemas import AlignPhonesModel, CreateGlossaryEntryModel, DiscoverWordsModel, RemoveTokenModel, UpsertTokenModel
from fastapi import WebSocket
from app.agents.word_discovery.word_discovery_service import initiate_discovery
from app.agents.phone_alignment.alignment_service import initiate_alignment
from ..data_access.database import doc2dict, projects_collection, entries_collection
from ..data_access import language
from bson.objectid import ObjectId
from typing import TypedDict, List


class IProjectToken(TypedDict):
    media_entry_id: str
    token_id: str


class SpannotateSession:
    def __init__(self, project_id: str, media_id: str):
        self.project_id = project_id
        self.media_id = media_id
        self.userId: str = ''
        print('init project_id', project_id)

    async def connect(self, websocket: WebSocket):
        self.ws = websocket
        await websocket.accept()
        await self._sendInitialData()

    async def process(self, msg):
        print('processing websocket msg', msg)
        cmd = msg['type']
        data = msg['data']
        if cmd == 'hello':
            await self._respond('info', 'hello yourself')
        elif cmd == 'user':
            self.userId = data
        elif cmd == 'typed':
            await self._typed(data)
        elif cmd == 'addtoken':
            await self._addToken(data)
        elif cmd == 'deltoken':
            await self._delToken(data)
        elif cmd == 'align':
            await self._align(data)

    async def _respond(self, type: str, data):
        await self.ws.send_json({
            "type": type,
            "data": data
        })

    async def _typed(self, data):
        apm = AlignPhonesModel(
            phones=data["phones"], tokens=data["tokens"]
        )
        alignment = await initiate_alignment(apm)
        print('alignment', alignment)
        aligntok = []
        for align in alignment:
            aligntok.append({
                "token": align['token'],
                "start": align['alignment'][0]['start'],
                "stop": align['alignment'][0]['stop'],
            })
        dwm = DiscoverWordsModel(
            phone_str=data["phones"],
            aligned_tokens=aligntok
        )
        discovered = await initiate_discovery(dwm)
        # Get the pseudo-token that corresponds to the text entry
        typedtoken: str
        if data['typedPos']:
            # if it's being inserted
            typedtoken = data['tokens'][data['typedPos']]
        else:
            typedtoken = data['tokens'][-1]  # otherwise it's just the last one
        # we only want the completitions for the thing we typed
        relevantdiscovered = list(
            set([x for x in discovered if typedtoken in x]))
        # Go and get all the glossary entries for the stuff that was discovered
        userEntries = {}
        async for glossary_entry in entries_collection.find({"user": self.userId, "form": {"$in": relevantdiscovered}}):
            userEntries[glossary_entry['form']] = doc2dict(glossary_entry)
        canonEntries = {}
        async for glossary_entry in entries_collection.find({"canonical": True, "form": {"$in": relevantdiscovered}}):
            canonEntries[glossary_entry['form']] = doc2dict(glossary_entry)
        # In the event the completion engine doesn't return the typed token, check if we have glossary entries anyway
        if typedtoken not in relevantdiscovered:
            cgentry = await entries_collection.find_one({"canonical": True, "form": typedtoken})
            ugentry = await entries_collection.find_one({"user": self.userId, "form": typedtoken})
            if cgentry or ugentry:
                relevantdiscovered.insert(0, typedtoken)
            if cgentry:
                canonEntries[typedtoken] = doc2dict(cgentry)
            if ugentry:
                userEntries[typedtoken] = doc2dict(ugentry)
        # send a response back
        completions = []
        for comp in relevantdiscovered:
            completions.append({
                "typedPos": data['typedPos'],
                "token": comp,
                "userEntry": userEntries[comp] if comp in userEntries else None,
                "canonEntry": canonEntries[comp] if comp in canonEntries else None
            })

        await self._respond("discovered", {
            "alignment": aligntok,
            "phones": data["phones"],
            "typed": typedtoken,
            "completions": completions
        })

    # alignment only, for initial loading
    async def _align(self, data):
        apm = AlignPhonesModel(
            phones=data["phones"], tokens=data["tokens"]
        )
        alignment = await initiate_alignment(apm)
        print('alignment', alignment)
        aligntok = []
        for align in alignment:
            aligntok.append({
                "token": align['token'],
                "start": align['alignment'][0]['start'],
                "stop": align['alignment'][0]['stop'],
            })
        await self._respond("align", {
            "alignment": aligntok,
            "phones": data["phones"]
        })

    async def _sendInitialData(self):
        project = await projects_collection.find_one({"_id": ObjectId(self.project_id)})
        thismedia = [x for x in project['timeline']['media']
                     if x['id'] == self.media_id][0]
        tokens: List[IProjectToken] = []
        if 'breath_groups' in thismedia:
            for bg in thismedia['breath_groups']:
                if 'tokens' in bg:
                    tokens.extend([x for x in bg['tokens']])
        else:
            await self._respond('init', [])
            return
        print('tokens', tokens)
        geid = list(set([x['glossary_entry_id'] for x in tokens]))
        glossary_entry_ids = [ObjectId(x) for x in geid]
        print('gid', glossary_entry_ids)
        glossaryEntries = {}
        async for document in entries_collection.find({"_id": {"$in": glossary_entry_ids}}, {"form": 1}):
            print('got', document)
            id = str(document["_id"])
            del document['_id']
            document['id'] = id
            glossaryEntries[id] = document
        await self._respond('init', {
            "breathGroups": thismedia['breath_groups'],
            "glossaryEntries": glossaryEntries
        })

    async def _addToken(self, data):
        upm = UpsertTokenModel(
            project_id = self.project_id,
            form = data['form'],
            user = self.userId,
            canonical = False,
            glossary_id = data['glossary_id'],
            breath_group_id = data['breath_group_id'],
            media_id = data['media_id'],
            position = data['position']
        )
        retval = await language.upsert_token(upm)
        await self._respond('newtoken', retval)

    async def _delToken(self, data):
        rtm = RemoveTokenModel(
            user = self.userId,
            glossary_id = data['glossary_id'],
            glossary_entry_id = data['glossary_entry_id'],
            project_id = self.project_id,
            token_id = data['token_id'],
            media_id =  data['media_id'],
            breath_group_id = data['breath_group_id']
        )
        retval = await language.remove_token(rtm)
        await self._respond('remtoken', retval)


