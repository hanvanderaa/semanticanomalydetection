from knowledge_base.KnowledgeBase import KnowledgeBase
from knowledge_base.KnowledgeRecord import Observation

class WorkItemPopulator:

    def __init__(self, weight = 1):
        self.weight = weight
        pass

    def populate(self, knowledge_base: KnowledgeBase):

        # Add each observation "weight" times
        for i in range(1,self.weight):

            knowledge_base.add_observation("create",  "offer", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("create", "allocate", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("create", "start", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("create", "complete", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("create", "fail", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("create", "suspend", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("create", "resume", Observation.V1_BEFORE_V2)

            knowledge_base.add_observation("offer", "allocate", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("offer", "start", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("offer", "complete", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("offer", "fail", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("offer", "suspend", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("offer", "resume", Observation.V1_BEFORE_V2)

            knowledge_base.add_observation("allocate", "start", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("allocate", "complete", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("allocate", "fail", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("allocate", "suspend", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("allocate", "resume", Observation.V1_BEFORE_V2)

            knowledge_base.add_observation("start", "complete", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("start", "fail", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("start", "suspend", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("start", "resume", Observation.V1_BEFORE_V2)

            knowledge_base.add_observation("suspend", "complete", Observation.V1_BEFORE_V2)
            knowledge_base.add_observation("resume", "complete", Observation.V1_BEFORE_V2)

            knowledge_base.add_observation("suspend", "resume", Observation.V1_BEFORE_V2)

            knowledge_base.add_observation("fail", "complete", Observation.XOR)
            knowledge_base.add_observation("fail", "complete", Observation.XOR)

            knowledge_base.add_observation("create", "start", Observation.CO_OCC)
            knowledge_base.add_observation("start", "complete", Observation.CO_OCC)
            knowledge_base.add_observation("suspend", "resume", Observation.CO_OCC)

        return