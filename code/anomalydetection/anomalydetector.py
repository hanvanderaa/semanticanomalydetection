from collections import Counter
from anomalydetection.anomaly import Anomaly
from knowledgebase.knowledgerecord import Observation
import labelparser.labelparser as lp


class AnomalyDetector:

    def __init__(self, kb, log, log_name, event_key, equal_bos, heuristic_parsing):
        self.kb = kb
        self.log = log
        self.log_name = log_name
        self.event_key = event_key
        self.equal_bos = equal_bos
        self.heuristic_parsing = heuristic_parsing
        self.parse_map = {}
        self.anomaly_counter = Counter()
        self.paired_anomaly_map = {}
        self.coocc_pairs = set()
        self.parser = lp.load_default_parser()

    def detect_anomalies(self):
        print("checking for anomalies in", self.log_name, "with", len(self.log), "traces")
        # first parse over all traces
        for id in range(len(self.log)):
            self.detect_anomalies_in_trace(self.log[id])
        # determine actual co-occurrence anomalies based on observed co-occurrence pairs
        for id in range(len(self.log)):
            self.identify_real_cooccurrence_anomalies(self.log[id])
        return self.anomaly_counter

    def detect_anomalies_in_trace(self, trace):
        for i in range(len(trace) - 1):
            for j in range(i + 1, len(trace)):
                pair_anomalies = self.detect_anomalies_for_pair(trace[i], trace[j])
                for anomaly in pair_anomalies:
                    self.anomaly_counter[anomaly] += 1

    def detect_anomalies_for_pair(self, event1, event2):
        event1_name = self.get_event_name(event1)
        event2_name = self.get_event_name(event2)
        pair_anomalies = set()
        # if pair already observed, return stored violations
        if (event1_name, event2_name) in self.paired_anomaly_map:
            return self.paired_anomaly_map[(event1_name, event2_name)]

        if self.pair_should_be_checked(event1_name, event2_name):
            verb1, verb2 = self.get_verb_pair(event1_name, event2_name)
            # check for exclusion violations
            if self.kb.exclusion_violation(verb1, verb2):
                # sort exclusion anomalies in a consistent manner
                if verb1 > verb2:
                    pair_anomalies.add(Anomaly(Observation.XOR, event1_name, event2_name,
                                               verb1, verb2,
                                               self.kb.get_record_count(verb1, verb2, Observation.XOR)))
                else:
                    pair_anomalies.add(Anomaly(Observation.XOR, event1_name, event2_name,
                                               verb2, verb1,
                                               self.kb.get_record_count(verb1, verb2, Observation.XOR)))
            #  check for ordering violation
            if self.kb.ordering_violation(verb1, verb2):
                pair_anomalies.add(Anomaly(Observation.ORDER, event1_name,
                                           event2_name, verb1, verb2,
                                           self.kb.get_record_count(verb2, verb1, Observation.ORDER)))
            # check for potential co-occurrence violation
            if self.kb.co_occurrence_dependency(verb1, verb2):
                self.coocc_pairs.add((event1_name, event2_name))
                self.coocc_pairs.add((event2_name, event1_name))
        self.paired_anomaly_map[(event1_name, event2_name)] = pair_anomalies
        return pair_anomalies

    def pair_should_be_checked(self, event1_name, event2_name):
        # checking mechanism for regular parser
        if not self.heuristic_parsing:
            # Parse events
            e1_parse = self.parse_event(event1_name)
            e2_parse = self.parse_event(event2_name)
            # check if conditions on business object match are met
            if not self.equal_bos or e1_parse.bos == e2_parse.bos:
                # check if there are actual actions detected
                # if len(e1_parse.actions) > 0 and len(e2_parse.actions) > 0:
                verb1, verb2 = self.get_verb_pair(event1_name, event2_name)
                # check if non-empty verbs and make sure they are not equivalent
                if verb1 and verb2 and not verb1 == verb2:
                    return True
            return False
        #  checking mechanism for heuristic parser
        return lp.differ_by_one_word(event1_name, event2_name)

    def identify_real_cooccurrence_anomalies(self, trace):
        # store all events in trace
        event_names = [str(event[self.event_key]).lower() for event in trace]
        for event in event_names:
            # check if event is part of a co-occurrence pair
            for (event1_name, event2_name) in self.coocc_pairs:
                if event == event1_name and event2_name not in event_names:
                    (verb1, verb2) = self.get_verb_pair(event1_name, event2_name)
                    count = self.kb.get_record_count(verb1, verb2, Observation.CO_OCC)
                    if event1_name < event2_name:
                        anomaly = Anomaly(Observation.CO_OCC, event1_name, event2_name, verb1, verb2, count)
                        self.anomaly_counter[anomaly] += 1
                    else:
                        anomaly = Anomaly(Observation.CO_OCC, event1_name, event2_name, verb2, verb1, count)
                        self.anomaly_counter[anomaly] += 1

    def parse_event(self, event_name):
        if event_name not in self.parse_map:
            self.parse_map[event_name] = self.parser.parse_label(event_name)
        return self.parse_map[event_name]

    def get_event_name(self, event):
        return str(event[self.event_key]).lower()

    def get_verb_pair(self, event1_name, event2_name):
        (verb1, verb2) = (None, None)
        if not self.heuristic_parsing:
            if len(self.parse_event(event1_name).actions) > 0:
                verb1 = self.parse_event(event1_name).actions[0]
            if len(self.parse_event(event2_name).actions) > 0:
                verb2 = self.parse_event(event2_name).actions[0]
        else:
            (verb1, verb2) = lp.get_differences(event1_name, event2_name)
        return verb1, verb2
