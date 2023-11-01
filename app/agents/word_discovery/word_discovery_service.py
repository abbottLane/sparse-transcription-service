from app.data_access.schemas import AlignedToken, DiscoverWordsModel
import asyncio
import json
import re
import ast

async def initiate_discovery(task_data: DiscoverWordsModel):
    # From input objects, construct the input the FST expects
    phone_str = "".join(task_data["phone_str"].split())
    sorted_aligned_tokens = sorted(task_data["aligned_tokens"], key=lambda x: x["start"])
    res = []
    i = 0
    known_tokens = []
    for tok in sorted_aligned_tokens:
        known_tokens.append(tok["token"])
        res.append(" ".join(phone_str[i:tok["start"]] + " ") + tok["token"] + " ")
        i = tok["stop"] + 1
    res.append(" ".join(phone_str[i:]))
    imputed_str = "".join(res)
    imputed_str = re.sub(" +", " ", imputed_str) # the nature of loops means sometimes we have two whitespace between characters. just replace with single whitespace

    print("Calling word discovery subprocess on: " + imputed_str)
    subprocess_call = ". alloenv/bin/activate && " + 'python app/agents/word_discovery/find_words.py -i "' + imputed_str + '"'
    proc = await asyncio.create_subprocess_shell(
        subprocess_call,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
        )
    stdout, stderr = await proc.communicate()

    str_form = stdout.decode().strip()
    print("STDERR: " + stderr.decode().strip())

    list_form = ast.literal_eval(str_form)
    offset_stripped = [re.sub("-", "", x) for x in list_form]

    # filter out all responses which are not grounded in an identified lexeme
    grounded_results = ["".join(x.split()) for x in offset_stripped if has_overlap(x.split(), known_tokens)]
    return grounded_results

def has_overlap(list1, list2):
    return bool(set(list1) & set(list2))