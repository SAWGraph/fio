import requests
import json
import urllib3
import geopandas
import pandas as pd
import xml.etree.ElementTree as ET
import math
import datetime
from datetime import date
import numpy as np
from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS, DCTERMS, GEO, PROV
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from shapely.geometry import Point
from pathlib import Path
from frs_utils import (epa_frs, epa_frs_data, fio, naics, sic, kwgr, kwg_ont, coso, schema,
                       OUTPUT_DIR, setup_logging, get_state, new_graph, fetch_all, clean_iri_part, safe_local, report_cleaned, format_interest_type, add_record_dates)
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
logging.info(f"***** Getting facility programs and naics for {state_code} from server.")

def load_data():
    '''Get the facilities as a list of dictionaries from the EPA ECHO API '''

    url = f'https://data.epa.gov/efservice/frs.frs_program_facility/state_code/equals/{state_code}/join/frs.frs_supplemental_interest/pgm_sys_id/equals/pgm_sys_id/pgm_sys_acrnm/equals/pgm_sys_acrnm/{{start}}:{{limit}}/json'
    facilities = fetch_all(url, timeout=30, test_size=15 if testing else None, verbose=verbose)
    logging.info(f'finished fetching facilities.')
    return facilities


def clean_attributes(facilities):
    # load to pandas dataframe from list of dictionaries 
    fac = pd.DataFrame(facilities)
    #fac = fac.dropna(axis=1, how='all')
    if verbose:
        print('FULL SCHEMA:')
        print(fac.info())
    
    # format various columns for triplification
    
    fac['pgm_sys_acrnm'] = fac['pgm_sys_acrnm'].apply(lambda x: clean_iri_part(x).upper()) #this is the main program for the naics code
    
    fac['sup_pgm_sys_acrnm'] = fac['sup_pgm_sys_acrnm'].apply(lambda x: clean_iri_part(x).upper() if pd.notnull(x) else None) #program for main federal programs
    # if interest type is npdes, override system and set to npdes to match other iris
    mask = fac['sup_interest_type'].apply(lambda x: bool(pd.notnull(x) and 'NPDES' in x))
    fac.loc[mask, 'sup_pgm_sys_acrnm'] = 'NPDES'

    fac['interest_id'] = fac['pgm_sys_id'].apply(clean_iri_part)
    fac['sup_pgm_sys_id'] = fac['sup_pgm_sys_id'].apply(lambda x: clean_iri_part(x) if pd.notnull(x) else None)
    fac['sup_interest_id'] = fac['sup_interest_id'].apply(lambda x: clean_iri_part(x) if pd.notnull(x) else None)
    #fac['interest_type'] = fac['interest_type'].apply(lambda x:''.join(x.title().split()))
    

    
    fac['interest_type'] = fac['sup_interest_type'].apply(format_interest_type)
    #fs_lookup = {'F':'Federal', 'S': 'State', 'T':'Tribal', 'P':'Private'}
    #fac['fed_state_desc'] = fac['fed_state_code'].apply(lambda x: fs_lookup[x] if pd.notnull(x) else pd.NA)
    
    fac['interest_label'] = fac[['sup_pgm_sys_acrnm', "reported_sup_interest_type", 'sup_pgm_sys_id']].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
    fac['interest_description'] = fac[['reported_sup_interest_type', 'sup_pgm_sys_id']].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1) 
    fac['start_date'] = pd.to_datetime(fac['start_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    fac['end_date'] = pd.to_datetime(fac['end_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    fac['create_date'] = pd.to_datetime(fac['create_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    fac['update_date'] = pd.to_datetime(fac['update_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    #fac['last_reported_date']

    # drop attributes that won't be triplified or referenced
    #fac = fac.drop(axis=1, labels=['city_name', 'country_name', 'county_name', 'epa_region_code', 'legislative_dist_num', 'location_address', 'postal_code', 'supplemental_location','state_name', 'tribal_land_code', 'tribal_land_name'])
    #fac = fac.drop(axis=1, labels=["code_description", "latitude83", "longitude83", "primary_name", "small_bus_ind", "state_code"])
    if verbose:
        print("USED SCHEMA:")
        print(fac.info())

    return fac


def has_value(value):
    '''True for a real value; False for None, NaN or an empty string (NaN is truthy, so plain truth tests miss it)'''
    return pd.notnull(value) and value != ''


def get_iris(facility):
    #build iris for any entities
    #print(facility)
    facility_iri = epa_frs_data[safe_local(f"d.FRS-Facility.{facility['registry_id']}")]
    record_iri = epa_frs_data[safe_local(f"d.Record.{facility['pgm_sys_acrnm']}.{facility['interest_id']}")]
    if has_value(facility['sup_pgm_sys_id']) and has_value(facility['sup_pgm_sys_acrnm']):
        if len(str(facility['sup_pgm_sys_id'])) >5 and facility['sup_pgm_sys_acrnm'] != 'UST' and any(char.isdigit() for char in str(facility['sup_pgm_sys_id'])) == True: #UST ids and some others are not unique across facilities
            sup_iri = epa_frs_data[safe_local(f"d.Record.{facility['sup_pgm_sys_acrnm']}.{facility['sup_pgm_sys_id']}")]
        else:
            sup_iri = epa_frs_data[safe_local(f"d.Record.{facility['sup_pgm_sys_acrnm']}.{facility['sup_interest_id']}.{facility['sup_pgm_sys_id']}")]
    elif has_value(facility['sup_pgm_sys_acrnm']):
        sup_iri = epa_frs_data[safe_local(f"d.Record.{facility['sup_pgm_sys_acrnm']}.{facility['sup_interest_id']}")]
    elif has_value(facility['sup_pgm_sys_id']):
        sup_iri = epa_frs_data[safe_local(f"d.Record.{facility['pgm_sys_acrnm']}-Supplemental.{facility['sup_pgm_sys_id']}")]
    else:
        sup_iri = epa_frs_data[safe_local(f"d.Record.{facility['pgm_sys_acrnm']}-Supplemental.{facility['sup_interest_id']}")]

    if has_value(facility['sup_pgm_sys_acrnm']):
        program = epa_frs[safe_local(f"d.ProgramInformationSystem.{facility['sup_pgm_sys_acrnm']}")] 
    else:
        program = epa_frs[safe_local(f"d.ProgramInformationSystem.{facility['pgm_sys_acrnm']}")] 
    
    interest = {}

    if pd.notnull(facility['frs.frs_supplemental_interest.pgm_sys_acrnm']):
        interest['class'] = epa_frs_data[safe_local(f"d.EnvironmentalInterestType.{facility['interest_type']}")]

    
        

    return facility_iri, record_iri, sup_iri, program, interest


def triplify(facilities):
    kg = new_graph()

    facilities = clean_attributes(facilities)

    for idx, facility in facilities.iterrows():
        #get iris
        facility_iri, record_iri, sup_iri, program, interest = get_iris(facility)

        #create facility
        kg.add((facility_iri, RDF.type, epa_frs["FRS-Facility"]))
        #kg.add((facility_iri, RDF.type, facility_class))
        kg.add((facility_iri, epa_frs['hasRecord'], sup_iri))
        kg.add((record_iri, epa_frs['hasSupplementalRecord'], sup_iri))

        #supplemental record
        kg.add((sup_iri, epa_frs['fromSystem'], program))
        if has_value(facility.sup_pgm_sys_id):
            kg.add((sup_iri, DCTERMS.identifier, Literal(facility.sup_pgm_sys_id, datatype=XSD.string)))
        else:
            kg.add((sup_iri, DCTERMS.identifier, Literal(facility.sup_interest_id, datatype=XSD.string)))
        add_record_dates(kg, sup_iri, facility)
    
        if 'class' in interest.keys():
            #environmental Interest
            kg.add((sup_iri, epa_frs['ofInterestType'], interest['class']))

            if pd.notnull(facility.interest_description) and facility.interest_description != "":
                kg.add((sup_iri, DCTERMS.description, Literal(facility['interest_description'], datatype=XSD.string)))
            if pd.notnull(facility.interest_label) and facility.interest_label != "" and facility.sup_pgm_sys_acrnm != 'NPDES': #don't add label for NPDES as they are already in regular records. 
                kg.add((sup_iri, RDFS.label, Literal(facility.interest_label, datatype=XSD.string)))
        

    report_cleaned()

    return kg

def main():
    '''main function initializes all other functions'''
    data = load_data()
    kg = triplify(data)
    if testing:
        kg_turtle_file = output_dir/ f"epa-frs-data-{state}-program-sup-record-test.ttl"
    else:
        kg_turtle_file = output_dir / f"epa-frs-data-{state}-program-sup-record.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger(f'Finished triplifying {state} program facilities and NAICS codes.')
    print(f'Finished triplifying {state} supplemental records.')

if __name__ == "__main__":
    main()