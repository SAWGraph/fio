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
import urllib.parse

import logging


## declare variables
state_code= input("state abbreviation?")  #'ME'
state= state_code
code_dir = Path(__file__).resolve().parent.parent
root_folder =Path(__file__).resolve().parent.parent.parent
output_dir = root_folder / "federal/us-frs/triples/"
logname = "log"
testing = False #only gets 15 records when set to true
verbose = True

##namespaces
epa_frs = Namespace(f"http://w3id.org/fio/v1/epa-frs#")
epa_frs_data = Namespace(f"http://w3id.org/fio/v1/epa-frs-data#")
fio = Namespace(f"http://w3id.org/fio/v1/fio#")
naics = Namespace(f"http://w3id.org/fio/v1/naics#")
sic = Namespace(f"http://w3id.org/fio/v1/sic#")
kwgr = Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/resource/')
kwg_ont = Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/ontology/')
coso = Namespace(f'http://w3id.org/coso/v1/contaminoso#')
schema = Namespace(f'http://schema.org/')


## initiate log file
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.info(f'****** Testing Run *********')
logging.info(f"Getting facility programs and naics for {state_code} from server.")

def load_data():
    '''Get the facilities as a list of dictionaries from the EPA ECHO API '''

    facilities = []
    limit = 10000
    increment= 1000
    start = 0

    #temporary limit to 5 for testing
    if testing == True:
        facilities_count = 15
        increment = 15
        limit = 15

    # query the facilities 10000 (limit) at a time, and merge into one list
    while True: #limit < facilities_count+increment:
        facilities_url = f'https://data.epa.gov/efservice/frs.frs_program_facility/state_code/equals/{state_code}/join/frs.frs_naics/pgm_sys_id/equals/pgm_sys_id/pgm_sys_acrnm/equals/pgm_sys_acrnm/{start}:{limit}/json' #join/frs.frs_supplemental_interest/
        print(facilities_url)
        resp = urllib3.request("GET", facilities_url, timeout=30)
        facilities_subset = resp.json()
        if facilities_subset == []:
            # stop when there are no results left
            break
        #if verbose:
            #print(facilities_subset[0])
        #print(type(facilities_subset[0]))
        if 'error' in facilities_subset[0].keys():
            #stop if an error is returned from the server
            print(facilities_subset['error'])
            break
        #print(facilities_subset)
        for facility in facilities_subset:
            facilities.append(facility)
        
        start += limit
        print(f'retrieved {limit}')
        limit += limit

        #stop after one loop if testing
        if testing == True:
            break

    #report count of records
    print(len(facilities), ' facilities found')
    #report keys - what attributes are available for facilities
    #for key in facilities[0].keys():
    #    print(key)
    logging.info(f'finished fetching facilities.')
    return facilities


def Initial_KG():
    #prefixes: Dict[str, str] = _PREFIX
    kg = Graph()
    #for prefix in prefixes:
    #    kg.bind(prefix, prefixes[prefix])
    kg.bind('fio', fio)
    kg.bind('epa-frs', epa_frs)
    kg.bind('epa-frs-data', epa_frs_data)
    kg.bind('naics', naics)
    kg.bind('sic', sic)
    kg.bind('coso', coso)
    kg.bind('kwgr', kwgr)
    kg.bind('kwg-ont', kwg_ont)
    kg.bind('schema', schema)
    return kg

def clean_attributes(facilities):
    # load to pandas dataframe from list of dictionaries 
    fac = pd.DataFrame(facilities)

    fac = fac.dropna(axis=1, how='all') #remove columns with no data
    replacements = str.maketrans({"(":"- ",
                     ")":"",
                     "&":"",
                     "/":"-",
                     ",":"",
                     ":":"-",
                     " ":"",
                     "#": "-"})
    
    # format various columns for triplification
    
    fac['pgm_sys_acrnm'] = fac['pgm_sys_acrnm'].apply(lambda x: x.translate(replacements).upper()) #this is the main program for the naics code
    fac['pgm_sys_id'] = fac['pgm_sys_id'].apply(lambda x: x.translate(replacements))

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
    iri['record'] = epa_frs_data[f"d.Record.{facility['pgm_sys_acrnm']}.{facility['pgm_sys_id']}"]   
    iri['naics'] = naics[f"NAICS-{facility['naics_code']}"]
    if facility['primary_indicator'] == 'PRIMARY':
        iri['ofIndustry'] = epa_frs['ofPrimaryIndustry']
    elif facility['primary_indicator'] == 'SECONDARY':
        iri['ofIndustry'] = epa_frs['ofSecondaryIndustry']
    else:
        iri['ofIndustry'] = fio['ofIndustry']
    return iri


def triplify(facilities):
    kg = Initial_KG()

    facilities = clean_attributes(facilities)

    for idx, facility in facilities.iterrows():
        #get iris
        iri = get_iris(facility)

        #create facility
        if pd.notnull(facility['naics_code']) and facility['naics_code'] != '999999':
            kg.add((iri['record'], iri['ofIndustry'], iri['naics']))
        

    return kg

## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True
    
def main():
    '''main function initializes all other functions'''
    data = load_data()
    kg = triplify(data)
    if testing:
        kg_turtle_file = output_dir/ f"epa-frs-data-facility-naics-{state}-test.ttl"
    else:
        kg_turtle_file = output_dir / f"epa-frs-data-facility-naics-{state}.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger(f'Finished triplifying {state} program facilities and NAICS codes.')


if __name__ == "__main__":
    main()