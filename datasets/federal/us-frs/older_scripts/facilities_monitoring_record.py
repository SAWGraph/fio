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

import logging

# This script gets facilities by specified state from the epa envriofacts rest api for frs facility sites (FRS_FACILITY_SITE). It also attempts to get the facility location from the epa GEO_FACILITY_POINT api. 

## declare variables
program= input("program acronym?")  #'ME'
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
logging.info(f"Getting facility programs and naics for {program} from server.")

def load_data():
    '''Get the facilities as a list of dictionaries from the EPA ECHO API '''

    # count function does not appear to work for this table
    #count_req = f'https://data.epa.gov/efservice/frs.frs_interest/PGM_SYS_ACRNM/=/{program}/COUNT'
    #count_url = urllib3.request("GET", count_req).data
    #print(count_url)
    #tree = ET.fromstring(count_url)
    #facilities_count = int(tree[0][0].text)
    #print('facilities count:', facilities_count)
    #logging.info(f"found {facilities_count} facilities for {state_code}.")

    facilities = []
    increment = 50000
    start = 0
    limit = start + increment
    

    #temporary limit to 5 for testing
    if testing == True:
        facilities_count = 15
        increment = 15
        limit = 15

    # query the facilities 10000 (limit) at a time, and merge into one list
    while True: #limit < facilities_count+increment:
        facilities_url = f'https://data.epa.gov/efservice/frs.frs_interest/pgm_sys_acrnm/equals/{program}/{start}:{limit}/json' #join/frs.frs_supplemental_interest/
        print(facilities_url)
        resp = urllib3.request("GET", facilities_url)
        facilities_subset = resp.json()
        #print(facilities_subset)
        if facilities_subset == []:
            # stop when there are no results left
            break
        #if verbose:
            #print(facilities_subset[0])
        if 'error' in facilities_subset[0].keys():
            #stop if an error is returned from the server
            print(facilities_subset['error'])
            break
        #print(facilities_subset)
        for facility in facilities_subset:
            facilities.append(facility)
        
        start += increment
        print(f'retrieved {limit}')
        limit += increment

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
    if verbose:
        print(fac.info())
    fac['create_date'] = pd.to_datetime(fac['create_date'], format='%Y-%m-%d %H:%M:%S')
    fac['update_date'] = pd.to_datetime(fac['update_date'], format='%Y-%m-%d %H:%M:%S')
    fac['start_date'] = pd.to_datetime(fac['start_date'], format='mixed', errors='coerce')
    fac['end_date'] = pd.to_datetime(fac['end_date'], format='mixed', errors='coerce')
    fac['pgm_sys_id'] = fac['pgm_sys_id'].replace(" ", "_")

    replacements = str.maketrans({"(":"- ",
                     ")":"",
                     "&":"",
                     "-":"- ",
                     "/":" ",
                     ",":"",
                     ":":"-"})
    fac['interest_type'] = fac['interest_type'].apply(lambda x: (''.join(((word if word in ['NSR', 'NPDES', 'ICIS', 'OSHA', 'ICIS-', 'CESQG', 'SQG', 'AFO','SW', 'BRAC', 'CZM', 'EPCRA', 'FRP', 'LQG', "II", "WIPP", 'NPL', 'TRI', 'TSCA', 'TSD', "UIC", 'VSQG', 'NESHAPS', 'SPCC'] else word.title()) for word in x.translate(replacements).split()))))
    return fac

def get_iris(facility):
    iris = {}

    iris['monitoring'] = epa_frs_data[f"d.MonitoringRecord.{facility['pgm_sys_acrnm']}.{facility['pgm_sys_id']}"]
    iris['program'] =  epa_frs_data[f"d.Program.{facility['pgm_sys_acrnm'].upper()}"] 
    iris['interest'] = epa_frs_data[f"d.EnvironmentalInterestType.{facility['interest_type']}"]

    return iris

def triplify(facilities):
    kg = Initial_KG()
    facilities = clean_attributes(facilities)


    for idx, facility in facilities.iterrows():
        iris = get_iris(facility)
        kg.add((iris['monitoring'], RDF.type, epa_frs['MonitoringRecord']))

        if pd.notnull(facility.start_date):
                kg.add((iris['monitoring'], PROV.startedAtTime, Literal(facility['start_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
                if facility.start_date_qualifier == 'CLS':
                    kg.add((iris['monitoring'], PROV.endedAtTime, Literal(facility['start_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.end_date):
                kg.add((iris['monitoring'], PROV.endedAtTime, Literal(facility['end_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.create_date):
                kg.add((iris['monitoring'], DCTERMS.created, Literal(facility['create_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.update_date):
                kg.add((iris['monitoring'], DCTERMS.modified, Literal(facility['update_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))

        kg.add((iris['monitoring'], epa_frs['ofInterestType'], iris['interest']))
        kg.add((iris['monitoring'], epa_frs['fromSystem'], iris['program']))
    return kg

def main():
    '''main function initializes all other functions'''
    data = load_data()
    kg = triplify(data)
    if testing:
        kg_turtle_file = output_dir/ f"epa-frs-data-facility-{program}-test.ttl"
    else:
        kg_turtle_file = output_dir / f"epa-frs-data-facility-{program}.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger(f'Finished triplifying {program} program facilities.')

if __name__ == "__main__":
    main()