from xml.dom import minidom
from pm4py.objects.petri.petrinet import PetriNet, Marking
from pm4py.visualization.petrinet import factory as pn_vis_factory
from pm4py.objects.petri import utils
from knowledge_base import PNMLExporter
import os

def get_next_id(net):
    return max([int(p.name) for p in net.places] + [int(t.name) for t in net.transitions]) + 1

# Parses EPML file and derives a respective Petri net
def parse_EPML(file, output_path = "../output/", pnml = True, jpg = True):
    file_name = file[file.rfind("/") + 1:]
    xmldoc = minidom.parse(file)
    epcs = xmldoc.getElementsByTagName('epc')

    # For each EPC...
    for epc in epcs:

        # Create Petri Net
        net = PetriNet(f"Petri Net ({epc.attributes['epcId']})")

        # Sets to keep track of element IDs
        transition_ids = {}
        place_ids = {}
        xor_ids = {}
        and_ids = {}

        # Get all functions
        function_ids = epc.getElementsByTagName('function')
        for function in function_ids:
            function_id = function.attributes['id'].value
            function_name = function.getElementsByTagName('name')[0].firstChild.nodeValue

            # Petri net transformation
            t = PetriNet.Transition(function_id, function_name)
            transition_ids[function_id] = t
            net.transitions.add(t)

        # Get all events
        event_ids = epc.getElementsByTagName('event')
        for event in event_ids:
            event_id = event.attributes['id'].value
            try:
                event_name = event.getElementsByTagName('name')[0].firstChild.nodeValue
            except:
                event_name = ""

            # Petri net transformation
            p = PetriNet.Place(event_id)
            place_ids[event_id]=p
            net.places.add(p)

        # Get all connectors
        xorConnectors = epc.getElementsByTagName('xor')
        for xorConnector in xorConnectors:
            xor_id = xorConnector.attributes['id'].value

            # Petri net transformation
            p = PetriNet.Place(xor_id)
            xor_ids[xor_id] = p
            net.places.add(p)

        orConnectors = epc.getElementsByTagName('or')
        for orConnector in orConnectors:
            or_id = orConnector.attributes['id'].value

            # Petri net transformation
            p = PetriNet.Place(or_id)
            xor_ids[xor_id] = p
            net.places.add(p)

        andConnectors = epc.getElementsByTagName('and')
        for andConnector in andConnectors:
            and_id = andConnector.attributes['id'].value

            # Petri net transformation
            t = PetriNet.Transition(and_id, f"and-{and_id}")
            and_ids[and_id] = t
            net.transitions.add(t)

        # Get all arcs
        arcs = epc.getElementsByTagName('arc')
        sources = list()
        targets = list()
        for arc in arcs:
            flow = arc.getElementsByTagName('flow')[0]
            source = flow.attributes["source"].value
            target = flow.attributes["target"].value
            sources.append(source)
            targets.append(target)

        # Required for assigning an appropriate id to new elements
        max_id = max([int(i) for i in sources] + [int(i) for i in targets])+1

        # Petri net transformation
        for i in range(len(sources)):

            # transition - place
            if (transition_ids.__contains__(sources[i]) and (place_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(transition_ids.get(sources[i]), place_ids.get(targets[i]), net)

            # place - transition
            if (place_ids.__contains__(sources[i]) and (transition_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(place_ids.get(sources[i]), transition_ids.get(targets[i]), net)

            # transition - transition
            if (transition_ids.__contains__(sources[i]) and (transition_ids.__contains__(targets[i]))):
                p = PetriNet.Place(get_next_id(net))
                net.places.add(p)
                utils.add_arc_from_to(transition_ids.get(sources[i]), p, net)
                utils.add_arc_from_to(p, transition_ids.get(targets[i]), net)

            # transition - transition
            if (place_ids.__contains__(sources[i]) and (place_ids.__contains__(targets[i]))):
                id = get_next_id(net)
                t = PetriNet.Transition(id, f"tau-{id}")
                net.transitions.add(t)
                utils.add_arc_from_to(place_ids.get(sources[i]), t, net)
                utils.add_arc_from_to(t, place_ids.get(targets[i]), net)

            # xor - transition
            if (xor_ids.__contains__(sources[i]) and (transition_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(xor_ids.get(sources[i]), transition_ids.get(targets[i]), net)

            # transition - xor
            if (transition_ids.__contains__(sources[i]) and (xor_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(transition_ids.get(sources[i]), xor_ids.get(targets[i]), net)

            # xor - place
            if (xor_ids.__contains__(sources[i]) and (place_ids.__contains__(targets[i]))):
                id = get_next_id(net)
                t = PetriNet.Transition(id, f"tau-{id}")
                net.transitions.add(t)
                utils.add_arc_from_to(xor_ids.get(sources[i]), t, net)
                utils.add_arc_from_to(t, place_ids.get(targets[i]), net)

            # place - xor
            if (place_ids.__contains__(sources[i]) and (xor_ids.__contains__(targets[i]))):
                id = get_next_id(net)
                t = PetriNet.Transition(id, f"tau-{id}")
                net.transitions.add(t)
                utils.add_arc_from_to(place_ids.get(sources[i]), t, net)
                utils.add_arc_from_to(t, xor_ids.get(targets[i]), net)

            # xor - xor
            if (xor_ids.__contains__(sources[i]) and (xor_ids.__contains__(targets[i]))):
                id = get_next_id(net)
                t = PetriNet.Transition(id, f"tau-{id}")
                net.transitions.add(t)
                utils.add_arc_from_to(xor_ids.get(sources[i]), t, net)
                utils.add_arc_from_to(t, xor_ids.get(targets[i]), net)

            # and - transition
            if (and_ids.__contains__(sources[i]) and (transition_ids.__contains__(targets[i]))):
                p = PetriNet.Place(get_next_id(net))
                net.places.add(p)
                utils.add_arc_from_to(and_ids.get(sources[i]), p, net)
                utils.add_arc_from_to(p, transition_ids.get(targets[i]), net)

            # transition - and
            if (transition_ids.__contains__(sources[i]) and (and_ids.__contains__(targets[i]))):
                p = PetriNet.Place(get_next_id(net))
                net.places.add(p)
                utils.add_arc_from_to(transition_ids.get(sources[i]), p, net)
                utils.add_arc_from_to(p, and_ids.get(targets[i]), net)

            # and - place
            if (and_ids.__contains__(sources[i]) and (place_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(and_ids.get(sources[i]), place_ids.get(targets[i]), net)

            # place - and
            if (place_ids.__contains__(sources[i]) and (and_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(place_ids.get(sources[i]), and_ids.get(targets[i]), net)

            # xor - and
            if (xor_ids.__contains__(sources[i]) and (and_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(xor_ids.get(sources[i]), and_ids.get(targets[i]), net)

            # and - xor
            if (and_ids.__contains__(sources[i]) and (xor_ids.__contains__(targets[i]))):
                utils.add_arc_from_to(and_ids.get(sources[i]), xor_ids.get(targets[i]), net)

    # Clean net from non-connected transitions
    to_be_removed = []
    for t in net.transitions:
        connected = False
        for arc in net.arcs:
            if (arc.source == t) or (arc.target == t):
                connected = True
                break
        if connected == False:
            to_be_removed.append(t)
    for t in to_be_removed:
        net.transitions.remove(t)

    # Create workflow net
    source_places = []
    sink_places = []
    for p in net.places:
        has_input = False
        has_output = False
        for arc in net.arcs:
            if arc.source == p:
                has_output = True
            if arc.target == p:
                has_input = True
        if has_output == False:
           sink_places.append(p)
        if has_input == False:
            source_places.append(p)

    # In case of several source places
    if (len(source_places) > 1):
        source = PetriNet.Place(get_next_id(net))
        net.places.add(source)
        for p in source_places:
            id = get_next_id(net)
            t = PetriNet.Transition(id, f"tau-{id}")
            net.transitions.add(t)
            utils.add_arc_from_to(source, t, net)
            utils.add_arc_from_to(t, p, net)

    # In case of several sink places
    if (len(sink_places) > 1):
        sink = PetriNet.Place(get_next_id(net))
        net.places.add(sink)
        for p in sink_places:
            id = get_next_id(net)
            t = PetriNet.Transition(id, f"tau-{id}")
            net.transitions.add(t)
            utils.add_arc_from_to(p, t, net)
            utils.add_arc_from_to(t, sink, net)

    # Save as jpg
    if jpg == True:
        parameters = {"format": "jpg"}
        gviz = pn_vis_factory.apply(net, None, None, parameters=parameters)
        pn_vis_factory.save(gviz, f"{output_path}{file_name}_net.jpg")

    # Save as pnml
    if pnml == True:
        initial_marking = Marking()
        initial_marking[place_ids.get(0)] = 1
        PNMLExporter.export_pnml(net, initial_marking, f"{output_path}{file_name}_net.pnml")

    return net


def main():
    # I won't put the original models online just to be safe
    dir = "/Users/henrikleopold/Uni/Models/Vodafone (updated)/"
    files = os.listdir(dir)
    max = 10
    counter = 0
    limit = False
    for file in files:
        if counter >= max and limit == True:
           break
        if file.endswith("epml"):
            print(dir + file)
            parse_EPML(dir + file, "../input/output-vodafone/", True, True)
            counter += 1

if __name__ == '__main__':
    main()



