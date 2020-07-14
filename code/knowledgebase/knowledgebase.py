from knowledgebase.knowledgerecord import KnowledgeRecord, Observation
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import labelparser.labelparser as lp


class KnowledgeBase:

    def __init__(self):
        self.record_map = {}

    def get_record(self, verb1, verb2, record_type):
        verb1 = lp.lemmatize_word(verb1)
        verb2 = lp.lemmatize_word(verb2)
        # symmetric XOR records are always stored in lexical order
        if record_type == Observation.XOR and verb2 > verb1:
            verb1, verb2 = verb2, verb1
        if (verb1, verb2, record_type) in self.record_map:
            return self.record_map[(verb1, verb2, record_type)]
        return None

    def get_record_count(self, verb1, verb2, record_type):
        record = self.get_record(verb1, verb2, record_type)
        if record is None:
            return 0
        return record.count

    def add_observation(self, verb1, verb2, record_type, count=1):
        record = self.get_record(verb1, verb2, record_type)
        if record:
            record.increment_count(count)
        else:
            self.add_new_record(verb1, verb2, record_type, count)

    def add_new_record(self, verb1, verb2, record_type, count):
        verb1 = lp.lemmatize_word(verb1)
        verb2 = lp.lemmatize_word(verb2)
        # ensure consistent ordering for symmetric XOR records
        if record_type == Observation.XOR and verb2 > verb1:
            verb1, verb2 = verb2, verb1
        self.record_map[(verb1, verb2, record_type)] = KnowledgeRecord(verb1, verb2, record_type, count)

    def exclusion_violation(self, verb1, verb2, min_count=1):
        return self.get_record_count(verb1, verb2, Observation.XOR) >= min_count

    def ordering_violation(self, verb1, verb2, min_count=1):
        return self.get_record_count(verb2, verb1, Observation.ORDER) >= min_count

    def co_occurrence_dependency(self, verb1, verb2, min_count=1):
        return self.get_record_count(verb1, verb2, Observation.CO_OCC) >= min_count

    def filter_out_conflicting_records(self):
        new_map = {}
        for (verb1, verb2, record_type) in self.record_map:
            # filter out conflicting exclusion constraints
            # logic: if there is a cooccurrence or order constraint involving two verbs, then they cannot be exclusive
            if record_type == Observation.XOR:
                record_count = self.get_record_count(verb1, verb2, record_type)
                other_counts = self.get_record_count(verb1, verb2, Observation.CO_OCC) + \
                            self.get_record_count(verb1, verb2, Observation.ORDER) + \
                            self.get_record_count(verb2, verb1, Observation.ORDER)
                if record_count > other_counts:
                    new_map[(verb1, verb2, record_type)] = self.record_map[(verb1, verb2, record_type)]
            # filter out conflicting ordering constraints
            # logic: only keep this order constraint if the reverse is less common
            if record_type == Observation.ORDER:
                order_count = self.get_record_count(verb1, verb2, record_type)
                reverse_count = self.get_record_count(verb2, verb1, record_type)
                if order_count > reverse_count:
                    new_map[(verb1, verb2, record_type)] = self.record_map[(verb1, verb2, record_type)]
            # filter out conflicting co-occurrence constraints
            if record_type == Observation.CO_OCC:
                new_map[(verb1, verb2, record_type)] = self.record_map[(verb1, verb2, record_type)]
                # co_occ_count = self.get_record_count(verb1, verb2, record_type)
                # xor_count = self.get_record_count(verb1, verb2, Observation.XOR)
                # if co_occ_count > xor_count:
                #     new_map[(verb1, verb2, record_type)] = self.record_map[(verb1, verb2, record_type)]
                # else:
                #     print('removing', (verb1, verb2, record_type, co_occ_count), "from kb. XOR count:",
                #           xor_count)
        self.record_map = new_map


    # def get_record_numbers(self):
    #     count_order = len([record for record in self.record_map.values() if record.record_type == Observation.ORDER])
    #     count_xor = len([record for record in self.record_map.values() if record.record_type == Observation.XOR])
    #     count_coocc = len([record for record in self.record_map.values() if record.record_type == Observation.CO_OCC])
    #     return (count_xor, count_order, count_coocc, len(self.record_map))
    #
    # def sort_records_by_confidence(self):
    #     newlist = sorted(self.record_map.values(), key=lambda x: x.count, reverse=True)
    #     for i in range(0, 20):
    #         print(newlist[i])
