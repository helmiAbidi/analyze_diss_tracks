import string
import Levenshtein
from difflib import SequenceMatcher
import pyphen
import phonetics


punctuation = string.punctuation.replace("'", "")
translation_table = str.maketrans(punctuation, ' ' * len(punctuation))
similarity_threshold = 0.75
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

####################################### ASSONANCE FUNCTIONS ########################################
def create_phonetic_syllable_represtation(line):
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

def detect_assonance(current_line_vowel_repr, next_line_vowel_repr):
    assonances = []
    i = 0
    while(i<len(current_line_vowel_repr)):
        j = i+1
        assonance = []
        indices_to_delete_current_line = []
        while (j<len(current_line_vowel_repr)):
            if current_line_vowel_repr[i][-1] == current_line_vowel_repr[j][-1]: 
                assonance.append(current_line_vowel_repr[j])
                indices_to_delete_current_line.append(j)
            j+=1

        j = 0
        while (j<len(next_line_vowel_repr)):
            if current_line_vowel_repr[i][-1] == next_line_vowel_repr[j][-1]: 
                assonance.append(next_line_vowel_repr[j])
            j+=1

        if len(assonance):
            assonance.insert(0,current_line_vowel_repr[i])
            assonances.append(list(set(assonance)))
            indices_to_delete_current_line.append(i)
            delete_indices_from_list(current_line_vowel_repr, indices_to_delete_current_line)
        else:
            i+=1
    
    return assonances

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