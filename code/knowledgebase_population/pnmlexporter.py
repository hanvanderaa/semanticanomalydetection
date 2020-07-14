import pm4py
from pm4py.objects.petri.petrinet import PetriNet, Marking
from lxml import etree
import uuid

def export_pnml(petrinet: PetriNet, marking: Marking, output_filename):
    final_marking = Marking()
    root = etree.Element("pnml")
    net = etree.SubElement(root, "net")
    net.set("id", "net1")
    net.set("type", "http://www.pnml.org/version-2009/grammar/pnmlcoremodel")
    page = etree.SubElement(net, "page")
    page.set("id", "n0")
    places_map = {}
    for place in petrinet.places:
        places_map[place] = place.name
        pl = etree.SubElement(page, "place")
        pl.set("id", str(place.name))
        pl_name = etree.SubElement(pl, "name")
        pl_name_text = etree.SubElement(pl_name, "text")
        pl_name_text.text = str(place.name)
        if place in marking:
            pl_initial_marking = etree.SubElement(pl, "initialMarking")
            pl_initial_marking_text = etree.SubElement(pl_initial_marking, "text")
            pl_initial_marking_text.text = str(marking[place])
    transitions_map = {}
    for transition in petrinet.transitions:
        transitions_map[transition] = transition.name
        trans = etree.SubElement(page, "transition")
        trans.set("id", str(transition.name))
        trans_name = etree.SubElement(trans, "name")
        trans_text = etree.SubElement(trans_name, "text")
        if transition.label is not None:
            trans_text.text = transition.label
        else:
            trans_text.text = transition.name
            tool_specific = etree.SubElement(trans, "toolspecific")
            tool_specific.set("tool", "ProM")
            tool_specific.set("version", "6.4")
            tool_specific.set("activity", "$invisible$")
            tool_specific.set("localNodeID", str(uuid.uuid4()))
    for arc in petrinet.arcs:
        arc_el = etree.SubElement(page, "arc")
        arc_el.set("id", str(hash(arc)))
        if type(arc.source) is pm4py.objects.petri.petrinet.PetriNet.Place:
            arc_el.set("source", str(places_map[arc.source]))
            arc_el.set("target", str(transitions_map[arc.target]))
        else:
            arc_el.set("source", str(transitions_map[arc.source]))
            arc_el.set("target", str(places_map[arc.target]))

    if len(final_marking) > 0:
        finalmarkings = etree.SubElement(net, "finalmarkings")
        marking = etree.SubElement(finalmarkings, "marking")

        for place in final_marking:
            placem = etree.SubElement(marking, "place")
            placem.set("idref", place.name)
            placem_text = etree.SubElement(placem, "text")
            placem_text.text = str(final_marking[place])
    tree = etree.ElementTree(root)
    tree.write(output_filename, pretty_print=True, xml_declaration=True, encoding="utf-8")