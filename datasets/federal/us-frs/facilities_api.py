import requests
import json
import urllib3
import geopandas
import xml.etree.ElementTree as ET
import math

from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from shapely.geometry import Point
from pathlib import Path

import logging

## declare variables
state_code='ME'
state= state_code
code_dir = Path(__file__).resolve().parent.parent
root_folder =Path(__file__).resolve().parent.parent.parent
output_dir = root_folder / "federal/us-frs/"
logname = "log"

##namespaces
us_frs = Namespace(f"http://sawgraph.spatialai.org/v1/us-frs#")
us_frs_data = Namespace(f"http://sawgraph.spatialai.org/v1/us-frs-data#")
fio = Namespace(f"http://sawgraph.spatialai.org/v1/fio#")
naics = Namespace(f"http://sawgraph.spatialai.org/v1/fio/naics#")
sic = Namespace(f"http://sawgraph.spatialai.org/v1/fio/sic#")
kwgr = Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/resource/')
kwg_ont = Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/ontology/')
coso = Namespace(f'http://sawgraph.spatialai.org/v1/contaminoso#')
geo = Namespace(f'http://www.opengis.net/ont/geosparql#')

## initiate log file
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.info(f"Getting facilities for {state_code} from server.")

def load_data():
    '''Get the facilities as a list of dictionaries from the EPA ECHO API '''
    count_req = f'https://data.epa.gov/efservice/FRS_FACILITY_SITE/STD_STATE_CODE/=/{state_code}/COUNT'

    count_url = urllib3.request("GET", count_req).data
    tree = ET.fromstring(count_url)
    facilities_count = int(tree[0][0].text)
    print(facilities_count)

    facilities = []
    limit = 10000
    start = 0


    while limit < facilities_count+10000:
        facilities_url = f'https://data.epa.gov/efservice/FRS_FACILITY_SITE/STD_STATE_CODE/=/{state_code}/rows/{start}:{limit}/JSON'
        resp = urllib3.request("GET", facilities_url)
        facilities_subset = resp.json()
        for facility in facilities_subset:
            facilities.append(facility)
        
        start += limit
        limit += limit

    #report count of records
    print(len(facilities), ' facilities found')
    #report keys
    #for key in facilities[0].keys():
    #    print(key)
    return facilities


def Initial_KG():
    #prefixes: Dict[str, str] = _PREFIX
    kg = Graph()
    #for prefix in prefixes:
    #    kg.bind(prefix, prefixes[prefix])
    kg.bind('fio', fio)
    kg.bind('us_frs', us_frs)
    kg.bind('us_frs_data', us_frs_data)
    kg.bind('naics', naics)
    kg.bind('sic', sic)
    kg.bind('coso', coso)
    kg.bind('geo', geo)
    kg.bind('kwgr', kwgr)
    kg.bind('kwg-ont', kwg_ont)
    return kg

def get_point(registry_id):
    url = f'https://data.epa.gov/efservice/GEO_FACILITY_POINT/REGISTRY_ID/=/{registry_id}/JSON'
    resp = urllib3.request("GET", url)
    if int(resp.status) == 200:
        facility_point = resp.json()
    else:
        print('server error on location')
        facility_point = []
    return facility_point


def get_attributes(row):
    #this is specific to the imported file
    facility = {
        'facility_id': row['registry_id'],
        'facility_name': row['std_name'], # 'primary_name' 


    }
     ## additional attributes that do not appear for all facilities
    facility_pt = get_point(row['registry_id'])
    #geometry
    #print(facility_pt)
    try:
        if 'latitude83' in facility_pt[0].keys():
            shape_pt = Point(facility_pt[0]['longitude83'], facility_pt[0]['latitude83'])
            #print(shape_pt)
            facility['WKT'] = shape_pt.wkt
            #print(facility['facility_id'], facility['WKT'])
    except:
        pass
        #print(facility['facility_id'], facility_pt)


    if 'FIPS_CODE' in row.keys():
        facility['county_fips']= row['fips_code']

    #identify federal facilities
    if row['federal_facility_code'] == 'Yes':
        facility['federal_bool'] = True
        if 'federal_agency_name' in row.keys():
            facility['federalAgencyCode'] = row['federal_agency_name']
    else:
        facility['federal_bool'] = False

    if 'tribal_land_code' in row.keys():
        facility['tribal_bool'] = True  # row.TRIBAL_LAND_NAME (rarely filled in)
    if 'site_type_name' in row.keys():
        facility['siteType'] = str(row['site_type_name']).title().replace(" ", "")

    return facility

