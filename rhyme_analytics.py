import string
import Levenshtein
from difflib import SequenceMatcher
from better_profanity import profanity
import pyphen
import phonetics


punctuation = string.punctuation.replace("'", "")
translation_table = str.maketrans(punctuation, ' ' * len(punctuation))
similarity_threshold = 0.75
# Create an instance of the Pyphen class using the 'en' dictionary for English language
dic = pyphen.Pyphen(lang='en_US')

####################################### PREPROCESSING FUNCTIONS ########################################
def remove_extra_spaces(input_string):
    # Split the string into words and join them with a single space
    return ' '.join(input_string.split())

def clean_line(line):
    line = line.replace("\n", " ")
    line = line.replace("\r", " ")

    # Replace punctuation marks with spaces
    line = line.translate(translation_table)
    line = remove_extra_spaces(line)
    return line


####################################### MULTI_RHYME FUNCTIONS ########################################
def levenshtein_similarity(str1, str2):
    # Calculate the Levenshtein distance
    distance = Levenshtein.distance(str1, str2)
    # Calculate the similarity ratio
    similarity = 1 - (distance / max(len(str1), len(str2)))
    return similarity

def difflib_similarity(str1, str2):
    # Create a SequenceMatcher object
    matcher = SequenceMatcher(None, str1, str2)
    # Calculate the similarity ratio
    similarity = matcher.ratio()
    return similarity

def detect_multi_rhymes(current_line_syllables, next_line_syllables):
    ## for each syllable in the current line check current line and next line. 
    # if you find matching syllables, start concatenating the matching syllable strings, stop when the similarity is under a specific threshold
    ## Sample input
    ## current_line_syllables = ["A", "B", "C"]
    ## next_line_syllables = ["D", "B", "C"]
    i=0
    mutli_rhymes = []

    while(i<(len(current_line_syllables)-1)):

        j,extension = 0, 0
        lookup_field = current_line_syllables[i+1:] + next_line_syllables

        while((i+extension)<len(current_line_syllables) and (j+extension) < len(lookup_field)): 
            str1 = ' '.join(current_line_syllables[i:i+1+extension])
            str2 = ' '.join(lookup_field[j:j+1+extension])

            similarity = difflib_similarity(str1, str2)
            if similarity >= similarity_threshold:
                extension +=1
            elif similarity<similarity_threshold and extension >1:
                break
            elif similarity<similarity_threshold and extension <=1:
                j+=1
                extension = 0
        
        if extension >1:
            mutli_rhyme = (current_line_syllables[i:i+extension],lookup_field[j:j+extension])   
            mutli_rhymes.append(mutli_rhyme)
        
        i = i+extension+1
    
    return mutli_rhymes

def detect_song_multi_rhymes(song_lines):
    # for each line -> create syllable phonetic representation of current & next line --> call the multi function
    # -> in case you find something add it to a dict: key:line number -> value: multi tuple. 
    multi_rhymes = {}
    for line_index in range(len(song_lines)-1):
        _,current_line_syllables_ph=create_phonetic_syllable_representation(song_lines[line_index])
        _,next_line_syllables_ph=create_phonetic_syllable_representation(song_lines[line_index+1])
        
        multi_rhyme = detect_multi_rhymes(current_line_syllables_ph, next_line_syllables_ph)
        if multi_rhyme is not None:
            multi_rhymes[line_index] = multi_rhyme
    
    return multi_rhymes

def compute_multi_rhyme_analytics(multi_rhymes, song_lenght):

    number_multi_rhymes, average_len_multi_rhymes, multi_rhyme_score = 0,0,0
    for index, (key,value) in enumerate(multi_rhymes.items()):
        if len(value)>0:
            number_multi_rhymes += 1
            average_len_multi_rhymes += len(value[0])
            for rhyme in value:
                multi_rhyme_score += len(rhyme[0]) 

    average_len_multi_rhymes = average_len_multi_rhymes/number_multi_rhymes
    multi_rhyme_score = multi_rhyme_score/song_lenght
    return number_multi_rhymes, average_len_multi_rhymes, multi_rhyme_score

####################################### ASSONANCE FUNCTIONS ########################################
def create_phonetic_syllable_representation(line):
    words_list = line.split(" ")
    line_syllables,line_syllables_ph = [],[]

    for word in words_list:
        syllables = dic.inserted(word).split('-')
        line_syllables.extend(syllables)
        for syllable in syllables:
            line_syllables_ph.append(phonetics.metaphone(syllable))
    return line_syllables,line_syllables_ph

def cut_at_last_vowel(line):
    vowels = "aeiou"
    words = line.split(" ")
    line_vowel_repr = []

    for word in words:
        last_vowel_pos = -1

        # Find the position of the last vowel
        for i, char in enumerate(reversed(word.lower())):
            if char in vowels:
                last_vowel_pos = len(word) - 1 - i
                break
    
        # If no vowel is found, return the original string
        if last_vowel_pos != -1:
            line_vowel_repr.append(word[:last_vowel_pos + 1].lower()) 

    return line_vowel_repr

