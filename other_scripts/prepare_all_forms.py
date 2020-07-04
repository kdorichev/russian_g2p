#!/usr/bin/python3
"""Prepare All_forms dictionary (json) from source text file.
    Usage: python prepare_all_forms.py input_dictionary.txt prepared_dictionary.json
"""

import json
import os
import sys
import codecs

from functools import reduce
import pymorphy2
from russian_tagsets import converters


rus_letters = set('а б в г д е ё ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ы ь э ю я'.split())
rus_vowels = set('а о у э ы и я ё ю е'.split())

def remove_accent(word: str) -> str:
    """Remove accent characters from the `word`."""
    return ''.join(list(filter(lambda character: character not in {'\'', '`'}, word)))

def check_source_word(word: str) -> bool:
    """Check all the characters in the `word` are in Russian alphabet and no other."""
    if not all([c in (rus_letters | {'-'}) for c in word.lower()]):
        return False
    return len(set(word.lower()) & rus_letters) > 0

def load_accents_dictionary(file_name: str) -> dict:
    """Load all forms source dictionary from txt file and prepare json file.

    Args:
        file_name (str): Path to All forms dictionary source ZipFile The class for reading and writing ZIP files.  See section 
        File format -- lines in the following form:
        друг#дру'г,друзья',дру'га,друзе'й,дру'гу,друзья'м,дру'га,друзе'й,дру'гом,друзья'ми,дру'ге,друзья'х
        
    Returns:
        dict: All forms dictionary
    """

    words_and_accents = dict()
    with codecs.open(file_name, mode='r', encoding='utf-8', errors='ignore') as dict_file:
        cur_line = dict_file.readline()
        cur_line_idx = 1
        while len(cur_line):
            prepared_line = cur_line.strip()
            error_message = f"File `{file_name}`, line {cur_line_idx}: incorrect entry: "
    
            if len(prepared_line):
                line_parts = prepared_line.split('#')
                assert len(line_parts) == 2, error_message
                source_lemma = line_parts[0].strip().lower()
                assert len(source_lemma) > 0, error_message
                assert check_source_word(source_lemma), error_message
                wordforms = set(filter(
                    lambda a: len(a) > 0,
                    map(lambda b: b.strip(), line_parts[1].split(','))
                ))
                assert len(wordforms) > 0, error_message
                is_found = False
                for cur_wordform in wordforms:
                    if source_lemma == remove_accent(cur_wordform):
                        is_found = True
                        break
                assert is_found, error_message
                for cur_wordform in wordforms:
                    prepared_wordform = remove_accent(cur_wordform).lower()
                    assert check_source_word(prepared_wordform), error_message
                    accented_wordform = cur_wordform.replace('\'', '+').replace('`', '').lower()
                    if '+' not in accented_wordform:
                        yo_ind = accented_wordform.find('ё')
                        if yo_ind < 0:
                            yo_ind = accented_wordform.find('Ё')
                        if yo_ind >= 0:
                            accented_wordform = accented_wordform[0:(yo_ind + 1)] + '+' \
                                                + accented_wordform[(yo_ind + 1):]
                    if '+' in accented_wordform:
                        ok = True
                    else:
                        vocals_number = reduce(lambda a, b: (a + 1) if b in rus_vowels else a, accented_wordform, 0)
                        ok = (vocals_number < 2)
                    if ok:
                        if prepared_wordform in words_and_accents:
                            if accented_wordform not in words_and_accents[prepared_wordform]:
                                words_and_accents[prepared_wordform][accented_wordform] = source_lemma
                        else:
                            words_and_accents[prepared_wordform] = {accented_wordform: source_lemma}
            cur_line = dict_file.readline()
            cur_line_idx += 1

    assert len(words_and_accents) > 0, \
        f'{file_name}: the accents dictionary cannot be loaded from this file!'
    return words_and_accents


