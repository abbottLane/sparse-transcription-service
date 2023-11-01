from typing import List
import panphon.distance
import sys
import re
import getopt, sys
import ast


FT = panphon.FeatureTable()
DST = panphon.distance.Distance()
GRAPHEME_PATTERN = re.compile('bb|kk|ng|dd|rdd|rd|rn|rl|rr|djdj|dj|nj|rr|b|m|k|g|d|n|l|r|y|h|d|a|e|i|o|u|.') # Defines the graphems of Kunwinjku orthography
ORTH2IPA = {
    "bb":"b",
    "ng":"ŋ",
    "dd":"t",
    "rdd":"ʈ",
    "rd":"ʈ",
    "rn":"ɳ",
    "rl":"ɭ",
    "rr":"r",
    "djdj":"ɟ",
    "dj":"ɟ",
    "nj":"ɲ",
    "b":"b",
    "m":"m",
    "k":"k",
    "g":"k",
    "d":"t",
    "n":"n",
    "l":"l",
    "r":"ɹ",
    "y":"j",
    "h":"ʔ",
    "d":"t",
    "a":"ɔ",
    "e":"ɛ",
    "i":"ɪ",
    "o":"ɔ",
    "u":"u"  
}

def do_job(argv):
    try:
        opts, _ = getopt.getopt(argv, "p:t:a:", ["ifile="])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(2)
    phones = ""
    tokens = ""
    do_all = False
    for opt, arg in opts:
        if opt == '-t':
            tokens = ast.literal_eval(arg)
        if opt == '-p':
            phones = arg
        if opt == "-a":
            if arg == "true":
                do_all = True
            

    print(align(tokens, phones, do_all=do_all))


def align(tokens, phones, do_all=False):
    top_positions = []
    standardized_phones = standardize_phones(phones)
    for tok in tokens:
        graphemes = re.findall(GRAPHEME_PATTERN, tok)
        ipa = transform(graphemes)

        distance_and_position = []
        # slide ipa str accross phone sequence and pick the likely hits
        for position, ch in enumerate(standardized_phones):
            # tok_ft = FT.word_fts(ipa)
            # ref_ft = FT.word_fts(standardize_phones[position:len(ipa)])
            sub_seq = standardized_phones[position:position+len(ipa)]
            distance = DST.feature_edit_distance(ipa, sub_seq)
            distance_and_position.append(
                {
                    "distance": distance/len(ipa),
                    "start": position,
                    "stop": position + len(ipa) - 1
                }
            )
        if not do_all:
            top_positions.append({"token": tok, "alignment": [min(distance_and_position, key=lambda x: x['distance'])]})
        else:
            top_positions.append({"token": tok, "alignment": distance_and_position})
    return top_positions

def transform(graphemes: List[str]) -> str:
    new_str = ""
    for grapheme in graphemes:
        if grapheme in ORTH2IPA:
            new_str += ORTH2IPA[grapheme]
        else:
            new_str += grapheme
    return new_str

def standardize_phones(phones : str):
    """We are given a string of phones, possibly space delineated, possibly not. Lets just clean up the string to standardized form

    Args:
        phones (str): a str representing a phone sequence
    """
    phones = re.sub(" +", "", phones)
    return phones

if __name__ == "__main__":
    if len(sys.argv) > 1:
        do_job(sys.argv[1:])
    else:
        print(align(tokens = ['na'], phones="n ɐ j ɪ n w ɔ ɣ ɛ ə"))