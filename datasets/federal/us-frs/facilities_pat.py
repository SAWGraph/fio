import os
from typing import Dict
from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
import rdflib
import pandas as pd
import encodings
import logging
from frs_utils import (epa_frs, epa_frs_data, fio, naics, sic, OUTPUT_DIR, setup_logging, get_state, new_graph)
import csv
from datetime import datetime
import sys
import math
import numpy as np
from datetime import date
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent
#print(code_dir)
sys.path.insert(0, str(code_dir))
#from variable import NAME_SPACE, _PREFIX

## declare variables
sa = get_state()
state = f' {sa}'

## data path
root_folder =Path(__file__).resolve().parent.parent.parent
data_dir = root_folder / "data/epa_pfas_analytic_tool/"
metadata_dir = None
output_dir = OUTPUT_DIR


## initiate log file
setup_logging()

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
        for state1 in df['State'].dropna().unique():
            df_state = df[df['State']==state1]
            kg = triplify(df_state)

            kg_turtle_file = output_dir / f"epa-frs-data-{state1.strip()}-pat.ttl"
            kg.serialize(kg_turtle_file, format='turtle')
            logging.info(f'Finished triplifying pfas analytics tool facilities - {state1.strip()}.')
            print(f'Finished triplifying pfas analytics tool facilities - {state1.strip()}.')

        #records with no state at all go to one generic file so they are not silently dropped
        df_nostate = df[df['State'].isna()]
        if len(df_nostate) > 0:
            kg = triplify(df_nostate)
            kg.serialize(output_dir / "epa-frs-data-unknown-pat.ttl", format='turtle')
            logging.info(f'Triplified {len(df_nostate)} PAT facilities with no state.')
            print(f'Finished triplifying pfas analytics tool facilities with no state ({len(df_nostate)} records).')

def load_data():
    #df = pd.read_csv(data_dir / f"industrysectors_{state}.csv")
    #df = pd.read_excel(data_dir/ 'industrysectors_9315b09b-eb10-456e-8f66-45d6f2586b50.xlsx')
    df = pd.read_excel(data_dir/ 'industrysectors_f3cfa581-fda9-497c-bdda-b05ac08d2b01.xlsx')
    #df = pd.read_json(data_dir / '')
    #replace - with nan
    df.replace(to_replace='-', value=pd.NA, inplace=True)
    print(df.info(verbose=True))
    logger = logging.getLogger('Data loaded to dataframe.')
    return df


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


def triplify(df) -> Graph:
    kg = new_graph()

    df = clean_attributes(df)
    for idx, row in df.iterrows():
        facility = get_attributes(row)
        facility_iri = get_iris(facility)
        if facility != False and facility_iri != False:
            #create facility
            kg.add((facility_iri, RDF.type, epa_frs["FRS-Facility"]))
            kg.add((facility_iri, RDF.type, epa_frs["EPA-PFAS-Facility"]))

    return kg


if __name__ == "__main__":
    main()