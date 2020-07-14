# semanticanomalydetection

This repository presents the implementation employed in the proof of concept of the paper "*Natural Language-driven Detection of Semantic Execution Anomalies in Event Logs*" by Han van der Aa and Henrik Leopold, currently under submission to the International Conference on Process Mining (2020).

## Libraries
Our work employs the [PM4py](https://pm4py.fit.fraunhofer.de/)  and [NLTK](https://www.nltk.org/) libraries, which can both be installed via, for instance, *pip install*.

## Employed data Collections

### Knowledge base population
As described in our paper, our instantiation of the knowledge base is populated based on three resources:
1. VerbOcean (http://demo.patrickpantel.com/demos/verbocean/). The records are already included in code/input/knowledgebase/verbocean.txt
2. SAP Reference collection of proprietary, though widely available process models.
3. BPM Academic Initiative process model collection from https://zenodo.org/record/3758705.

However, we recommend the usage of the pre-populated knowledge base instantiation used to conduct the experiments, stored as code/input/serializedkbs/icpmKB.ser

### Event logs

**Real-world logs** We used the following publicly available real-world logs: [BPI Challenge 2012](https://data.4tu.nl/repository/uuid:3926db30-f712-4394-aebc-75976070e91f), [BPI Challenge 2014](https://data.4tu.nl/repository/uuid:c3e5d162-0cfd-4bb0-bd82-af5268819c35), [BPI Challenge 2015](https://doi.org/10.4121/uuid:31a308ef-https://data.4tu.nl/repository/uuid:31a308ef-c844-48da-948c-305d167a0ec1), and [BPI Challenge 2018](https://doi:10.4121/uuid:3301445f-95e8-4ff0-98a4-901f1f204972). 
Make sure to place the logs you want to run in the code/input/logs/ folder and ensure that the *logs* dictionary in _main.py_ contains the appropriate reference to the log file and event class identifier.

**Synthetic event logs** We also used a synthetic event log generated based on the [University Adminssion process models](http://www.henrikleopold.com/wp-content/uploads/2016/12/AdmissionDataSet_PNML_2013.zip). The employed log file and accompanying process model is included in code/logs/admission/.

## Running the tool
Anomaly detection can be started by simply executing _main.py_. We recommend to use the default settings as provided (indicated by RECOMMENDED in the upper comments of main.py). The detected anomalies are printed as console output and saved in a .csv file in code/output/. 