def delete_indices_from_list(input_list, indices_to_delete):
    # Sort the indices in reverse order
    indices_to_delete = sorted(indices_to_delete, reverse=True)
    
    # Delete elements at the specified indices
    for index in indices_to_delete:
        del input_list[index]
    
    return input_list

def detect_assonance(current_line_vowel_repr, next_line_vowel_repr, line_index):
    assonances_dict =  {"A": {line_index:[],line_index+1:[]}, "O": {line_index:[],line_index+1:[]},
                         "E": {line_index:[],line_index+1:[]}, "I": {line_index:[],line_index+1:[]},
                           "U": {line_index:[],line_index+1:[]}}
    assonances = []
    i = 0
    while(i<len(current_line_vowel_repr)):
        j = i+1
        assonance = []
        indices_to_delete_current_line = []
        while (j<len(current_line_vowel_repr)):
            if current_line_vowel_repr[i][-1] == current_line_vowel_repr[j][-1]:
                assonance.append(current_line_vowel_repr[j])
                assonances_dict[current_line_vowel_repr[i][-1].upper()][line_index].append(current_line_vowel_repr[j]) 
                indices_to_delete_current_line.append(j)
            j+=1

        j = 0
        while (j<len(next_line_vowel_repr)):
            if current_line_vowel_repr[i][-1] == next_line_vowel_repr[j][-1]: 
                assonance.append(next_line_vowel_repr[j])
                assonances_dict[current_line_vowel_repr[i][-1].upper()][line_index+1].append(next_line_vowel_repr[j]) 

            j+=1

        if len(assonance):
            assonances_dict[current_line_vowel_repr[i][-1].upper()][line_index].insert(0,current_line_vowel_repr[i])
            assonances_dict[current_line_vowel_repr[i][-1].upper()][line_index] = list(set(assonances_dict[current_line_vowel_repr[i][-1].upper()][line_index]))
            assonances_dict[current_line_vowel_repr[i][-1].upper()][line_index+1] = list(set(assonances_dict[current_line_vowel_repr[i][-1].upper()][line_index+1])) 

            assonance.insert(0,current_line_vowel_repr[i])
            assonances.append(list(set(assonance)))
            indices_to_delete_current_line.append(i)
            delete_indices_from_list(current_line_vowel_repr, indices_to_delete_current_line)
        else:
            i+=1
    
    return assonances,assonances_dict

def detect_song_assonance(song_lines):
    vowels_dict = {"A": {}, "O": {}, "E": {}, "I": {}, "U": {}}
    assonances = {}

    for line_index in range(len(song_lines)-1):
        current_line_vowel_repr = cut_at_last_vowel(song_lines[line_index])
        if not len(current_line_vowel_repr):
            continue
        next_line_vowel_repr = cut_at_last_vowel(song_lines[line_index+1])
        
        assonance,assonance_dict  = detect_assonance(current_line_vowel_repr, next_line_vowel_repr,line_index)

        if len(assonance):
            ## fill assonances dict
            assonances[line_index] = assonance
            ### fill vowels dict
            for key,value in assonance_dict.items():
                # if the key to the line index exists, create the union of two lists. 
                # if it doesn't, add new key to the dictionary.
                if line_index in vowels_dict[key].keys():
                    vowels_dict[key][line_index] = list(set(vowels_dict[key][line_index]) | set(assonance_dict[key][line_index]))
                else:
                    vowels_dict[key][line_index] = assonance_dict[key][line_index]

                if (line_index+1) in vowels_dict[key].keys():
                    vowels_dict[key][line_index+1] = list(set(vowels_dict[key][line_index+1]) | set(assonance_dict[key][line_index+1]))
                else:
                    vowels_dict[key][line_index+1] = assonance_dict[key][line_index+1]    
    
    return assonances,vowels_dict    

def compute_assonance_score(vowels_dict,lines_length):
    ## calculate assonance score 
    assonance_score = 0
    for vowel,value in vowels_dict.items():
        assonance_score+=sum(len(value) for value in vowels_dict[vowel].values())
    assonance_score = assonance_score/lines_length
    
    return assonance_score
####################################### RHYME SCHEMES FUNCTIONS ########################################
def add_to_rhyme_schemes(dictionary, key_, value_):
    if key_ not in dictionary:
        dictionary[key_] = [value_]
    else:
        dictionary[key_].append(value_)
    return dictionary

def are_lists_equal(list1, list2):
    set1 = set(map(tuple, list1))
    set2 = set(map(tuple, list2))
    return set1 == set2

