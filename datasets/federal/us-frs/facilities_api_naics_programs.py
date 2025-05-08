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
state_code= input("state abbreviation?")  #'ME'
state= state_code
code_dir = Path(__file__).resolve().parent.parent
root_folder =Path(__file__).resolve().parent.parent.parent
output_dir = root_folder / "federal/us-frs/triples/"
logname = "log"
testing = False #only gets 15 records when set to true

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
        facilities_count = 15
        increment = 15
        limit = 15

    # query the facilities 10000 (limit) at a time, and merge into one list
    while True: #limit < facilities_count+increment:
        facilities_url = f'https://data.epa.gov/efservice/frs.v_pub_frs_naics_ez/state_code/equals/{state_code}/left/frs.frs_interest/left/frs.frs_supplemental_interest/{start}:{limit}/json' #join/frs.frs_supplemental_interest/
        print(facilities_url)
        resp = urllib3.request("GET", facilities_url)
        facilities_subset = resp.json()
        if facilities_subset == []:
            # stop when there are no results left
            break
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
    fac['pgm_sys_acrnm'] = fac['pgm_sys_acrnm'].apply(lambda x: x.upper().replace("/", "-")) #this is the main program for the naics code
    fac['frs.frs_interest.pgm_sys_acrnm'] = fac['frs.frs_interest.pgm_sys_acrnm'].apply(lambda x: x.upper().replace("/", "-") if pd.notnull(x) else None) #program for main federal programs
    fac['frs.frs_supplemental_interest.pgm_sys_acrnm'] = fac['frs.frs_supplemental_interest.pgm_sys_acrnm'].apply(lambda x: x.upper().replace("/", "-") if pd.notnull(x) else None) #program for supplemental
    
    fac['interest_id'] = fac['pgm_sys_id']
    #fac['sup_pgm_interest_id'] = fac['frs.frs_supplemental_interest.pgm_sys_id']
    #fac['interest_type'] = fac['interest_type'].apply(lambda x:''.join(x.title().split()))
    
    replacements = str.maketrans({"(":"- ",
                     ")":"",
                     "&":"",
                     "-":"- ",
                     "/":" ",
                     ",":"",
                     ":":"-"})
    
    fac['interest_type'] = fac['interest_type'].apply(lambda x: (''.join(((word if word in ['NSR', 'NPDES', 'ICIS', 'OSHA', 'ICIS-', 'CESQG', 'SQG', 'AFO','SW', 'BRAC', 'CZM', 'EPCRA', 'FRP', 'LQG', "II", "WIPP", 'NPL', 'TRI', 'TSCA', 'TSD', "UIC", 'VSQG', 'NESHAPS', 'SPCC'] else word.title()) for word in x.translate(replacements).split()))))
    fac['sup_interest_type'] = fac['sup_interest_type'].apply(lambda x: (''.join(((word if word in ['NSR', 'NPDES', 'ICIS', 'OSHA', 'ICIS-', 'CESQG', 'SQG', 'AFO','SW', 'BRAC', 'CZM', 'EPCRA', 'FRP', 'LQG', "II", "WIPP", 'NPL', 'TRI', 'TSCA', 'TSD', "UIC", 'VSQG', 'NESHAPS', 'SPCC'] else word.title()) for word in x.translate(replacements).split()))) if not pd.isna(x) else None)
    fs_lookup = {'F':'Federal', 'S': 'State', 'T':'Tribal', 'P':'Private'}
    fac['fed_state_desc'] = fac['fed_state_code'].apply(lambda x: fs_lookup[x] if pd.notnull(x) else pd.NA)
    
    fac['interest_label'] = fac[['active_status', 'frs.frs_interest.pgm_sys_acrnm', 'frs.frs_interest.pgm_sys_id', "reported_sup_interest_type", 'sup_pgm_sys_id']].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
    fac['interest_description'] = fac[['start_date_qualifier','start_date','end_date_qualifier','end_date']].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1) 
    fac['start_date'] = pd.to_datetime(fac['start_date'], format='%Y-%m-%d %H:%M:%S')
    fac['sup_start_date'] = pd.to_datetime(fac['frs.frs_supplemental_interest.start_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    fac['end_date'] = pd.to_datetime(fac['end_date'], format='%Y-%m-%d %H:%M:%S')
    fac['sup_end_date'] = pd.to_datetime(fac['frs.frs_supplemental_interest.end_date'], format='%Y-%m-%d %H:%M:%S')
    fac['create_date'] = pd.to_datetime(fac['create_date'], format='%Y-%m-%d %H:%M:%S')
    fac['update_date'] = pd.to_datetime(fac['update_date'], format='%Y-%m-%d %H:%M:%S')
    fac['sup_create_date'] = pd.to_datetime(fac['frs.frs_supplemental_interest.create_date'], format='%Y-%m-%d %H:%M:%S')
    fac['sup_update_date'] = pd.to_datetime(fac['frs.frs_supplemental_interest.update_date'], format='%Y-%m-%d %H:%M:%S')
    
    #fac['last_reported_date']

    # drop attributes that won't be triplified or referenced
    fac = fac.drop(axis=1, labels=['city_name', 'country_name', 'county_name', 'epa_region_code', 'legislative_dist_num', 'location_address', 'postal_code', 'supplemental_location','state_name', 'tribal_land_code', 'tribal_land_name'])
    fac = fac.drop(axis=1, labels=["code_description", "latitude83", "longitude83", "primary_name", "small_bus_ind", "state_code"])
    print("USED SCHEMA:")
    print(fac.info())
    #print(fac.start_date.unique())
    #print(fac.end_date.unique())

    return fac


def get_iris(facility):
    #build iris for any entities
    #print(facility)
    facility_iri = epa_frs_data[f"d.FRS-Facility.{facility['registry_id']}"]
    facility_class = epa_frs[f"{facility['pgm_sys_acrnm'].upper()}-Facility"] #can also infer this

    #geo_iri = epa_frs_data[f"d.FRS-Facility-Geometry.{facility['registry_id']}"]
    naics_iri = naics[f"NAICS-{facility['naics_code']}"]
    interest = {}
    if pd.notnull(facility['sup_interest_id']):
        interest['iri'] = epa_frs_data[f"d.EnvironmentalInterest.Supplemental.{facility['frs.frs_supplemental_interest.pgm_sys_acrnm']}.{facility['sup_pgm_sys_id']}"]
        interest['class'] = epa_frs[facility['sup_interest_type']]
    else: # pd.notnull(facility['pgm_sys_id']): #facility['fed_state_code'] in ['F'] and facility['pgm_sys_acrnm'] != 'NPDES':
        interest['iri'] = epa_frs_data[f"d.EnvironmentalInterest.{facility['frs.frs_interest.pgm_sys_acrnm']}.{facility['interest_id']}"]
        interest['class'] = epa_frs[facility['interest_type']]
    
        

    return facility_iri, naics_iri, facility_class, interest


def triplify(facilities):
    kg = Initial_KG()

    facilities = clean_attributes(facilities)

    for idx, facility in facilities.iterrows():
        #get iris
        facility_iri, naics_iri, facility_class, interest = get_iris(facility)

        #create facility
        kg.add((facility_iri, RDF.type, epa_frs["FRS-Facility"]))
        kg.add((facility_iri, RDF.type, facility_class))
        kg.add((facility_iri, epa_frs[f'ofIndustry.{facility.pgm_sys_acrnm}'], naics_iri)) #subproperty for fio:ofIndustry
        kg.add((facility_iri, epa_frs[f'hasIdentifier.{facility.pgm_sys_acrnm}'], Literal(facility.pgm_sys_id, datatype=XSD.string))) #subproperty for dcterms:identifier
        
        if facility.primary_indicator == 'primary':
            kg.add((facility_iri, epa_frs[f'{facility.primary_indicator}Industry'], naics_iri)) #subproperty for fio:ofIndustry

        #environmental Interest
        kg.add((facility_iri, epa_frs['hasEnvironmentalInterest'], interest['iri']))
        if pd.notnull(facility.start_date):
            kg.add((interest['iri'], PROV.startedAtTime, Literal(facility['start_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
            if facility.start_date_qualifier == 'CLS':
                kg.add((interest['iri'], PROV.endedAtTime, Literal(facility['start_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.sup_start_date):
            kg.add((interest['iri'], PROV.startedAtTime, Literal(facility['sup_start_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.end_date):
            kg.add((interest['iri'], PROV.endedAtTime, Literal(facility['end_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.sup_end_date):
            kg.add((interest['iri'], PROV.endedAtTime, Literal(facility['sup_end_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.create_date):
            kg.add((interest['iri'], DCTERMS.created, Literal(facility['create_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.sup_create_date):
                    kg.add((interest['iri'], DCTERMS.created, Literal(facility['sup_create_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.update_date):
            kg.add((interest['iri'], schema['dateModified'], Literal(facility['update_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))
        if pd.notnull(facility.sup_update_date):
            kg.add((interest['iri'], schema['dateModified'], Literal(facility['sup_update_date'].strftime('%Y-%m-%dT%H:%M:%S') , datatype=XSD.dateTime)))


        kg.add((interest['iri'], RDF.type, interest['class']))

        if pd.notnull(facility.interest_description) and facility.interest_description != "":
            kg.add((interest['iri'], DCTERMS.description, Literal(facility['interest_description'], datatype=XSD.string)))
        if pd.notnull(facility.interest_label) and facility.interest_label != "":
            kg.add((interest['iri'], RDFS.label, Literal(facility.interest_label, datatype=XSD.string)))
        if pd.notnull(facility['sup_pgm_sys_id']):
            kg.add((interest['iri'], DCTERMS.identifier, Literal(f"{facility['sup_pgm_sys_acrnm']}:{facility['sup_pgm_sys_id']}", datatype=XSD.string)))
        if pd.notnull(facility.source_of_data):
            pass

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
        kg_turtle_file = output_dir/ f"us-frs-data-facility-naics-{state}-test.ttl"
    else:
        kg_turtle_file = output_dir / f"us-frs-data-facility-naics-{state}.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger(f'Finished triplifying {state} program facilities and NAICS codes.')


if __name__ == "__main__":
    main()