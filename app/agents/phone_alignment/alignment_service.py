from app.data_access import crud
from app.data_access.crud import get_media, retrieve_project
from app.data_access.language import retrieve_glossary
from app.data_access.schemas import AlignPhonesModel
import asyncio
import json
import re

WORDSPOTTING_THRESHOLD=.1

async def initiate_alignment(task_data: AlignPhonesModel, wordspotting=False):
    subprocess_call = ". alloenv/bin/activate && " + 'python app/agents/phone_alignment/token2phonalign.py -p "' + str(task_data["phones"])  + ' " -t "' + str(task_data["tokens"]) + '"'
    
    if wordspotting:
        subprocess_call += " -a true"
    proc = await asyncio.create_subprocess_shell(
        subprocess_call,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
        )
    stdout, stderr = await proc.communicate()
    print('stdout', stdout, 'stderr', stderr)
    dict_as_str = stdout.decode().strip()
    dict_as_str = re.sub("'", "\"", dict_as_str)
    return json.loads(dict_as_str)

async def wordspotting(media_id: str):
    """Given a media_id, apply the relevent project's glossary to that media's phone sequence data

    Args:
        media_id (str): id of media who's phone sequence we want to apply the glossary entries to
    """
    media = await get_media(media_id=media_id)
    #assert(len(media) == 1, "Media ID failed to return exactly 1 media object")
    media = media[0]
    project = await retrieve_project(id = media['project'])
    glossary = await retrieve_glossary(project['glossary_id'])
    for region in media['agents']['regions']:
        task_data = AlignPhonesModel.parse_obj(
            {
                "tokens" : [x for x in glossary['entries'].keys()],
                "phones" : region['phones']
            }
        )
        task_response = await initiate_alignment(task_data, wordspotting=True)

        # we have alignments of every word in the glossary accross THIS VAD region.
        # these need to be filtered down to only high confidence alignments
        #  uugh the computational waste.....we will have to find a better way to do this later.

        for token in task_response:
            thresholded_alignments = []
            for alignment in token['alignment']:
                if alignment['distance'] < WORDSPOTTING_THRESHOLD:
                    thresholded_alignments.append(alignment)
            token['alignment'] = thresholded_alignments
        region['wordspotting'] = [x for x in task_response if len(x['alignment']) >= 1]
                    
    # Update this media entry with all spotted tokens lower than the wordspotting threshold
    await crud.update_media_entry(media_id, {
        "agents.regions": media['agents']['regions']
    })

