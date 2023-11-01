import argparse
import re
from HFST_Model import HFSTModel

HFST_MODEL = HFSTModel("app/agents/word_discovery/FST/kunwok-acceptor.min.bin.hfst")
ORTH_PATTERN = re.compile('bb|kk|ng|dd|rdd|rd|rn|rl|rr|djdj|dj|nj|rr|b|m|k|g|d|n|l|r|y|h|d|a|e|i|o|u|.') # Defines the graphemes of Kunwinjku orthography

def main(line: str):   
    # # test: remove line below later
    # line = "k ɐ bolk n ɐ n"
    results = HFST_MODEL.apply_down(" " + line.rstrip() + " ") # pad with blank space on both side so we catch beginning words
    print(results)
    #results = combine_results(results)

    #print(line.rstrip() + "\n" + "\n".join(results) + "\n")

def combine_results(results):
    # First, convert results to spans
    matches = []
    for r in results: 
        new_r = re.findall(ORTH_PATTERN, r)
        new_match = None
        last_grapheme = "-"
        for i, current_grapheme in enumerate(new_r):
            if current_grapheme != "-" and last_grapheme == "-": # start a new match
                new_match = FSTMatch(start=i)
                new_match.add_char(current_grapheme)
                last_grapheme = current_grapheme
            elif current_grapheme != "-" and last_grapheme != "-": # continue a match
                new_match.add_char(current_grapheme)
                last_grapheme = current_grapheme
                if len(new_r)-1 == i: # we are at the end of the string, and need to close it out
                    new_match.stop = i
                    matches.append(new_match)
            elif current_grapheme =="-" and last_grapheme != "-": # close out a match
                new_match.stop = i
                last_grapheme = current_grapheme
                matches.append(new_match)
            
    # Second, keep only the longest spans which do not overlap
    #   The intuition here is that if the list is sorted with the logest matches on top,
    #   then we can simply keep the first match, and check all subsequent matches for occurence within the same span.
    #   If they do, we ignore them, if they dont, we have found the next longest, non-overlapping match.
    sorted_matches = [k for k in sorted(matches, key=lambda x: len(x.char_seq), reverse=True)]
    matches=None
    keep = []
    keep_ranges=set()
    for match in sorted_matches:
        match_idx_set = set(range(match.start, match.stop))
        if match_idx_set.isdisjoint(keep_ranges):
            keep.append(match)
            keep_ranges = keep_ranges.union(match_idx_set)
    return keep

class FSTMatch:
    def __init__(self, start):
        self.start = start
        self.stop = None
        self.char_seq = []

    def get_len(self):
        return len(self.char_seq)
    
    def add_char(self, c):
        self.char_seq.append(c)
    
    def __str__(self):
        return "{char_seq:" + str(self.char_seq) + ", start: " + str(self.start) + ", stop: " + str(self.stop) + "}"
    
    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find words in a stream of phones')
    parser.add_argument('-i', help="phone string with imputed lexemes")
    args = parser.parse_args()
    main(args.i)