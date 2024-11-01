import os
from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
import pandas as pd
import geopandas as gpd
import json
import encodings
import logging
import csv
from datetime import datetime
import sys
import math
import numpy as np
from datetime import date
from pyutil import *
from pathlib import Path
from shapely.geometry import Point

code_dir = Path(__file__).resolve().parent.parent
#print(code_dir)
#sys.path.insert(0, str(code_dir))
#from variable import NAME_SPACE, _PREFIX

## declare variables
logname = "log"
state = 'IL'

## data path
root_folder =Path(__file__).resolve().parent.parent.parent
data_dir = root_folder / "data/frs_echo/"
metadata_dir = None
output_dir = root_folder / "federal/us-frs"

##namespaces
us_frs = Namespace(f"http://sawgraph.spatialai.org/v1/us-frs#")
us_frs_data = Namespace(f"http://sawgraph.spatialai.org/v1/us-frs-data#")
fio = Namespace(f"http://sawgraph.spatialai.org/v1/fio#")
naics = Namespace(f"http://sawgraph.spatialai.org/v1/fio/naics#")
sic = Namespace(f"http://sawgraph.spatialai.org/v1/fio/sic#")
coso = Namespace(f'http://sawgraph.spatialai.org/v1/contaminoso#')

## initiate log file
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.info("Running triplification for facilities")

def main():
    '''main function initializes all other functions'''
    naics_df, sic_df = load_data()
    kg = triplify(naics_df)
    kg2 = triplify(sic_df)

    kg_turtle_file = "us-frs-industry-naics-echo-"+state+".ttl".format(output_dir)
    kg_turtle_file2 = "us-frs-industry-sic-echo-"+state+".ttl".format(output_dir)
    kg.serialize(kg_turtle_file, format='turtle')
    kg2.serialize(kg_turtle_file2, format='turtle')
    logger = logging.getLogger('Finished triplifying pfas analytics tool facility industries.')

def load_data():
    #df = pd.read_csv(data_dir / "industrysectors_ME.csv")
    naics_df = pd.read_csv(data_dir / str('state_combined_'+state.lower()) / str(state+'_NAICS_FILE.CSV'), low_memory=False, dtype=str) #make sure to import as string and not drop leading 0 in codes
    sic_df = pd.read_csv(data_dir / str('state_combined_'+state.lower()) / str(state+'_SIC_FILE.csv'), low_memory=False, dtype=str)
    logger = logging.getLogger('Data loaded to dataframe.')
    print(naics_df.info())
    print(sic_df.info())
    return naics_df, sic_df


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
    return kg


def get_attributes(row):
    #this is specific to the imported file
    facility = {
        'facility_id': row.REGISTRY_ID,
        'program': str(row.PGM_SYS_ACRNM).lower().replace('/','-'),
        'primary': row.PRIMARY_INDICATOR

    }
    ## additional attributes that do not appear for all facilities
    if 'NAICS_CODE' in row.keys():
        facility['naics_code'] = str(row.NAICS_CODE)
    elif 'SIC_CODE' in row.keys():
        facility['sic_code'] = str(row.SIC_CODE)

    return facility

def get_iris(facility):
    #build iris for any entities
    facility_iri = us_frs_data['d.FRS-Facility.'+str(facility['facility_id'])]

    #industry iri
    if 'naics_code' in facility.keys():
        if len(facility['naics_code'])>4:
            industry_iri = naics['NAICS-IndustryCode-'+str(facility['naics_code'])]
        elif len(facility['naics_code'])==4:
            industry_iri = naics['NAICS-IndustryGroup-' + str(facility['naics_code'])]
        elif len(facility['naics_code']) == 3:
            industry_iri = naics['NAICS-IndustrySubsector-' + str(facility['naics_code'])]
        elif len(facility['naics_code']) in {1,2}:
            industry_iri = naics['NAICS-IndustrySector-' + str(facility['naics_code'])]
    elif 'sic_code' in facility.keys():
        if len(facility['sic_code']) == 4:
            industry_iri = sic['SIC-IndustryCode-' + str(facility['sic_code'])]
    else:
        print('error on: ', facility['facility_id'], facility['sic_code'])
        industry_iri = False

    extra_iris = {}

    #primary predicate
    if 'primary' in facility.keys():
        if facility['primary'] == 'PRIMARY':
            extra_iris['primary'] = us_frs['primaryIndustry']
        elif facility['primary'] == 'SECONDARY':
            extra_iris['primary'] = us_frs['secondaryIndustry']

    #industry predicate
    industry_predicate = us_frs[facility['program']+'-Industry']

    return facility_iri, industry_iri, industry_predicate, extra_iris

def triplify(df):
    kg = Initial_KG()
    for idx, row in df.iterrows():
        #get attributes
        facility = get_attributes(row)
        #get iris
        facility_iri, industry_iri, industry_predicate, extra_iris = get_iris(facility)

        #create facility
        if industry_iri:
            kg.add((facility_iri, industry_predicate, industry_iri))

        if 'primary' in extra_iris.keys():
            kg.add((facility_iri, extra_iris['primary'], industry_iri))

    return kg

## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True


if __name__ == "__main__":
    main()