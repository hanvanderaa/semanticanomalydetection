import os
import pickle
import csv
import sys

from knowledgebase_population import verboceanpopulator
from knowledgebase_population.bpmnpopulator import BPMNPopulator
from knowledgebase.knowledgebase import KnowledgeBase
from knowledgebase_population.petrinetpopulator import PetriNetKBPopulator
from pm4py.objects.log.importer.xes import importer as xes_importer
from anomalydetection.anomalydetector import AnomalyDetector


# KNOWLEDGE_BASE_SETTINGS
# load serialized KB rather than populating (RECOMMENDED = True, file: icpmKB.ser)
LOAD_SERIALIZED_KB = True
KB_SERIAL_FILE = "input/serializedkbs/icpmKB.ser"
# population settings (RECOMMENDED = True, True)
EQUAL_BOS_IN_POPULATION = True
FILTER_KB = True
# set options for population (does not work when loading serialized)
# (recommended = True, True, True)
use_SAP_models = True
use_BPMAI_models = False
use_verbocean = False
# only repopulate KB instead of detecting anomalies
ONLY_POPULATE_KB = False

# use less precise (heuristic) parsing (recommended = False)
HEURISTIC_PARSER = False



# Stores which tag is used in respective log to capture the event name
logs = {
    "BPI_2012.xes": "concept:name",
    "BPI_2014.xes": "concept:name",
    "BPIC15_1.xes.xml": "activityNameEN",
    "BPIC15_2.xes.xml": "activityNameEN",
    "BPIC15_3.xes.xml": "activityNameEN",
    "BPIC15_4.xes.xml": "activityNameEN",
    "BPIC15_5.xes.xml": "activityNameEN",
    "BPI_2018.xes": "concept:name",
    "admission/admission iis erlangen.xes": "concept:name"
}

def main():
    kb = obtain_knowledge_base()
    if ONLY_POPULATE_KB:
        sys.exit()

    # Create new output file
    with open("output/" + get_output_file_name(), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        header = ["log", "anomaly type", "event1", "event2", "verb1", "verb2", "record_conf", "anomaly_count"]
        writer.writerow(header)

    for log_name in logs.keys():
        log_file = f"input/logs/{log_name}"
        if os.path.exists(log_file):
            print("\nloading event log", log_name)
            log = xes_importer.apply(log_file)
            print("detecting anomalies")
            detector = AnomalyDetector(kb, log, log_name, logs[log_name], True, HEURISTIC_PARSER)
            anomaly_counter = detector.detect_anomalies()
            #   write results to file (and stdout)
            with open("output/" + get_output_file_name(), 'a', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                for anomaly in anomaly_counter:
                    row = [log_name]
                    row.extend(anomaly.to_array())
                    row.append(anomaly_counter[anomaly])
                    writer.writerow(row)
                    print(anomaly, "count:", anomaly_counter[anomaly])
    print('done')


def obtain_knowledge_base():
    if not LOAD_SERIALIZED_KB:
        kb = _populate_knowledge_base()
        pickle.dump(kb, open(KB_SERIAL_FILE, "wb"))
        if FILTER_KB:
            kb.filter_out_conflicting_records()
        return kb
    else:
        kb = pickle.load(open(KB_SERIAL_FILE, "rb"))
        print("loaded knowledge base from", KB_SERIAL_FILE)
        if FILTER_KB:
            kb.filter_out_conflicting_records()
        return kb


def _populate_knowledge_base():
    kb = KnowledgeBase()

    if use_BPMAI_models:
        # from ai collection
        ai_dir = "input/knowledgebase/bpmai/models"
        populator = BPMNPopulator(equal_bos=EQUAL_BOS_IN_POPULATION, heuristic_parser=HEURISTIC_PARSER)
        populator.populate(kb, ai_dir)

    if use_SAP_models:
        # from SAP collection
        populator = PetriNetKBPopulator(equal_bos=EQUAL_BOS_IN_POPULATION, heuristic_parser=HEURISTIC_PARSER)
        sap_dir = "input/knowledgebase/sapmodels/"
        files = os.listdir(sap_dir)
        files = [f for f in files if f.endswith("pnml")]
        for i, file in enumerate(files):
            print(f"({i}) --------------")
            print(sap_dir + file)
            populator.populate(kb, os.path.abspath(sap_dir) + "/" + file)

    if use_verbocean:
        # from verbocean records
        verboceanpopulator.populate(kb, "input/knowledgebase/verbocean.txt", count_per_record= 1000)
    return kb

def get_output_file_name():
    output_string = "Violations_"
    if EQUAL_BOS_IN_POPULATION:
        output_string = output_string + "EqBosInPop_"
    else:
        output_string = output_string + "NoEqBosInPop_"
    output_string = output_string + "EqBosInCheck_"
    if HEURISTIC_PARSER:
        output_string = output_string + "Heuristic.csv"
    else:
        output_string = output_string + "NoHeuristic.csv"
    return output_string


if __name__ == '__main__':
    main()
