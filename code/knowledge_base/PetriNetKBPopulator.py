import labelparser.labelparser as lp
from pm4py.objects.petri.importer import pnml as pnml_importer
from knowledge_base.KnowledgeBase import KnowledgeBase
from knowledge_base.KnowledgeRecord import Observation
import itertools


class PetriNetKBPopulator:

    def __init__(self, equal_bos = False, heuristic_parser = False):
        self.parser = lp.load_default_parser()
        self.equal_bos = equal_bos
        self.heuristic_parser = heuristic_parser

    def populate(self, knowledge_base: KnowledgeBase, path_to_net):
        # Populates knowledge base using the contents of a petri net in PNML format

        # Load net from file
        net, initial_marking, final_marking = pnml_importer.import_net(path_to_net)

        # Clean strings (especially from SAP)
        for t in net.transitions:
            t.label = t.label.replace('\n', ' ').replace('\r', '')

        # Find source and sink place
        source_place = None
        sink_place = None
        for p in net.places:
            has_preset = False
            has_postset = False
            for arc in net.arcs:
                if arc.target == p:
                    has_preset = True
                if arc.source == p:
                    has_postset = True
            if not (has_preset):
                source_place = p
            if not (has_postset):
                sink_place = p

        # Get starting end end transitions
        start_transitions = self._get_postset_transitions(source_place, net, False)
        end_transitions  = self._get_preset_transitions(sink_place, net, False)
        #print(f"source: {start_transitions}")
        #print(f"sink: {end_transitions}")

        # Get all finite paths from start to end transitions
        finite_paths = []
        for t1 in start_transitions:
            for t2 in end_transitions:
                if t1!=t2:
                    finite_paths = [*finite_paths, *self._get_possible_paths(net, t1, t2, [])]

        # Note that the computation below is still heuristic because loops
        # Test for co-occurrence and exclusiveness
        for t1 in [t for t in net.transitions if not self._is_silent(t)]:
            for t2 in [t for t in net.transitions if not self._is_silent(t)]:
                # If t1 and t2 co-occur in ALL finite paths, we consider them as co-occurring
                cooccurrence = True
                # If t1 and t2 do NOT co-occur in ANY finite path, we consider them exclusive
                exclusive = True
                for p in finite_paths:
                    if not(t1 in p) or not(t2 in p):
                        cooccurrence = False
                    if t1 in p and t2 in p:
                        exclusive = False
                label1 = str(t1.label).lower()
                label2 = str(t2.label).lower()
                if (cooccurrence or exclusive) and not self.heuristic_parser:
                    t1_parse = self.parser.parse_label(label1)
                    t2_parse = self.parser.parse_label(label2)
                    # check BO requirements
                    if not self.equal_bos or t1_parse.bos == t2_parse.bos:
                        if len(t1_parse.actions) > 0 and len(t2_parse.actions) > 0:
                            if t1_parse.actions[0] != t2_parse.actions[0]:
                                if cooccurrence:
                                    knowledge_base.add_observation(t1_parse.actions[0], t2_parse.actions[0], Observation.CO_OCC)
                                    print(f"CO-OCC:{t1} - {t2}, verbs: {t1_parse.actions[0]} - {t2_parse.actions[0]}")
                                if exclusive:
                                    knowledge_base.add_observation(t1_parse.actions[0], t2_parse.actions[0],Observation.XOR)
                                    print(f"XOR: {t1} - {t2}, verbs: {t1_parse.actions[0]} - {t2_parse.actions[0]}")
                if (cooccurrence or exclusive) and self.heuristic_parser:
                    if not self.equal_bos or lp.differ_by_one_word(label1, label2):
                        (verb1, verb2) = lp.get_differences(label1, label2)
                        if cooccurrence:
                            knowledge_base.add_observation(verb1, verb2, Observation.CO_OCC)
                            print(f"CO-OCC:{t1} - {t2}, verbs: {verb1} - {verb2}")
                        if exclusive:
                            knowledge_base.add_observation(verb1, verb2, Observation.XOR)
                            print(f"XOR: {t1} - {t2}, verbs: {verb1} - {verb2}")

        # Search for lifecycle relations
        for t1 in net.transitions:
            for t2 in net.transitions:
                if not (self._is_silent(t1)) and not (self._is_silent(t2)):
                    if t2 in self._get_transitive_postset(t1, net, set()) and not t1 in self._get_transitive_postset(t2, net, set()):
                        label1 = str(t1.label).lower()
                        label2 = str(t2.label).lower()
                        if not self.heuristic_parser:
                            t1_parse = self.parser.parse_label(label1)
                            t2_parse = self.parser.parse_label(label2)
                            # check BO requirements
                            if not self.equal_bos or t1_parse.bos == t2_parse.bos:
                                # There need to be different actions ...
                                if len(t1_parse.actions) > 0 and len(t2_parse.actions) > 0:
                                    if t1_parse.actions[0] != t2_parse.actions[0]:
                                        # and the same business object
                                        # if t1_parse.bos == t2_parse.bos:
                                        knowledge_base.add_observation(t1_parse.actions[0], t2_parse.actions[0], Observation.V1_BEFORE_V2)
                                        print(f"ORDER: {t1} - {t2}, verbs: {t1_parse.actions[0]} - {t2_parse.actions[0]}")
                        if self.heuristic_parser and lp.differ_by_one_word(label1, label2):
                            (verb1, verb2) = lp.get_differences(label1, label2)
                            knowledge_base.add_observation(verb1, verb2, Observation.V1_BEFORE_V2)
                            print(f"ORDER: {t1} - {t2}, verbs: {verb1} - {verb2}")

    def _get_possible_paths(self, net, t1, t2, path=[]):
        # Returns all possible paths from t1 to t2 as a list of lists
        indirect_postset = self._get_indirect_postset_transitions(t1, net, False, False)
        # if target (t2) in postset, add current and target transition and return
        if t2 in indirect_postset:
            path.append(t1)
            path.append(t2)
            return [path]
        # if no transitions in postset, return empty list
        if len(indirect_postset) == 0:
            return []
        # Several transitions in postset ...
        else:
            path.append(t1)
            # Determine transitions to be visited (make sure that we don't visit the same transition again and get stuck
            to_be_visited = indirect_postset.difference(set(path))
            # If no transition is left, return empty list
            if len(to_be_visited) == 0:
                return []
            else:
                paths = []
                # Recursively traverse
                for t in to_be_visited:
                    recursive_paths = self._get_possible_paths(net, t, t2, path.copy())
                    if len(recursive_paths) > 0:
                        if isinstance(recursive_paths[0], list):
                            for p in recursive_paths:
                                paths.append(p)
                        else:
                            paths.append(recursive_paths)
                return paths

    def _parse_transitions(self, transitions):
        # Parses the provided set of transitions and updates respective records with all pairs
        for t1, t2 in itertools.combinations(transitions, 2):
            t1_parse = self.parser.parse_label(str(t1.label).lower())
            t2_parse = self.parser.parse_label(str(t2.label).lower())
        return t1_parse, t2_parse

    def _get_transitive_postset(self, transition, net, visited_transitions):
        # Returns all transitions in the postset of a transition. Note that these might
        # include all transitions if the model contains loops.

        # Obtain all transitions in the indirect post set of considered transition
        transitive_post_set = self._get_indirect_postset_transitions(transition, net, False, False)

        # Determine which transitions still need to be visited
        # to_be_visited = [t for t in transitive_post_set if t not in visited_transitions]
        to_be_visited = transitive_post_set.difference(visited_transitions)

        # Update visited transitions
        visited_transitions.update(to_be_visited)
        if len(to_be_visited) == 0:
            return set()
        else:
            # Recursively build transitive postset
            for t in to_be_visited:
                recursive_result = self._get_transitive_postset(t, net, visited_transitions)
                transitive_post_set.update(recursive_result)
                visited_transitions.update(recursive_result)
            return transitive_post_set

    def _get_postset_transitions(self, place, net, ignore_silent=True):
        # Returns the set of transitions in the postset of the provided place
        # When ignore_silent == True, silent transitions will be removed from the postset
        postset = set()

        # Consider all arcs where the provided place is the source
        for arc in net.arcs:
            if arc.source == place:
                # If (target) transition represents an actual activity, append it to postset
                if ignore_silent and not (self._is_silent(arc.target)) and not (self._is_silent(arc.target)):
                    postset.add(arc.target)
                if not (ignore_silent):
                    postset.add(arc.target)
        return postset

    def _get_preset_transitions(self, place, net, ignore_silent=True):
        # Returns the set of transitions in the preset of the provided place
        # When ignore_silent == True, silent transitions will be removed from the preset
        preset = set()

        # Consider all arcs where the provided place is the source
        for arc in net.arcs:
            if arc.target == place:
                # If (source) transition represents an actual activity, append it to postset
                if ignore_silent and not (self._is_silent(arc.source)) and not (self._is_silent(arc.source)):
                    preset.add(arc.source)
                if not (ignore_silent):
                    preset.add(arc.source)
        return preset

    def _get_indirect_postset_transitions(self, transition, net, ignore_silent=True, ignore_sequences=True):
        # Returns the set of transitions in the (indirect) postset of the postset of places
        # If ignore_silent == True, silent transitions will be removed from the postset
        # If ignore_sequences == True, an empty set will be returned for transitions with a single outgoing place
        direct_postset = set()
        indirect_postset = set()

        # Build direct postset (consisting of places)
        for arc in net.arcs:
            if arc.source == transition:
                direct_postset.add(arc.target)

        # Get indirect postsets of transition by returning postset for each place
        if (ignore_sequences and len(direct_postset) > 1) or not (ignore_sequences):
            for p in direct_postset:
                indirect_postset.update(self._get_postset_transitions(p, net, ignore_silent))
        return indirect_postset

    def _is_silent(self, transition):
        # Checks whether provided transition is a silent transition
        if transition.label.startswith("and"):
            return True
        if transition.label.startswith("tau"):
            return True
        return False
