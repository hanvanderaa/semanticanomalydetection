from knowledge_base.KnowledgeRecord import KnowledgeRecord, Observation
from nltk.corpus import wordnet
from collections import Counter
from nltk.stem import WordNetLemmatizer


class KnowledgeBase:

    def __init__(self):
        self.verb_to_records = {}
        self.pair_to_record = {}
        self.verb_counts = Counter()

    def get_record(self, verb1, verb2):
        verb1 = lemmatize_word(verb1)
        verb2 = lemmatize_word(verb2)
        if (verb1, verb2) in self.pair_to_record:
            return self.pair_to_record[(verb1, verb2)]
        if (verb2, verb1) in self.pair_to_record:
            return self.pair_to_record[(verb2, verb1)]
        return None

    def add_verb_occurrence(self, verb):
        self.verb_counts[verb] += 1

    def add_observation(self, verb1, verb2, observation_type):
        self.add_new_record(verb1, verb2)
        if observation_type in (Observation.V1_BEFORE_V2, Observation.V2_BEFORE_V1):
            self._add_ordered_observation(verb1, verb2, observation_type)
        self.get_record(verb1, verb2).add_observation(observation_type)

    def _add_ordered_observation(self, verb1, verb2, observation_type):
        record = self.get_record(verb1, verb2)
        # check if observation order should be reversed
        if record.verb1 != verb1:
            observation_type = Observation.V1_BEFORE_V2 if observation_type == Observation.V2_BEFORE_V1 else Observation.V2_BEFORE_V1
        record.add_observation(observation_type)

    def add_new_record(self, verb1, verb2):
        verb1 = lemmatize_word(verb1)
        verb2 = lemmatize_word(verb2)
        if self.get_record(verb1, verb2) is None:
            new_record = KnowledgeRecord(verb1, verb2)
            self.pair_to_record[(verb1, verb2)] = new_record
            self.verb_to_records[verb1] = self.verb_to_records.get(verb1, set())
            self.verb_to_records[verb2] = self.verb_to_records.get(verb2, set())
            self.verb_to_records[verb1].add(new_record)
            self.verb_to_records[verb2].add(new_record)

    def get_all_records(self, verb):
        return self.verb_to_records[verb]

    def exclusion_violation(self, verb1, verb2):
        if verb1 in _wordnet_antonyms(verb2) or verb2 in _wordnet_antonyms(verb1):
            # print("antonyms found", verb1, verb2)
            return True
        record = self.get_record(verb1, verb2)
        if record is None:
            return False
        return record.observation_counts[Observation.XOR] >= 1

    def ordering_violation(self, verb1, verb2):
        record = self.get_record(verb1, verb2)
        if record is None:
            return False
        if record.verb1 == verb1:
            return record.observation_counts[Observation.V2_BEFORE_V1] >= 1
        if record.verb2 == verb2:
            return record.observation_counts[Observation.V1_BEFORE_V2] >= 1

    def co_occurrence_violation(self, verb1, verb2):
        record = self.get_record(verb1, verb2)
        if record is None:
            return False
        return record.observation_counts[Observation.CO_OCC] >= 1


def _wordnet_antonyms(term):
    antonyms = set()
    for syn in wordnet.synsets(term):
        for l in syn.lemmas():
            if l.antonyms():
                for ant in l.antonyms():
                    antonyms.add(l.antonyms()[0].name())
    return antonyms


lemmatizer = WordNetLemmatizer()


def lemmatize_word(word):
    lemma = lemmatizer.lemmatize(word, pos='v')
    lemma = lemmatizer.lemmatize(lemma, pos='n')
    return lemma
