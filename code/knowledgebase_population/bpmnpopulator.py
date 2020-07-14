import labelparser.labelparser as lp
from pm4py.objects.petri.importer import pnml as pnml_importer
from knowledgebase.knowledgebase import KnowledgeBase
from knowledgebase.knowledgerecord import Observation
import itertools
import os
import json

class BPMNPopulator:

    def __init__(self, equal_bos=False, heuristic_parser=True):
        self.parser = lp.load_default_parser()
        self.equal_bos = equal_bos
        self.heuristic_parser = heuristic_parser
        self.follows = None
        self.labels = None
        self.tasks = set()
        self.parsed_models = 0
        self.parsed_models_used = 0

    def populate(self, knowledge_base: KnowledgeBase, path_to_directory):

        # Load list of "parsable" models
        with open("input/knowledgebase/ai_file_list.txt") as f:
            parsable_files = f.readlines()
        parsable_files = tuple([x.strip() for x in parsable_files])

        self.parsed_models = 1

        files = os.listdir(path_to_directory)
        files = [f for f in files if (f.endswith("json") and not f.endswith("meta.json"))]
        for i, file in enumerate(files):
            print(f"{i} - ({self.parsed_models}, {self.parsed_models_used}) --------------")
            print(path_to_directory + file)

            # Only use models that can be parsed (the "positive list" was created separately)
            if file.endswith(parsable_files):
               self._populate_from_json(knowledge_base, os.path.abspath(path_to_directory) + "/" + file)
            else:
                print("MODEL SKIPPED")
        print(f"Number of models parsed: {self.parsed_models}")

    # Checks whether considered json file is an English BPMN 2.0 model accordingg to meta file
    def _is_en_bpmn(self,path_to_directory,json_file):
        json_file = json_file.replace(".json",".meta.json")
        with open(os.path.abspath(path_to_directory) + "/" + json_file, 'r') as f:
            data = f.read()
            json_data = json.loads(data)
        mod_language = json_data['model']['modelingLanguage']
        nat_language = json_data['model']['naturalLanguage']
        if mod_language=="bpmn20" and nat_language=="en":
            return True
        else:
            return False

    def _populate_from_json(self, knowledge_base: KnowledgeBase, path_to_json):
        self.follows, self.labels, self.tasks = self._loadJSON(path_to_json)
        print_info = False
        extracted_info = False

        # Clean strings (especially from SAP)
        for l in self.labels.keys():
            self.labels[l] = self.labels[l].replace('\n', ' ').replace('\r', '').replace('  ',' ')

        # Find source and sink shapes (typically events)
        source_shapes = set()
        sink_shapes = set()
        for s in self.follows.keys():

            # Iterate over all shapes except sequence flows
            irrelevant_shapes = ("SequenceFlow", "DataObject", "Pool", "Lane")
            if not self.labels[s].startswith(irrelevant_shapes):
                if len(self._get_postset(s)) == 0:
                    sink_shapes.add(s)
                if len(self._get_preset(s)) == 0:
                    source_shapes.add(s)

        # Print source and sink shapes
        if print_info:
            print()
            print("Source and sink shapes:")
            print([self.labels[s] for s in source_shapes])
            print([self.labels[s] for s in sink_shapes])

        # Get all finite paths from start to end shapes
        finite_paths = []
        for s1 in source_shapes:
             for s2 in sink_shapes:
                 if s1 != s2:
                     finite_paths = [*finite_paths, *self._get_possible_paths(s1, s2, [])]

        # Print all finite paths
        if print_info:
            print()
            print("All finite paths:")
            for p in finite_paths:
                print([self.labels[s] for s in p])


        # Note that the computation below is still heuristic because of loops
        # Test for co-occurrence and exclusiveness
        for s1 in self.tasks:
            for s2 in self.tasks:
                # If s1 and 22 co-occur in ALL finite paths, we consider them as co-occurring
                cooccurrence = True
                # If s1 and s2 do NOT co-occur in ANY finite path, we consider them exclusive
                exclusive = True
                for p in finite_paths:
                    if not (s1 in p) or not (s2 in p):
                        cooccurrence = False
                    if s1 in p and s2 in p:
                        exclusive = False
                label1 = self.labels[s1].lower()
                label2 = self.labels[s2].lower()
                if (cooccurrence or exclusive) and not self.heuristic_parser:
                    s1_parse = self.parser.parse_label(label1)
                    s2_parse = self.parser.parse_label(label2)
                    # check BO requirements
                    if not self.equal_bos or s1_parse.bos == s2_parse.bos:
                        if len(s1_parse.actions) > 0 and len(s2_parse.actions) > 0:
                            if s1_parse.actions[0] != s2_parse.actions[0]:
                                if cooccurrence:
                                    knowledge_base.add_observation(s1_parse.actions[0], s2_parse.actions[0],Observation.CO_OCC)
                                    extracted_info = True
                                    if print_info:
                                        print(f"CO-OCC:{self.labels[s1]} - {self.labels[s2]}, verbs: {s1_parse.actions[0]} - {s2_parse.actions[0]}")
                                if exclusive:
                                    knowledge_base.add_observation(s1_parse.actions[0], s2_parse.actions[0],Observation.XOR)
                                    extracted_info = True
                                    if print_info:
                                        print(f"XOR: {self.labels[s1]} - {self.labels[s2]}, verbs: {s1_parse.actions[0]} - {s2_parse.actions[0]}")
                if (cooccurrence or exclusive) and self.heuristic_parser:
                    if not self.equal_bos or lp.differ_by_one_word(label1, label2):
                        (verb1, verb2) = lp.get_differences(label1, label2)
                        if cooccurrence:
                            knowledge_base.add_observation(verb1, verb2, Observation.CO_OCC)
                            extracted_info = True
                            if print_info:
                                print(f"CO-OCC:{self.labels[s1]} - {self.labels[s2]}, verbs: {verb1} - {verb2}")
                        if exclusive:
                            knowledge_base.add_observation(verb1, verb2, Observation.XOR)
                            extracted_info = True
                            if print_info:
                                print(f"XOR: {self.labels[s1]} - {self.labels[s2]}, verbs: {verb1} - {verb2}")

        # Search for lifecycle relations
        for s1 in self.tasks:
            for s2 in self.tasks:
                if s2 in self._get_transitive_postset(s1, set()) and not s1 in self._get_transitive_postset(s2,set()):
                    label1 = self.labels[s1].lower()
                    label2 = self.labels[s2].lower()
                    if not self.heuristic_parser:
                        s1_parse = self.parser.parse_label(label1)
                        s2_parse = self.parser.parse_label(label2)
                        # check BO requirements
                        if not self.equal_bos or s1_parse.bos == s2_parse.bos:
                            # There need to be different actions ...
                            if len(s1_parse.actions) > 0 and len(s2_parse.actions) > 0:
                                if s1_parse.actions[0] != s2_parse.actions[0]:
                                    # and the same business object
                                    # if t1_parse.bos == t2_parse.bos:
                                    knowledge_base.add_observation(s1_parse.actions[0], s2_parse.actions[0],Observation.ORDER)
                                    extracted_info = True
                                    if print_info:
                                        print(f"ORDER: {self.labels[s1]} - {self.labels[s2]}, verbs: {s1_parse.actions[0]} - {s2_parse.actions[0]}")
                    if self.heuristic_parser and lp.differ_by_one_word(label1, label2):
                        (verb1, verb2) = lp.get_differences(label1, label2)
                        knowledge_base.add_observation(verb1, verb2, Observation.ORDER)
                        extracted_info = True
                        if print_info:
                            print(f"ORDER: {self.labels[s1]} - {self.labels[s2]}, verbs: {verb1} - {verb2}")
        self.parsed_models += 1
        if extracted_info == True:
            self.parsed_models_used += 1

    def _get_possible_paths(self,s1,s2, path=[]):
        # Returns all possible paths from s1 to s2 as a list of lists
        postset = self._get_postset(s1)
        # if target (s2) is in postset, add current and target shape and return
        if s2 in postset:
            path.append(s1)
            path.append(s2)
            return [path]
        # if no shapes in postset, return empty list
        if len(postset) == 0:
            return []
        # Several shapes in postset ...
        else:
            path.append(s1)

            # Determine shapes to be visited (make sure that we don't visit the same shape again and get stuck
            to_be_visited = postset.difference(set(path))
            # If no shape is left, return empty list
            if len(to_be_visited) == 0:
                return []
            else:
                paths = []
                # Recursively traverse
                for s in to_be_visited:
                    recursive_paths = self._get_possible_paths(s, s2, path.copy())
                    if len(recursive_paths) > 0:
                        if isinstance(recursive_paths[0], list):
                            for p in recursive_paths:
                                paths.append(p)
                        else:
                            paths.append(recursive_paths)
                return paths


    def _get_transitive_postset(self,shape,visited_shapes):
        # Returns all shapes in the postset of a shape. Note that these might
        # include all shapes if the model contains loops.

        # Obtain all shapes  in the postset of considered shape
        transitive_post_set = self._get_postset(shape)

        # Determine which transitions still need to be visited
        to_be_visited = transitive_post_set.difference(visited_shapes)

        # Update visited shapes
        visited_shapes.update(to_be_visited)
        if len(to_be_visited) == 0:
            return set()
        else:
            # Recursively build transitive postset
            for s in to_be_visited:
                recursive_result = self._get_transitive_postset(s, visited_shapes)
                transitive_post_set.update(recursive_result)
                visited_shapes.update(recursive_result)
            return transitive_post_set


    def _get_postset(self,shape):
        # Note: The direct postset of a shape typically only contains the arc, not another element.
        # Exceptions are attached events. Both is handled properly.
        postset = set()
        direct_postset = set(self.follows[shape])
        for s in direct_postset:
            # Ignore message flows
            if self.labels[s].startswith("MessageFlow"):
                continue
            if not self.labels[s].startswith("SequenceFlow"):
                postset.add(s)
            else:
                postset.update(self.follows[s])
        return postset


    def _get_preset(self,shape):
        # Note: The direct preset of a shape typically only contains the arc, not another element.
        # Exceptions are attached events. Both is handled properly.
        preset = set()
        for s1 in self.follows.keys():
            if s1!=shape and shape in self.follows[s1]:
                if not self.labels[s1].startswith("MessageFlow"):
                    if not self.labels[s1].startswith("SequenceFlow"):
                        preset.add(s1)
                    else:
                        for s2 in self.follows.keys():
                            if s2!=s1 and s1 in self.follows[s2]:
                                preset.add(s2)
        return preset


    def _process_shapes(self, shapes):

        follows = {}
        labels = {}
        tasks = set()

        # Analyze shape list and store all shapes and activities
        # PLEASE NOTE: the code below ignores BPMN sub processes
        for shape in shapes:

            # Save all shapes to dict
            #print(shape['stencil']['id'], shape)

            # If current shape is a pool or a lane, we have to go a level deeper
            if  shape['stencil']['id'] == 'Pool' or shape['stencil']['id'] == 'Lane':
                result = self._process_shapes(shape['childShapes'])
                follows.update(result[0])
                labels.update(result[1])
                tasks.update(result[2])

            shapeID = shape['resourceId']
            outgoingShapes = [s['resourceId'] for s in shape['outgoing']]
            if shapeID not in follows:
                follows[shapeID] = outgoingShapes

            # Save all tasks and respective labels separately
            if shape['stencil']['id'] == 'Task':
                if not shape['properties']['name'] == "":
                    tasks.add(shape['resourceId'])
                    labels[shape['resourceId']] = shape['properties']['name']
                else:
                    labels[shape['resourceId']] = 'Task'
            else:
                if 'name' in shape['properties'] and not shape['properties']['name'] == "":
                    labels[shape['resourceId']] = shape['stencil']['id'] + " (" + shape['properties']['name'] + ")";
                else:
                    labels[shape['resourceId']] = shape['stencil']['id']
        return follows, labels, tasks

    def _loadJSON(self, path_to_json):
        json_data = None
        with open(path_to_json, 'r') as f:
            data = f.read()
            json_data = json.loads(data)

        follows, labels, tasks = self._process_shapes(json_data['childShapes'])
        return follows, labels, tasks


