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
data_dir =  root_folder / "data/epa_pfas_analytic_tool/"
output_dir = root_folder / "federal/pfas-industries/epa-pfas-analytic-tools/"

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
    logging.info("Start getting industries from EPA PFAS Analytic Tools")

    ## read data file
    data_file = data_dir / "PFASHandlingIndustrySectors-Apr2023-Pub.xlsx"
    df = pd.read_excel(data_file, sheet_name="Industries of Interest", dtype=str)
    print(df.info())


    ## create output graph
    g = Graph()
    for p in prefixes:
        g.bind(p, prefixes[p])

    ## process each row
    for index, row in df.iterrows():

        naics_code = str(row['2017 NAICS Code'])
    #    naics_label = row['NAICS Title']

        naics_uri = prefixes['naics'][f"NAICS-{naics_code}"]

        if row['OLEM list'] == 'Y':
            g.add((prefixes['fio-pfas']['OLEM-PFAS-IndustryCollection'], prefixes['fio']['hasMember'], naics_uri))

        if row['OAR list'] == 'Y':
            g.add((prefixes['fio-pfas']['OAR-PFAS-IndustryCollection'], prefixes['fio']['hasMember'], naics_uri))

        if row['OECA Research'] == 'Y':
            g.add((prefixes['fio-pfas']['OECA-PFAS-IndustryCollection'], prefixes['fio']['hasMember'], naics_uri))

        if row['MN List'] == 'Y':
            g.add((prefixes['fio-pfas']['MN-PFAS-IndustryCollection'], prefixes['fio']['hasMember'], naics_uri))

        if row['Salvatore et al. (2022)'] == 'Y':
            g.add((prefixes['fio-pfas']['Salvatore-PFAS-IndustryCollection'], prefixes['fio']['hasMember'], naics_uri))

    g.add((prefixes['fio-pfas']['OLEM-PFAS-IndustryCollection'], RDFS.subClassOf, prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern']))
    g.add((prefixes['fio-pfas']['OLEM-PFAS-IndustryCollection'], RDFS.label, Literal("Industries identified by EPA Office of Land and Emergency Management (OLEM) as potential PFAS users")))
    g.add((prefixes['fio-pfas']['OAR-PFAS-IndustryCollection'], RDFS.subClassOf, prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern']))
    g.add((prefixes['fio-pfas']['OAR-PFAS-IndustryCollection'], RDFS.label, Literal("Industries identified by EPA Office of Air and Radiation (OAR) as potential PFAS users")))
    g.add((prefixes['fio-pfas']['OECA-PFAS-IndustryCollection'], RDFS.subClassOf, prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern']))
    g.add((prefixes['fio-pfas']['OECA-PFAS-IndustryCollection'], RDFS.label, Literal("Industries identified by EPA Office of Enforcement and Compliance Assurance (OECA) research as potential PFAS users")))
    g.add((prefixes['fio-pfas']['MN-PFAS-IndustryCollection'], RDFS.subClassOf, prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern']))
    g.add((prefixes['fio-pfas']['MN-PFAS-IndustryCollection'], RDFS.label, Literal("Industries identified by Minnesota Pollution Control Agency as potential PFAS users")))
    g.add((prefixes['fio-pfas']['Salvatore-PFAS-IndustryCollection'], RDFS.subClassOf, prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern']))
    g.add((prefixes['fio-pfas']['Salvatore-PFAS-IndustryCollection'], RDFS.label, Literal("Industries identified by Salvatore et al. (2022) as potential PFAS users")))
    g.add((prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern'], RDF.type, OWL.Class))
    g.add((prefixes['fio-pfas']['IndustryCollectionByPFASContaminationConcern'], RDFS.subClassOf, prefixes['fio']['IndustryCollection']))

    ## serialize output graph
    output_file = output_dir / "pfashandlingindustrysectors-epa.ttl"
    g.serialize(destination=str(output_file), format='turtle')
    logging.info(f"Finished writing output to {output_file}")


if __name__ == "__main__":
        main()