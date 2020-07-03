#!/usr/bin/python3
"""Preprocessor class.

:class: Preprocessor is used to preprocess text.

  Typical usage example:
  ...

"""

from re import sub
from rnnmorph.predictor import RNNMorphPredictor


class Preprocessor():
    """[summary]
    """

    def __init__(self, batch_size=1):
        """[summary]

        Args:
            batch_size (int, optional): [description]. Defaults to 1.
        """

        self.batch_size = batch_size
        self.predictor = RNNMorphPredictor(language="ru")

    def __del__(self):
        if hasattr(self, 'predictor'):
            del self.predictor

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.predictor = self.predictor
        return result

    def __deepcopy__(self, memodict={}):
        cls = self.__class__
        result = cls.__new__(cls)
        result.predictor = self.predictor
        return result

    def gettags(self, texts: list) -> list:
        """Get morpho tags for the `texts`

        Args:
            texts (list): List of lists

        Raises:
            ValueError: [description]

        Returns:
            list: list of lists -- words and motpho tags
            
        Example:            
            PreProcess.gettags([['я купил самолёт и ракеты'], ['ух ты']])
            [[['<sil>', 'SIL _'],
              ['я', 'PRON Case=Nom|Number=Sing|Person=1'],
              ['купил', 'VERB Gender=Masc|Mood=Ind|Number=Sing|Tense=Past|VerbForm=Fin|Voice=Act'],
              ['самолёт', 'NOUN Case=Acc|Gender=Masc|Number=Sing'],
              ['и', 'CONJ _'],
              ['ракеты', 'NOUN Case=Acc|Gender=Fem|Number=Plur'],
              ['<sil>', 'SIL _']],
             [['<sil>', 'SIL _'],
              ['ух', 'INTJ _'],
              ['ты', 'PRON Case=Nom|Number=Sing|Person=2'],
              ['<sil>', 'SIL _']]]
        """

        if not isinstance(texts, list):
            raise ValueError(f'Expected `{type([1, 2])}`, but got `{type(texts)}`.')
        if len(texts) == 0:
            return []
        all_phonetic_phrases = []
        all_phrases_for_rnnmorph = []
        for cur_text in texts:
            list_of_phonetic_phrases = [cur.strip() for cur in ' '.join(cur_text).split('<sil>')]
            united_phrase_for_rnnmorph = []
            for phonetic_phrase in list_of_phonetic_phrases:
                if len(phonetic_phrase) > 0:
                    united_phrase_for_rnnmorph += phonetic_phrase.split()
            if len(united_phrase_for_rnnmorph) > 0:
                all_phrases_for_rnnmorph.append(united_phrase_for_rnnmorph)
                all_phonetic_phrases.append(list_of_phonetic_phrases)
            else:
                all_phonetic_phrases.append([])
        if len(all_phrases_for_rnnmorph) > 0:
            all_forms = self.predictor.predict_sentences(all_phrases_for_rnnmorph, \
                                                         batch_size=self.batch_size)
        else:
            all_forms = []
        all_words_and_tags = []
        phrase_ind = 0
        
        for cur in all_phonetic_phrases:
            words_and_tags = [['<sil>', 'SIL _']]
            if len(cur) > 0:
                token_ind = 0
                for phonetic_phrase in cur:
                    if len(phonetic_phrase) > 0:
                        n = len(phonetic_phrase.split(' '))
                        analysis = all_forms[phrase_ind][token_ind:(token_ind + n)]
                        for word in analysis:
                            word_and_tag = []
                            word_and_tag.append(word.word)
                            word_and_tag.append(word.pos + ' ' + word.tag)
                            words_and_tags.append(word_and_tag)
                        words_and_tags.append(['<sil>', 'SIL _'])
                        token_ind += n
                phrase_ind += 1
            all_words_and_tags.append(words_and_tags)
        return all_words_and_tags

    def __call__(self, texts: str):
        """Call the instance like function. Use in pipelines, too."""
        return self.preprocessing(texts)[0]

    def preprocessing(self, texts: str):
        """[summary]

        Args:
            texts (str): Text to preprocess.

        Returns:
            list: A list of processed words and tags.
        """

        def prepare(text: str) -> str:
            """Replace punctuation marks with <sil> tag; remove special symbols."""

            text = sub(r'[\.\,\?\!\(\);:]+', ' <sil>', text.lower())
            text = sub(r' [–-] |\n', ' <sil> ', text)
            text = sub(r'\s{2,}', ' ', text)
            text = sub(r'^\s|(?<!\w)[\\\/@#~¬`£€\$%\^\&\*–_=+\'\"\|«»–-]+', '', text)
            return text.strip().split(' ')

        return self.gettags([prepare(cur) for cur in texts])
