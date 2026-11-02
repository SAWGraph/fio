import requests
import json
import urllib3
import geopandas
import pandas as pd
#import xml.etree.ElementTree as ET
import math
import datetime
from datetime import date

from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS, DCTERMS, GEO, PROV
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from shapely.geometry import Point
from pathlib import Path
from frs_utils import (epa_frs, epa_frs_data, fio, naics, sic, kwgr, kwg_ont, coso, schema,
                       OUTPUT_DIR, setup_logging, get_state, new_graph, fetch_all, clean_iri_part, safe_local, report_cleaned)
import urllib.parse

import logging


## declare variables
state_code = get_state()  #'ME'
state= state_code
output_dir = OUTPUT_DIR
testing = False #only gets 15 records when set to true
verbose = False

## initiate log file
setup_logging()
if testing:
    logging.info(f'****** Testing Run *********')
logging.info(f"***** Getting facility programs NAICS for {state_code} from server.")

def load_data():
    '''Get the facilities as a list of dictionaries from the EPA ECHO API '''

    url = f'https://data.epa.gov/efservice/frs.frs_program_facility/state_code/equals/{state_code}/join/frs.frs_naics/pgm_sys_id/equals/pgm_sys_id/pgm_sys_acrnm/equals/pgm_sys_acrnm/{{start}}:{{limit}}/json'
    facilities = fetch_all(url, timeout=30, test_size=15 if testing else None, verbose=verbose)
    logging.info(f'finished fetching facilities.')
    return facilities


def clean_attributes(facilities):
    # load to pandas dataframe from list of dictionaries 
    fac = pd.DataFrame(facilities)

    fac = fac.dropna(axis=1, how='all') #remove columns with no data
    # format various columns for triplification
    
    fac['pgm_sys_acrnm'] = fac['pgm_sys_acrnm'].apply(lambda x: clean_iri_part(x).upper()) #this is the main program for the naics code
    fac['pgm_sys_id'] = fac['pgm_sys_id'].apply(clean_iri_part)

    #fac['create_date'] = pd.to_datetime(fac['create_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    #fac['update_date'] = pd.to_datetime(fac['update_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    #fac['naics_code']
    #fac['naics_uin']

    if verbose:
        print("USED SCHEMA:")
        print(fac.info())

    return fac


def get_iris(facility):
    #build iris for any entities
    #print(facility)
    iri={}
    iri['record'] = epa_frs_data[safe_local(f"d.Record.{facility['pgm_sys_acrnm']}.{facility['pgm_sys_id']}")]   
    iri['naics'] = naics[safe_local(f"NAICS-{facility['naics_code']}")]
    if facility['primary_indicator'] == 'PRIMARY':
        iri['ofIndustry'] = epa_frs['ofPrimaryIndustry']
    elif facility['primary_indicator'] == 'SECONDARY':
        iri['ofIndustry'] = epa_frs['ofSecondaryIndustry']
    else:
        iri['ofIndustry'] = fio['ofIndustry']
    return iri


def triplify(facilities):
    kg = new_graph()

    facilities = clean_attributes(facilities)

    for idx, facility in facilities.iterrows():
        #get iris
        iri = get_iris(facility)

        #create facility
        if pd.notnull(facility['naics_code']) and facility['naics_code'] != '999999':
            kg.add((iri['record'], iri['ofIndustry'], iri['naics']))
        

    report_cleaned()

    return kg

def main():
    '''main function initializes all other functions'''
    data = load_data()
    kg = triplify(data)
    if testing:
        kg_turtle_file = output_dir/ f"epa-frs-data-{state}-facility-naics-test.ttl"
    else:
        kg_turtle_file = output_dir / f"epa-frs-data-{state}-facility-naics.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger(f'Finished triplifying {state} program facilities and NAICS codes.')


if __name__ == "__main__":
    main()