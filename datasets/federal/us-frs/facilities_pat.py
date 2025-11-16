import os
from typing import Dict
from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
import pandas as pd
import encodings
import logging
import csv
from datetime import datetime
import sys
import math
import numpy as np
from datetime import date
from pyutil import *
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent
#print(code_dir)
sys.path.insert(0, str(code_dir))
#from variable import NAME_SPACE, _PREFIX

## declare variables
logname = "log"
sa = input("state abbreviation?")
state = f' {sa}'

## data path
root_folder =Path(__file__).resolve().parent.parent.parent
data_dir = root_folder / "data/epa_pfas_analytic_tool/"
metadata_dir = None
output_dir = root_folder / "federal/us-frs/triples/"


epa_frs = Namespace(f"http://w3id.org/fio/v1/epa-frs#")
epa_frs_data = Namespace(f"http://w3id.org/fio/v1/epa-frs-data#")
fio = Namespace(f"http://w3id.org/fio/v1/fio#")
naics = Namespace(f"http://w3id.org/fio/v1/naics#")
sic = Namespace(f"http://w3id.org/fio/v1/sic#")

## initiate log file
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

logging.info(f"Running triplification for PAT facilities {state}")

def main():
    '''main function initializes all other functions'''
    df = load_data()

    if sa:
        #filter to just one state
        df = df[df['State'] == state]
        kg = triplify(df)

        kg_turtle_file = output_dir / f"epa-frs-data-{state.strip()}-pat.ttl".format(output_dir)
        kg.serialize(kg_turtle_file, format='turtle')
        logger = logging.getLogger(f'Finished triplifying pfas analytics tool facilities - {state}.')
        
    else:
        #loop through all states
        for state1 in df['State'].unique():
            df_state = df[df['State']==state1]
            kg = triplify(df_state)

            kg_turtle_file = output_dir / f"epa-frs-data-{state.strip()}-pat.ttl".format(output_dir)
            kg.serialize(kg_turtle_file, format='turtle')
            logger = logging.getLogger(f'Finished triplifying pfas analytics tool facilities - {state}.')
            print(f'Finished triplifying pfas analytics tool facilities - {state1}.')

def load_data():
    #df = pd.read_csv(data_dir / f"industrysectors_{state}.csv")
    #df = pd.read_excel(data_dir/ 'industrysectors_275aeff7-cbf1-46c2-92a9-67886bcbc0ee.xlsx') #older data
    df = pd.read_excel(data_dir/ 'industrysectors_dee6b0cb-ab9e-4952-bf70-977004a9e878.xlsx')
    #df = pd.read_json(data_dir / '')
    #replace - with nan
    df.replace(to_replace='-', value=pd.NA, inplace=True)
    print(df.info(verbose=True))
    logger = logging.getLogger('Data loaded to dataframe.')
    return df


def Initial_KG() -> object:
    #prefixes: Dict[str, str] = _PREFIX
    kg = Graph()
    #for prefix in prefixes:
    #    kg.bind(prefix, prefixes[prefix])
    kg.bind('fio', fio)
    kg.bind('epa-frs', epa_frs)
    kg.bind('epa-frs-data', epa_frs_data)
    #kg.bind('naics', naics)
    #kg.bind('sic', sic)
    return kg

def clean_attributes(df):
    #print(df.info())
    pass

    return df

def get_attributes(row):

    if pd.notnull(row['ECHO Facility Report']):
        echo_facility = row['ECHO Facility Report']
        echo_url, fac_id = echo_facility.rsplit('=')
    else:
        #airports have no FRS id
        return False
        #TO DO need a better identifier for non FRS facilities
        #fac_id = row['Facility']
        #print('error: ', row['Facility'])

    facility = {
        'facility_name': row['Facility'],
        'status': row['Status'],
        'facility_id': ''.join(fac_id.split()),
        'latitude': row['Latitude'],
        'longitude': row['Longitude'],
    }

    return facility

def get_iris(facility):
    #remove airports with no frs_id
    if facility != False:
        facility_iri = epa_frs_data['d.'+'FRS-Facility.'+facility['facility_id']]
    else:
        return False
    return facility_iri


def triplify(df):
    kg = Initial_KG()

    df = clean_attributes(df)
    for idx, row in df.iterrows():
        facility = get_attributes(row)
        facility_iri = get_iris(facility)
        if facility != False:
            #create facility
            kg.add((facility_iri, RDF.type, epa_frs["FRS-Facility"]))
            kg.add((facility_iri, RDF.type, epa_frs["EPA-PFAS-Facility"]))

    return kg

## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True


if __name__ == "__main__":
    main()