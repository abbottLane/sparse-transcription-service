import getopt, sys
from allosaurus.am.utils import *
from allosaurus.audio import Audio
from allosaurus.model import resolve_model_name
from allosaurus.pm.factory import read_pm
from allosaurus.am.factory import read_am
from allosaurus.lm.factory import read_lm
from pydub import AudioSegment
from typing import List
import wave
import numpy as np
from argparse import Namespace
from pathlib import Path

MODEL = "wlane120920"
LANG = "gup-en"
STARTPADDING = 0.05
ENDPADDING = 0.025

def directAllo(file: str, regions: List[tuple]) -> Audio:
    model_name = resolve_model_name(MODEL)
    inference_config = Namespace(model=model_name, device_id=-1, lang=LANG, approximate=False, prior=None)
    #model_path = Path(__file__).parent / 'pretrained' / inference_config.model
    model_path = Path(__file__).parent / 'kunwinjku_allosaurus' / inference_config.model
    pm = read_pm(model_path, inference_config)
    am = read_am(model_path, inference_config)
    lm = read_lm(model_path, inference_config)
    wf = wave.open(file)
    channel_number = wf.getnchannels()
    num_frames = wf.getnframes()
    samp_rate = wf.getframerate()
    width = wf.getsampwidth()
    duration = num_frames / samp_rate
    tokenlist = []
    for (start, stop) in regions:
        audio = Audio()
        audio.set_header(sample_rate=samp_rate, sample_size=num_frames, channel_number=1, sample_width=width)
        stime = round(max(0, start - STARTPADDING) * samp_rate)
        etime = round(min(duration, stop + ENDPADDING) * samp_rate)
        wf.setpos(stime)
        frames = wf.readframes(etime - stime)
        audio_bytes = np.frombuffer(frames, dtype='int16')
        if channel_number == 2:
            audio_bytes = audio_bytes[0::2]
        audio.samples = audio_bytes
        audio.sample_size = len(audio.samples)
        feat = pm.compute(audio)
        feats = np.expand_dims(feat, 0)
        feat_len = np.array([feat.shape[0]], dtype=np.int32)
        tensor_batch_feat, tensor_batch_feat_len = move_to_tensor([feats, feat_len], -1)
        tensor_batch_lprobs = am(tensor_batch_feat, tensor_batch_feat_len)
        batch_lprobs = tensor_batch_lprobs.detach().numpy()
        tokens = lm.compute(batch_lprobs[0], LANG, 1)
        tokenlist.append(tokens)
    return tokenlist

def dojob(argv) -> int:
    inputfile = ''
    regions = []
    try:
        opts, _ = getopt.getopt(argv, "hi:r:", ["ifile=","regions="])
    except getopt.GetoptError:
        print('alloworker.py -i <inputfile> -r "[(start,stop),...]"')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-i':
            inputfile = arg
        elif opt == '-r':
            regions = eval(arg)
    print(str(directAllo(inputfile, regions)))

if __name__ == "__main__":
    dojob(sys.argv[1:])
