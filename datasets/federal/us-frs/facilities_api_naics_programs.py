import requests
import json
import urllib3
import geopandas
import pandas as pd
import xml.etree.ElementTree as ET
import math
import datetime
from datetime import date

from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS, DCTERMS, GEO
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from shapely.geometry import Point
from pathlib import Path

import logging

# This script gets facilities by specified state from the epa envriofacts rest api for frs facility sites (FRS_FACILITY_SITE). It also attempts to get the facility location from the epa GEO_FACILITY_POINT api. 

## declare variables
state_code= input("state abbreviation?")  #'ME'
state= state_code
code_dir = Path(__file__).resolve().parent.parent
root_folder =Path(__file__).resolve().parent.parent.parent
output_dir = root_folder / "federal/us-frs/triples/"
logname = "log"
testing = False  #only gets 5 records when set to true

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

    # count function does not appear to work for this table
    #count_req = f'https://data.epa.gov/efservice/frs.v_pub_frs_naics_ez/STATE_CODE/=/{state_code}/COUNT'
    #count_url = urllib3.request("GET", count_req).data
    #tree = ET.fromstring(count_url)
    #facilities_count = int(tree[0][0].text)
    #print('facilities count:', facilities_count)
    #logging.info(f"found {facilities_count} facilities for {state_code}.")

    facilities = []
    limit = 10000
    increment= 1000
    start = 0

    #temporary limit to 5 for testing
    if testing == True:
        facilities_count = 5
        increment = 5
        limit = 5

    # query the facilities 10000 (limit) at a time, and merge into one list
    while True: #limit < facilities_count+increment:
        facilities_url = f'https://data.epa.gov/efservice/frs.v_pub_frs_naics_ez/state_code/equals/{state_code}/join/frs.frs_supplemental_interest/{start}:{limit}/json'
        print(facilities_url)
        resp = urllib3.request("GET", facilities_url)
        facilities_subset = resp.json()
        if facilities_subset == []:
            # stop when there are no results left
            break
        print(facilities_subset[0])
        print(type(facilities_subset[0]))
        if 'error' in facilities_subset[0].keys():
            #stop if an error is returned from the server
            print(facilities_subset['error'])
            break
        #print(facilities_subset)
        for facility in facilities_subset:
            facilities.append(facility)
        
        start += limit
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
    kg.bind('epa_frs', epa_frs)
    kg.bind('epa_frs_data', epa_frs_data)
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
    print('FULL SCHEMA:')
    print(fac.info())
    
    # format various columns for triplification
    fac['primary_indicator'] = fac['primary_indicator'].apply(lambda x: x.lower())
    fac['pgm_sys_acrnm'] = fac['pgm_sys_acrnm'].apply(lambda x: x.lower().replace("/", "-"))
    # drop attributes that won't be triplified or referenced
    fac = fac.drop(axis=1, labels=['city_name', 'country_name', 'county_name', 'epa_region_code', 'legislative_dist_num', 'location_address', 'postal_code', 'supplemental_location','state_name', 'tribal_land_code', 'tribal_land_name'])
    fac = fac.drop(axis=1, labels=["code_description", "latitude83", "longitude83", "primary_name", "small_bus_ind", "source_of_data", "state_code"])
    print("USED SCHEMA:")
    print(fac.info())

    return fac


def get_iris(facility):
    #build iris for any entities
    #print(facility)
    #facility_iri = epa_frs_data[f"d.FRS-Facility.{facility['registry_id']}"]
    facility_iri = epa_frs_data[f"d.PGM-Facility.{facility['pgm_sys_id']}"]

    #geo_iri = epa_frs_data[f"d.FRS-Facility-Geometry.{facility['registry_id']}"]
    naics_iri = naics[f"NAICS-{facility['naics_code']}"]


    return facility_iri, naics_iri


def triplify(facilities):
    kg = Initial_KG()

    facilities = clean_attributes(facilities)

    for idx, facility in facilities.iterrows():
        #get iris
        facility_iri, naics_iri = get_iris(facility)

        #create facility
        kg.add((facility_iri, RDF.type, epa_frs["PGM-Facility"]))
        kg.add((facility_iri, epa_frs[f'{facility.pgm_sys_acrnm}-Industry'], naics_iri))
        kg.add((facility_iri, epa_frs[f'has{str(facility.pgm_sys_acrnm).upper()}id'], Literal(facility.pgm_sys_id, datatype=XSD.string)))
        if facility.primary_indicator == 'primary':
            kg.add((facility_iri, epa_frs[f'{facility.primary_indicator}Industry'], naics_iri))

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
        kg_turtle_file = f"us-frs-data-facility-naics-{state}-test.ttl".format(output_dir)
    else:
        kg_turtle_file = f"us-frs-data-facility-naics-{state}.ttl".format(output_dir)
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger('Finished triplifying pfas analytics tool facilities.')


if __name__ == "__main__":
    main()