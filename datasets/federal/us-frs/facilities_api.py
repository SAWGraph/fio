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
testing = False  #only gets 200 records when set to true
verbose = False

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
logging.info(f"Getting facilities for {state_code} from server.")

def load_data():
    '''Get the facilities as a list of dictionaries from the EPA ECHO API '''
    count_req = f'https://data.epa.gov/efservice/FRS_FACILITY_SITE/STD_STATE_CODE/=/{state_code}/COUNT'

    count_url = urllib3.request("GET", count_req).data
    tree = ET.fromstring(count_url)
    facilities_count = int(tree[0][0].text)
    print('facilities count:', facilities_count)
    logging.info(f"found {facilities_count} facilities for {state_code}.")

    facilities = []
    limit = 10000
    increment= 10000
    start = 0

    #temporary limit to 5 for testing
    if testing == True:
        facilities_count = 200
        increment = 200
        limit = 200

    # query the facilities 10000 (limit) at a time, and merge into one list
    while limit < facilities_count+increment:
        facilities_url = f'https://data.epa.gov/efservice/frs.frs_facility_site/std_state_code/equals/{state_code}/left/frs.geo_facility_point/{start}:{limit}/JSON'
        resp = urllib3.request("GET", facilities_url, timeout=10)
        facilities_subset = resp.json()
        print(facilities_url)
        for facility in facilities_subset:
            facilities.append(facility)
        
        start += increment
        print(f'retrieved to {limit}')
        limit += increment

    #report count of records
    print(len(facilities), ' facilities found')
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

def get_point(registry_id):
    '''Gets a WKT string based on a registry id from the FRS envirofacts api.
    Note this is no longer used as a join in the initial query performed better. Preserved for reference. '''
    print(registry_id)
    url = f'https://data.epa.gov/efservice/GEO_FACILITY_POINT/REGISTRY_ID/=/{registry_id}/JSON'
    #print(url)
    resp = urllib3.request("GET", url)
    #print(resp.status)
    if int(resp.status) == 200:
        try:
            facility_point = resp.json()
            if verbose:
                print(facility_point)
            shape_pt = Point(facility_point[0]['longitude83'], facility_point[0]['latitude83'])
            facility_WKT = shape_pt.wkt
        except:
            print(f'geometry error facility:{registry_id}')
            facility_WKT = None
    return facility_WKT

def get_WKT(lat, long):
    try:
        wkt = Point(long, lat).wkt
    except:
        wkt = None
    if str(wkt) == "POINT EMPTY":
        wkt = None
    return wkt

def clean_attributes(facilities):
    #load to pandas dataframe from list of dictionaries 
    fac = pd.DataFrame(facilities)
    if verbose:
        print('FULL SCHEMA')
        print(fac.info())
    
    #format various columns for triplification
    fac['federal_bool'] = fac['federal_facility_code'].map({"Y": True, "N": False}) #boolean for federal sites
    #print('tribal:', fac['tribal_land_code'].value_counts())
    fac['tribal_bool'] = fac['tribal_land_code'].map({"Y": True, "N": False}) #boolean for tribal sites
    fac['small_business_bool'] = fac.small_bus_ind.map({"Y": True, "N": False})
    fac = fac.assign(siteType = lambda x: x.site_type_name.str.title().str.replace(' ','')) #reformated type for use in Facility subclass
    fac['updated'] = pd.to_datetime(fac['update_date'], format="%d-%b-%y") #updated date to pd.datetime
    fac['created'] = pd.to_datetime(fac['create_date'], format="%d-%b-%y") #created date to pd.datetime
    fac['refreshed'] = pd.to_datetime(fac['refresh_date'], format="%d-%b-%y") #refreshed date to pd.datetime
    fac['geo_time'] = pd.to_datetime(fac['timestamp'], format='%Y-%m-%d %H:%M:%S')
    fac['WKT'] = fac.apply(lambda x: get_WKT(x.latitude83, x.longitude83), axis=1)
    if verbose:
        print(fac.operating_status.unique())
    #drop attributes that won't be triplified or referenced
    fac = fac.drop(axis=1, labels=['state_name', 'location_address', 'supplemental_location', 'epa_region_code', 'data_quality_code', 'user_id', 'interest_status_code', 'std_city_name', 'std_county_name', 'legislative_dist_num', 'objectid', 'std_postal_code', 'std_country','country_name', 'county_name', 'std_stype_before', 'std_base_name', 'std_stype_after',  'city_name', 'std_street_name', 'postal_code', 'fips_code', 'std_house_number', 'icis_identifier', 'review_flag', 'state_code', 'std_suffix', 'review_reason', 'sensitive_ind', 'stand_alone_flag', 'public_ind'])
    #drop additional attributes that have been reformated
    fac = fac.drop(axis=1, labels=['federal_facility_code', 'tribal_land_code', 'timestamp', 'update_date', 'create_date', 'refresh_date', 'small_bus_ind'])
    if verbose:
        print('USED SCHEMA')
        print(fac.info())


    return fac


