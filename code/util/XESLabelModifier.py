from lxml import etree as et


label_map = {
"W_Wijzigen contractgegevens": "change contract deteails",
"W_Afhandelen leads": "process leads",
"A_CANCELLED": "cancelled",
"A_APPROVED": "approved",
"A_SUBMITTED":  "submitted",
"A_REGISTERED": "registered",
"A_DECLINED": "declined",
"A_ACTIVATED": "ativated",
"O_SENT": "sent",
"W_Nabellen incomplete dossiers": "call after incomplete dossiers",
"O_CANCELLED": "cancelled",
"A_PARTLYSUBMITTED": "partly submitted",
"A_ACCEPTED": "accepted",
"A_FINALIZED": "finalized",
"O_CREATED": "created",
"O_SENT_BACK": "send back",
"O_SELECTED": "selected",
"W_Beoordelen fraude": "assess fraud",
"O_DECLINED": "declined",
"W_Completeren aanvraag": "complete request",
"W_Nabellen offertes": "call after offers",
"W_Valideren aanvraag": "verify request",
"A_PREACCEPTED": "preaccepted",
"O_ACCEPTED": "accepted",
}

def main():

    file = '../input/logs/BPIC15_1.xes'
    event_key = "activityNameEN"
    tree = et.parse(file)
    data = tree.getroot()
    unique_labels = set()

    # find all traces
    traces = data.findall('{http://www.xes-standard.org/}trace')
    for t in traces:

        # for each event
        for event in t.iter('{http://www.xes-standard.org/}event'):
            for a in event:
                if a.attrib['key'] == event_key:
                    event_label = a.attrib['value']
                    unique_labels.add(event_label)
                    new_attrib = et. Element("string")
                    new_attrib.set("key", "concept:new_name")
                    new_attrib.set("value", get_new_event_name(event_label))
                    event.append(new_attrib)
    tree.write("../input/logs/BPIC15_1_modified.xes", pretty_print=True, xml_declaration=True, encoding="utf-8")

def get_new_event_name(event_label):
    orig = event_label
    if event_label in label_map:
        event_label = label_map[event_label]
    event_label = event_label.lower()
    event_label = event_label.replace("generating", "generate")
    event_label = event_label.replace("creating", "create")
    event_label = event_label.replace("phase", "")
    event_label = event_label.lstrip()
    if orig != event_label:
        print("changed", orig, "to", event_label)
    return event_label

if __name__ == '__main__':
    main()
