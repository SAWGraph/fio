import requests
import json
import urllib3
import geopandas
import pandas as pd
import xml.etree.ElementTree as ET
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

    #count_req = f'https://data.epa.gov/efservice/FRS_SUPPLEMENTAL_INTEREST/STATE_CODE/=/{state_code}/COUNT'
    #count_url = urllib3.request("GET", count_req).data
    #print(count_url)
    #tree = ET.fromstring(count_url)
    #facilities_count = int(tree[0][0].text)
    #print('facilities count:', facilities_count)
    #logging.info(f"found {facilities_count} facilities for {state_code}.")

    #temporary limit to 5 for testing
    if testing == True:
        facilities_count = 15
        increment = 15
        limit = 15

    # query the facilities 10000 (limit) at a time, and merge into one list
    while True: #limit < facilities_count+increment:
        facilities_url = f'https://data.epa.gov/efservice/frs.frs_program_facility/state_code/equals/{state_code}/join/frs.frs_supplemental_interest/pgm_sys_id/equals/pgm_sys_id/pgm_sys_acrnm/equals/pgm_sys_acrnm/{start}:{limit}/json' #join/frs.frs_supplemental_interest/
        print(facilities_url)
        resp = urllib3.request("GET", facilities_url, timeout=10)
        facilities_subset = resp.json()
        if facilities_subset == []:
            # stop when there are no results left
            break
        if verbose:
            print(facilities_subset[0])
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
    #fac = fac.dropna(axis=1, how='all')
    if verbose:
        print('FULL SCHEMA:')
        print(fac.info())
    
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
    
    fac['sup_pgm_sys_acrnm'] = fac['sup_pgm_sys_acrnm'].apply(lambda x: x.translate(replacements).upper() if pd.notnull(x) else None) #program for main federal programs
    # if interest type is npdes, override system and set to npdes to match other iris
    mask = fac['sup_interest_type'].apply(lambda x: True if 'NPDES' in x else False)
    fac.loc[mask, 'sup_pgm_sys_acrnm'] = 'NPDES'

    fac['interest_id'] = fac['pgm_sys_id'].apply(lambda x: x.translate(replacements))
    fac['sup_pgm_sys_id'] = fac['sup_pgm_sys_id'].apply(lambda x: x.translate(replacements) if pd.notnull(x) else None)
    fac['sup_interest_id'] = fac['sup_interest_id']
    #fac['interest_type'] = fac['interest_type'].apply(lambda x:''.join(x.title().split()))
    

    
    fac['interest_type'] = fac['sup_interest_type'].apply(lambda x: (''.join(((word if word in ['NSR', 'NPDES', 'ICIS', 'OSHA', 'ICIS-', 'CESQG', 'SQG', 'AFO','SW', 'BRAC', 'CZM', 'EPCRA', 'FRP', 'LQG', "II", "WIPP", 'NPL', 'TRI', 'TSCA', 'TSD', "UIC", 'VSQG', 'NESHAPS', 'SPCC'] else word.title()) for word in x.translate(replacements).split()))) if not pd.isna(x) else None)
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


def get_iris(facility):
    #build iris for any entities
    #print(facility)
    facility_iri = epa_frs_data[f"d.FRS-Facility.{facility['registry_id']}"]
    record_iri = epa_frs_data[f"d.Record.{facility['pgm_sys_acrnm']}.{facility['interest_id']}"]
    if pd.notnull(facility['sup_pgm_sys_id']):
        sup_iri = epa_frs_data[f"d.Record.{facility['sup_pgm_sys_acrnm']}.{facility['sup_pgm_sys_id']}"]
    else:
        sup_iri = epa_frs_data[f"d.Record.{facility['sup_pgm_sys_acrnm']}.{facility['sup_interest_id']}"]
    program = epa_frs[f"{facility['sup_pgm_sys_acrnm']}"] 
    
    interest = {}

    if pd.notnull(facility['frs.frs_supplemental_interest.pgm_sys_acrnm']):
        interest['class'] = epa_frs_data[f"d.EnvironmentalInterestType.{facility['interest_type']}"]

    
        

    return facility_iri, record_iri, sup_iri, program, interest


def triplify(facilities):
    kg = Initial_KG()

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
        kg.add((sup_iri, DCTERMS.identifier, Literal(facility.sup_pgm_sys_id, datatype=XSD.string)))
        if pd.notnull(facility.start_date):
            kg.add((sup_iri, PROV.startedAtTime, Literal(facility['start_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
            if facility.start_date_qualifier == 'CLS':
                kg.add((sup_iri, PROV.endedAtTime, Literal(facility['start_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.end_date):
            kg.add((sup_iri, PROV.endedAtTime, Literal(facility['end_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.create_date):
            kg.add((sup_iri, DCTERMS.created, Literal(facility['create_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.update_date):
            kg.add((sup_iri, DCTERMS.modified, Literal(facility['update_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
    
        if 'class' in interest.keys():
            #environmental Interest
            kg.add((sup_iri, epa_frs['ofInterestType'], interest['class']))

            if pd.notnull(facility.interest_description) and facility.interest_description != "":
                kg.add((sup_iri, DCTERMS.description, Literal(facility['interest_description'], datatype=XSD.string)))
            if pd.notnull(facility.interest_label) and facility.interest_label != "" and facility.sup_pgm_sys_acrnm != 'NPDES': #don't add label for NPDES as they are already in regular records. 
                kg.add((sup_iri, RDFS.label, Literal(facility.interest_label, datatype=XSD.string)))
        

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
        kg_turtle_file = output_dir/ f"epa-frs-data-facility-sup-record-{state}-test.ttl"
    else:
        kg_turtle_file = output_dir / f"epa-frs-data-facility-sup-record-{state}.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger(f'Finished triplifying {state} program facilities and NAICS codes.')


if __name__ == "__main__":
    main()