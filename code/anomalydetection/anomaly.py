class Anomaly:

    def __init__(self, anomaly_type, event1, event2, verb1, verb2, record_count):
        self.anomaly_type = str(anomaly_type).split('.')[-1]
        self.event1 = event1
        self.event2 = event2
        self.verb1 = verb1
        self.verb2 = verb2
        self.record_count = record_count

    def __repr__(self):
        return self.anomaly_type + ": " + self.event1 + "---" + self.event2 +  \
               " record: (" + self.verb1 + ", " + self.verb2 + ", conf: " + str(self.record_count) + ")"

    def to_array(self):
        return [self.anomaly_type, self.event1, self.event2, self.verb1, self.verb2, self.record_count]

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()