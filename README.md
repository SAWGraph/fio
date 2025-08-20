# FIO

The Facilities and Industries Ontology provides a representation of facilities and their industry classification(s). It is extended by the FRS ontology that incorporates facilities in the US from EPA's facility registry service (<https://www.epa.gov/frs>) , and the NAICS and SIC ontologies that populate these two industry classification schemes.

## Schema Diagram

![FIO schema diagram](./ontology/FIO.png)

[FIO ontology schema diagram](https://lucid.app/lucidchart/0b649dc4-e466-4d29-ae34-5c0f113f5a46/edit?viewport_loc=-1453%2C-27%2C2951%2C1455%2Cq4u-GszAWYkJ&invitationId=inv_0e3483a0-96fc-4faf-8c17-1a5bf73fd23b)

 ## FIO Ontology
 The ontology is implemented at [/ontology/FIO.ttl](/ontology/FIO.ttl) 
 
 and the documentation is hosted at: [https://theskailab.github.io/fio/index-en.html](https://theskailab.github.io/fio/index-en.html) also redirected from [http://w3id.org/fio/](http://w3id.org/fio/)

 ## Datasets
 The ontology is instantiated by the datasets for NAICS and EPA FRS in [/datasets](/datasets)
 
 The dataset folders contains:
* Dataset ontology that serves that aligns dataset terms to FIO
* instances or a sample of instances (for epa-frs) 
* python scripts used to triplify the dataset

## Evaluation

The [/sparql](/sparql) folder contains example sparql queries that were used to evaluate the ontology using instances from the datasets. 
These queries can also be run on the existing instances of FIO graph in the SAWGraph project [here](https://gdb.acg.maine.edu:7201) and [here](https://frink.apps.renci.org/) 