def get_iris(facility):
    #build iris for any entities
    facility_iri = us_frs_data['d.FRS-Facility.'+str(facility['facility_id'])]

    geo_iri = us_frs_data['d.FRS-Facility-Geometry.'+str(facility['facility_id'])]
    extra_iris ={}

    if 'county_fips' in facility.keys():
        extra_iris['county_iri'] = kwgr['administrativeRegion.USA.' + str(facility['county_fips'])]  # namespace needs to be replaced
        #TODO add uri for the state and triplify the state to sfWithin
    #TODO agency codes need labels  FRS_PROGRAM_FACILITY.FEDERAL_AGENCY_CODE
    if 'federalAgencyCode' in facility.keys():
        agency_iri = fio['d.Agency.'+str(facility['federalAgencyCode'])]
        extra_iris['agency'] = agency_iri
    
    #siteType to class
    if 'siteType' in facility.keys():
        if facility['siteType'] != 'Facility':
            extra_iris['type'] = us_frs[facility['siteType']+'-Facility']



    return facility_iri, geo_iri, extra_iris


def triplify(facilities):
    kg = Initial_KG()
    if state=='ME':
        kg_agency = Initial_KG()
    for row in facilities:
        #get attributes
        facility = get_attributes(row)
        #get iris
        facility_iri, geo_iri, extra_iris = get_iris(facility)

        #create facility
        kg.add((facility_iri, RDF.type, us_frs["FRS-Facility"]))
        kg.add((facility_iri, RDFS.label, Literal(facility['facility_name'], datatype= XSD.string)))
        kg.add((facility_iri, us_frs['hasFRSId'], Literal(facility['facility_id'], datatype=XSD.string)))

        #geometry
        if 'WKT' in facility:
            kg.add((facility_iri, geo['hasGeometry'], geo_iri))
            kg.add((geo_iri, geo["asWKT"], Literal(facility['WKT'], datatype=geo["wktLiteral"])))
        if 'county_fips' in facility.keys():
            kg.add((facility_iri, kwg_ont['sfWithin'], extra_iris['county_iri'])) 
        if 'tribal_bool' in facility.keys():
            #kg.add((facility_iri, coso['locatedIn'], ))
            pass
        #TODO huc code
        

        #federal
        if facility['federal_bool'] == True :
            kg.add((facility_iri, RDF.type, us_frs['Federal-Facility']))
            if 'agency' in extra_iris.keys():
                kg.add((facility_iri, fio['ofAgency'], extra_iris['agency']))
        #siteType
        if 'type' in extra_iris.keys():
            kg.add((facility_iri, RDF.type, extra_iris['type']))

        if state=='ME' and 'federalAgencyCode' in facility.keys():
            kg_agency.add((extra_iris['agency'], RDF.type, fio['Agency']))
            kg_agency.add((extra_iris['agency'], RDFS.label, Literal(facility['federalAgency'], datatype=XSD.string)))

    if state=='ME':
        kg_turtle_file = "us-frs-agency-codes-"+ state+".ttl".format(output_dir)
        kg_agency.serialize(kg_turtle_file, format='turtle')

    return kg

## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True
    
def main():
    '''main function initializes all other functions'''
    df = load_data()
    kg = triplify(df)

    kg_turtle_file = "us-frs-data-facility-site-"+ state+".ttl".format(output_dir)
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger('Finished triplifying pfas analytics tool facilities.')


if __name__ == "__main__":
    main()