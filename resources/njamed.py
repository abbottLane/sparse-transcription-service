import json

DICTIONARY_JSON = "resources/njamed_dictionary.json"

def load_entries(glossary_id, user, canonical):
    """Construct glossary entries from Njamed dictionary

    eg:
    {
        "glossary_id":"",
        "form": "yime",
        "gloss": "says",
        "tokens":[],
        "user":"userid123",
        "canonical": False
    }

    Returns:
        dict: Returns an object resembling a glossary entry
    """
    # Opening JSON file 
    f = open(DICTIONARY_JSON,) 
    njamed_entries = json.load(f)
    gloss_mocks = []
    for entry in njamed_entries:
        gloss_mock=dict()
        gloss_mock['glossary_id'] = glossary_id
        gloss_mock['form'] = entry['orth']
        gloss_mock['gloss'] = ""
        gloss_mock['tokens'] = []
        gloss_mock['user'] = user 
        gloss_mock['canonical'] = canonical
        if canonical == True:
            gloss_mock['lexical_entry'] = {
                "translation": entry['translation'],
                "examples": entry['examples'],
                "pos": entry['pos']
            }
        gloss_mocks.append(gloss_mock)
    return gloss_mocks

if __name__ == "__main__":
    load_entries(glossary_id = "GL123", user = "TetsingTesting", canonical = "False")