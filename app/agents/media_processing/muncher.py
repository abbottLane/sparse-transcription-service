#from pydub import AudioSegment
import asyncio
from auditok import split
import json
from ...data_access import crud
from typing import TypedDict, List, Tuple
from bson.objectid import ObjectId

DEFAULTSAMPLERATE = 8000


class Region(TypedDict):
    start: float
    end: float
    allo: str


class AudioInfo(TypedDict):
    peaks: List[float]
    regions: List[Region]

# This function takes a full sourcefile path and a destination filepath as arguments
# It will run ffmpeg to convert, mono, normalize and resample the audio ...
# ... then gather peak data from audiowaveform and normalizes those values
# ... then it splits the audio into regions with auditok
# ... then despatch a list of AudioSegment objects to alloallo for multi-threaded processing
# ... then returns the data into the AudioInfo data type described above


async def munchinator(sourceFile: str, processedFile: str) -> AudioInfo:
    ffmpegcmd = 'ffmpeg -i ' + sourceFile + ' -ac 1 -vn -filter_complex "loudnorm,aresample=' + \
        str(DEFAULTSAMPLERATE) + '" -y ' + processedFile
    proc = await asyncio.create_subprocess_shell(ffmpegcmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode:
        raise Exception('ffmpeg failed', stderr.decode())
    awaveformcmd = 'audiowaveform -i ' + processedFile + \
        ' --output-format json --pixels-per-second 20 --bits 8'
    proc = await asyncio.create_subprocess_shell(awaveformcmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    awaveformstdout, stderr = await proc.communicate()
    print('return code', proc.returncode)
    if proc.returncode:
        raise Exception('audiowaveform failed', stderr.decode())
    jsondata = json.loads(awaveformstdout)
    max_val = float(max(jsondata["data"]))
    normdata = [round(x / max_val, 2) for x in jsondata["data"]]
    regions = split(processedFile)
    reglist = [(round(x.meta.start, 3), round(x.meta.end, 3)) for x in regions]
    allostrings: List[str] = await alloWorker(processedFile, reglist)
    fregions = []
    for i, reg in enumerate(reglist):
        fregions.append(
            {"start": reg[0], "end": reg[1], "phones": allostrings[i]})
    return {"peaks": normdata, "regions": fregions}


async def alloWorker(filepath: str, regions: List[Tuple[float, float]]) -> List[str]:
    subprocess_call = ". alloenv/bin/activate && " + \
        'python app/agents/media_processing/turboworker.py -i "' + \
        filepath + '" -r "' + str(regions) + '"'
    print("subprocess call: " + subprocess_call)
    proc = await asyncio.create_subprocess_shell(
        subprocess_call,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    #print("STDERR: " + stderr.decode() )
    #print("STDOUT: " + stdout.decode() )
    receivedstring = stdout.decode().strip()
    return eval(receivedstring)


async def media_processing_background_task(filepath, resample_path, id):
    print("STARTED BACKGROUND PROCESS")
    try:
        processed_data = await munchinator(filepath, resample_path)
        # update the media_entry with list of voice detection spans
        await crud.update_media_entry(id, {
            "agents.peaks": processed_data['peaks'],
            "agents.regions": processed_data['regions']
        })
        mediaEntry = await crud.get_media(media_id=id)
        projectId = mediaEntry[0]['project']
        breathgroups = []
        if processed_data['regions']:
            for r in processed_data['regions']:
                breathgroups.append({
                    "id": str(ObjectId()),
                    "start": r['start'],
                    "end": r['end'],
                    "tokens": []
                })
        mediadata = {
            "id": id,
            "breath_groups": breathgroups
        }
        await crud.add_media_to_project(projectId, mediadata)

    except Exception as e:
        print(e)
