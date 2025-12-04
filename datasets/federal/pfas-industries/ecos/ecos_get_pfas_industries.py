import os
from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS, DCTERMS
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
import urllib3
from urllib import parse
import json
import pandas as pd
import encodings
import urllib
import logging
import math
from pathlib import Path
import numpy as np
from pyutil import *
import sys
import re
import pprint

logname = "log"

## data path
root_folder = Path(__file__).resolve().parent.parent.parent.parent
data_dir =  root_folder / "data/ecos/"
output_dir = root_folder / "federal/pfas-industries/ecos/"

##namespaces
prefixes = {}
prefixes['naics'] = Namespace("http://w3id.org/fio/v1/naics#")
prefixes['fio-pfas'] = Namespace(f'http://w3id.org/sawgraph/v1/pfas-industries#')
prefixes['fio'] = Namespace("http://w3id.org/fio/v1/fio#")

## initiate log file
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

def main():
    logging.info("Start getting industries from ecos")

    ## read data file
    data_file = data_dir / "PFAS Use in Industry Table.csv"
    df = pd.read_csv(data_file, dtype=str)
    print(df.info())


    ## create output graph
    g = Graph()
    for p in prefixes:
        g.bind(p, prefixes[p])

    ## process each row
    for index, row in df.iterrows():
        naics, title = row['2022 NAICS Code, Title'].split(',',1)
        g.add( (prefixes['fio-pfas']['ECOS-PFAS-IndustryCollection'], prefixes['fio']['hasMember'], prefixes['naics'][f"NAICS-{naics}"]) )

    g.add( (prefixes['fio-pfas']['ECOS-PFAS-IndustryCollection'], RDFS.label, Literal("Industries identified by ECOS as potential PFAS users")) )
    g.add(( prefixes['fio-pfas']['ECOS-PFAS-IndustryCollection'], RDFS.subClassOf, prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern'] ))

     ## serialize output graph
    output_file = output_dir / "pfashandlingindustrysectors_ecos.ttl"
    g.serialize(destination=str(output_file), format='turtle')
    logging.info(f"Finished writing output to {output_file}")


if __name__ == "__main__":
        main()