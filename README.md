# semanticanomalydetection

This repository presents the implementation employed in the proof of concept of the paper "*Detecting Semantic Execution Anomalies in Event Logs*" by Han van der Aa and Henrik Leopold, currently under submission to the BPM Conference (2020).

## Libraries
Our work employs the [PM4py](https://pm4py.fit.fraunhofer.de/)  and [NLTK](https://www.nltk.org/) libraries, which can both be installed via, for instance, *pip install*.

## Employed data Collections

### Knowledge base population
As described in our paper, our instantiation of the knowledge base is populated based on five resources:
1. Manually extracted records from the [SAP Library](help.sap.com). The records are included in code/input/knowledgebase/lifecycles/sap_lib_lifecycles.csv and automatically loaded in _main.py_
2. Manually extracted records from the Work item lifecycle [1]. The records are included in code/input/knowledgebase/lifecycles/work_item_lifecycles.csv and automatically loaded in _main.py_
3. Telecom process model collection of proprietary process models.
4. SAP Reference collection of proprietary, though widely available process models.
5. Antonyms from WordNet - As part of the NLTK library and automatically incorporated in the implementation.

Although we are not a liberty to provide the process model collections corresponding to items 2 and 3, the knowledge records extracted from these are incorporated in the knowledge base instantiation used to conduct the experiments, stored as code/input/knowledgebase/serializedkb.ser

### Event logs

**Real-world logs** We used the following publicly available real-world logs: [BPI Challenge 2012](https://data.4tu.nl/repository/uuid:3926db30-f712-4394-aebc-75976070e91f), [BPI Challenge 2014](https://data.4tu.nl/repository/uuid:c3e5d162-0cfd-4bb0-bd82-af5268819c35), [BPI Challenge 2015](https://doi.org/10.4121/uuid:31a308ef-https://data.4tu.nl/repository/uuid:31a308ef-c844-48da-948c-305d167a0ec1), and [BPI Challenge 2018](https://doi:10.4121/uuid:3301445f-95e8-4ff0-98a4-901f1f204972). 
Make sure to place the logs you want to run in the code/input/logs/ folder and ensure that the *logs* dictionary in _main.py_ contains the appropriate reference to the log file and event class identifier.

**Synthetic event logs** We used synthetic event logs generated based on the [University Adminssion process models](http://www.henrikleopold.com/wp-content/uploads/2016/12/AdmissionDataSet_PNML_2013.zip). The employed log files are included code/logs/admission/

## Running the tool
Anomaly detection can be started by simply executing _main.py_. We recommend to use the default settings as provided.
In the reported experiments, we varied the boolean  _STRICT_MATCHING_PREDICATE_ boolean to obtain results for the two different configurations.

The detected anomalies are printed as console output and saved in a .csv file in code/output/. 




## Reference
[1] Russell, N., van der Aalst, W.M., Ter Hofstede, A.H., Edmond, D.: Workflow resource patterns: Identification, representation and tool support. In: CAiSE. pp. 216–232. Springer (2005)