def analyze_line_endings(line_endings):
    # Dictionary to store character information
    char_info = {}

    # Iterate over the string to collect information
    for index, char in enumerate(line_endings):
        if char not in char_info:
            char_info[char] = {'count': 0, 'indices': []}
        char_info[char]['count'] += 1
        char_info[char]['indices'].append(index)
    
    list_indices=[] 
    for k,v in char_info.items():
        list_indices.append(v["indices"])

    return char_info,list_indices

def detect_song_rhyme_schemes(song_lines):
    rhyme_schemes = {}
    line_index = 0
    while(line_index<len(song_lines)-3):
        remaining_lines = len(song_lines)-line_index
        four_line_endings = song_lines[line_index][-1] + song_lines[line_index+1][-1] + song_lines[line_index+2][-1] + song_lines[line_index+3][-1]

        if remaining_lines >5:
            six_line_endings = four_line_endings + song_lines[line_index+4][-1] + song_lines[line_index+5][-1]
            six_line_info, list_indices = analyze_line_endings(six_line_endings)

            unique_chars = len(six_line_info)
            match unique_chars:
                case 1:
                    pass
                case 2:
                    #check if it's AABAAB otherwise pass.
                    scheme_AABAAB = are_lists_equal(list_indices, [[0,1,3,4], [2,5]])
                    if scheme_AABAAB:
                        rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "AABAAB", song_lines[line_index:line_index+6])
                        scheme_AABAAB = False
                        line_index += 6
                        continue
                    pass
                    
                case 3:
                    #check if it's AABCCB otherwise pass.
                    scheme_AABCCB = are_lists_equal(list_indices, [[0,1], [2,5], [3,4]])
                    if scheme_AABCCB:
                        rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "AABCCB", song_lines[line_index:line_index+6])
                        scheme_AABCCB = False
                        line_index += 6
                        continue
                    pass
                case 4:
                    pass
                case 5:
                    #check if it's XXAXXA otherwise pass.
                    scheme_XXAXXA = are_lists_equal(list_indices, [[0],[1],[2,5], [3],[4]]) 
                    if scheme_XXAXXA:
                        rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "XXAXXA", song_lines[line_index:line_index+6])
                        scheme_XXAXXA = False
                        line_index += 6
                        continue
                    pass
                case 6:
                    line_index+=1
                    continue #no rhyme scheme found.
        
        
        four_line_info, list_indices = analyze_line_endings(four_line_endings)



        unique_chars = len(four_line_info)

        match unique_chars:
            case 1:
                rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "AAAA", song_lines[line_index:line_index+4])
                line_index += 4
                continue
            case 2:
                # can be ABAB, AABB, ABBA,AAXA
                scheme_ABAB = are_lists_equal(list_indices, [[0,2],[1,3]])
                if scheme_ABAB:
                    rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "ABAB", song_lines[line_index:line_index+4])
                    scheme_ABAB = False
                    line_index += 4
                    continue
                
                scheme_AABB = are_lists_equal(list_indices, [[0,1], [2,3]])
                if scheme_AABB:
                    rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "AABB", song_lines[line_index:line_index+4])
                    scheme_AABB = False
                    line_index += 4
                    continue

                scheme_ABBA = are_lists_equal(list_indices, [[0,3], [1,2]])
                if scheme_ABBA:
                    rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "ABBA", song_lines[line_index:line_index+4])
                    scheme_ABBA = False
                    line_index += 4
                    continue

                scheme_AAXA = are_lists_equal(list_indices, [[0,1,3], [2]])
                if scheme_AAXA:
                    rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "AAXA", song_lines[line_index:line_index+4])
                    scheme_AAXA = False
                    line_index += 4
                    continue

                pass
            case 3:
                #can be XAXA, AXXA
                scheme_XAXA = are_lists_equal(list_indices, [[0],[1,3],[2]])
                if scheme_XAXA:
                    rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "XAXA", song_lines[line_index:line_index+4])
                    scheme_XAXA = False
                    line_index += 4
                    continue
                
                scheme_AXXA = are_lists_equal(list_indices, [[0,3],[1], [2]])
                if scheme_AXXA:
                    rhyme_schemes = add_to_rhyme_schemes(rhyme_schemes, "AXXA", song_lines[line_index:line_index+4])
                    scheme_AXXA = False
                    line_index += 4
                    continue
                pass
            case 4:
                line_index += 1
                continue # no rhyme scheme found
        line_index += 1
    
    return rhyme_schemes

def compute_rhyme_schemes_score(rhyme_schemes, lines_length):
    rhyme_schemes_score = 0
    for k,v in rhyme_schemes.items():
        rhyme_schemes_score += len(v) * len(k)

    rhyme_schemes_score = rhyme_schemes_score/lines_length
    
    return rhyme_schemes_score

####################################### PROFANITY FUNCTIONS ########################################
def compute_profanity_score(song_words):
    profanity_score = len(song_words)
    for word in song_words:
        if profanity.contains_profanity(word):
            profanity_score-=1
    
    profanity_score = profanity_score/len(song_words)

    return profanity_score