def get_iris(facility):
    #build iris for any entities
    #print(facility)
    facility_iri = epa_frs_data[f"d.FRS-Facility.{facility['registry_id']}"]
    geo_iri = epa_frs_data[f"d.FRS-Facility-Geometry.{facility['registry_id']}"]
    extra_iris ={}

    if pd.notnull(facility['std_county_fips']):
        extra_iris['county_iri'] = kwgr['administrativeRegion.USA.' + str(facility['std_county_fips'])]  # align to Admin 2 in Spatial Graph
        
    if pd.notnull(facility['federal_agency_code']):
        agency_iri = epa_frs_data['d.Agency.'+str(facility['federal_agency_code'])] #agency codes defined frs.frs_agency_ref in controlled vocab script
        extra_iris['agency'] = agency_iri
    
    #siteType to class
    if pd.notnull(facility['siteType']) and facility['siteType'] != 'Facility':
            extra_iris['type'] = epa_frs_data[f"d.{facility['siteType']}-Facility"]

    return facility_iri, geo_iri, extra_iris


def triplify(facilities):
    kg = Initial_KG()

    facilities = clean_attributes(facilities)

    for idx, facility in facilities.iterrows():
        #get iris
        facility_iri, geo_iri, extra_iris = get_iris(facility)

        #create facility
        kg.add((facility_iri, RDF.type, epa_frs["FRS-Facility"]))
        kg.add((facility_iri, RDFS.label, Literal(facility['primary_name'], datatype= XSD.string)))
        if pd.notnull(facility.std_full_address):
            kg.add((facility_iri, schema['address'], Literal(facility['std_full_address'], datatype=XSD.string)))
        kg.add((facility_iri, DCTERMS.alternative, Literal(facility['std_name'], datatype=XSD.string)))
        kg.add((facility_iri, epa_frs['hasFRSId'], Literal(facility['registry_id'], datatype=XSD.string)))
        kg.add((facility_iri, DCTERMS.created, Literal(facility['created'].strftime('%Y-%m-%d'), datatype=XSD.date)))
        if pd.notnull(facility.updated):
            kg.add((facility_iri, DCTERMS.modified, Literal(facility['updated'].strftime('%Y-%m-%d'), datatype=XSD.date)))

        if pd.notnull(facility['std_county_fips']):
            kg.add((facility_iri, kwg_ont['sfWithin'], extra_iris['county_iri'])) 

        #geometry
        if pd.notnull(facility['WKT']):
            kg.add((facility_iri, GEO['hasGeometry'], geo_iri))
            kg.add((geo_iri, GEO["asWKT"], Literal(facility['WKT'], datatype=GEO["wktLiteral"])))
            if pd.notnull(facility.geo_time):
                kg.add((geo_iri, schema['dateModified'],  Literal(facility['geo_time'].strftime('%Y-%m-%d'), datatype=XSD.date)))
        
        #tribal
        if facility['tribal_bool']:
            kg.add((facility_iri, epa_frs['ofFacilityType'], epa_frs_data['d.Tribal-Facility'])) #TODO needs a label
            #kg.add((facility_iri, coso['locatedIn'], ))

        #federal
        if facility['federal_bool']:
            kg.add((facility_iri, epa_frs['ofFacilityType'], epa_frs_data['d.Federal-Facility'])) #TODO needs a label
            if 'agency' in extra_iris.keys():
                kg.add((facility_iri, fio['ownedBy'], extra_iris['agency']))

        #smallbusiness
        if facility['small_business_bool']:
            kg.add((facility_iri, epa_frs['ofFacilityType'], epa_frs_data['d.SmallBusiness-Facility'])) #TODO needs a label

        #siteType
        if 'type' in extra_iris.keys():
            kg.add((facility_iri, epa_frs['ofFacilityType'], extra_iris['type']))
            kg.add((extra_iris['type'], RDF.type, epa_frs['FacilityType']))
            kg.add((extra_iris['type'], RDFS.label, Literal(facility['site_type_name'])))

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
        kg_turtle_file = output_dir / f"epa-frs-data-facility-site-{state}-test.ttl"
    else:
        kg_turtle_file = output_dir / f"epa-frs-data-facility-site-{state}.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger('Finished triplifying pfas analytics tool facilities.')


if __name__ == "__main__":
    main()