def main():
    """Prepare the dictionary script."""
    if sys.argv.__len__() != 3:
        print("Usage: input_dictionary.txt prepared_dictionary.json")
        return

    source_dictionary_name = os.path.normpath(sys.argv[1])
    prepared_dictionary_name = os.path.normpath(sys.argv[2])
    
    words_and_accents = load_accents_dictionary(source_dictionary_name)
    simple_wordsforms = list()
    homonyms = dict()
    morph = pymorphy2.MorphAnalyzer()
    to_ud20 = converters.converter('opencorpora-int', 'ud20')

    for cur_word in words_and_accents:
        variants_of_accents = sorted(list(words_and_accents[cur_word].keys()))
        if len(variants_of_accents) > 1:
            lemmas = set(words_and_accents[cur_word].values())
            str_width = len(str(len(variants_of_accents)))
            homonyms[cur_word] = {}
            if len(lemmas) == len(variants_of_accents):
                for ind in range(len(variants_of_accents)):
                    lemma = words_and_accents[cur_word][variants_of_accents[ind]]
                    morpho_variants = morph.parse(cur_word)
                    best_morpho = None
                    for cur_morpho in morpho_variants:
                        if cur_morpho.normal_form == lemma:
                            best_morpho = cur_morpho
                            break
                    if best_morpho is None:
                        best_similarity = 0
                        for cur_morpho in morpho_variants:
                            if cur_morpho.normal_form.startswith(lemma) or lemma.startswith(cur_morpho.normal_form):
                                cur_similarity = min(len(lemma), len(cur_morpho.normal_form))
                                if cur_similarity > best_similarity:
                                    best_morpho = cur_morpho
                                    best_similarity = cur_similarity
                    if best_morpho is None:
                        homonyms[cur_word]['{0:>0{1}}'.format(ind + 1, str_width)] = variants_of_accents[ind]
                    else:
                        if str(best_morpho.methods_stack[0][0]) == '<DictionaryAnalyzer>':
                            morpho_tag = to_ud20(str(best_morpho.tag))
                            if morpho_tag in homonyms[cur_word]:
                                counter = 2
                                while (morpho_tag + '({0})'.format(counter)) in homonyms[cur_word]:
                                    counter += 1
                                morpho_tag += '({0})'.format(counter)
                            homonyms[cur_word][morpho_tag] = variants_of_accents[ind]
                        else:
                            homonyms[cur_word]['{0:>0{1}}'.format(ind + 1, str_width)] = variants_of_accents[ind]
            else:
                if len(lemmas) == 1:
                    lemma_morpho = morph.parse(list(lemmas)[0])[0]
                    if str(lemma_morpho.methods_stack[0][0]) == '<DictionaryAnalyzer>':
                        lexeme_counter = 0
                        for it in lemma_morpho.lexeme:
                            if it.word == cur_word:
                                lexeme_counter += 1
                        if lexeme_counter == 1:
                            simple_wordsforms.append(variants_of_accents[0])
                            del homonyms[cur_word]
                        else:
                            for ind in range(len(variants_of_accents)):
                                variant_name = '{0:>0{1}}'.format(ind + 1, str_width)
                                homonyms[cur_word][variant_name] = variants_of_accents[ind]
                    else:
                        for ind in range(len(variants_of_accents)):
                            homonyms[cur_word]['{0:>0{1}}'.format(ind + 1, str_width)] = variants_of_accents[ind]
                else:
                    for ind in range(len(variants_of_accents)):
                        homonyms[cur_word]['{0:>0{1}}'.format(ind + 1, str_width)] = variants_of_accents[ind]
        else:
            simple_wordsforms.append(variants_of_accents[0])
    print(f"`{source_dictionary_name}`: dictionary has been loaded from this file.")
    with codecs.open(prepared_dictionary_name, mode='w', encoding='utf-8', errors='ignore') as fp:
        json.dump([homonyms, sorted(simple_wordsforms)], fp, ensure_ascii=False, indent=4, sort_keys=True)
    print(f"`{prepared_dictionary_name}`: dictionary has been saved into this file.")
    print(f"Number of homonyms: {len(homonyms)}.")


if __name__ == '__main__':
    main()
