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
state= "OH"

## data path
root_folder =Path(__file__).resolve().parent.parent.parent
data_dir = root_folder / "data/frs_echo/"
metadata_dir = None
output_dir = root_folder / "federal/us-frs/"

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
    df = load_data()
    kg = triplify(df)


    kg_turtle_file = "us-frs-environmentalInterest-echo_"+state +".ttl".format(output_dir)
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger('Finished triplifying pfas analytics tool facility industries.')

def load_data():
    #df = pd.read_csv(data_dir / "industrysectors_ME.csv")
    df = pd.read_csv(data_dir / str('state_combined_'+ state.lower()) / str(state + '_NAICS_FILE.CSV'), low_memory=False, dtype=str)
    logger = logging.getLogger('Data loaded to dataframe.')
    print(df.info())

    return df


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
        'interest':row.INTEREST_TYPE,
        'program':str(row.PGM_SYS_ACRNM).replace('/', '').replace('-', ''),  #remove slashes and hyphens
        'program_id':row.PGM_SYS_ID

    }
    ## additional attributes that do not appear for all facilities

    return facility

def get_iris(facility):
    #build iris for any entities
    facility_iri = us_frs_data['d.FRS-Facility.'+str(facility['facility_id'])]


    return facility_iri

def triplify(df):
    kg = Initial_KG()
    for idx, row in df.iterrows():
        #get attributes
        facility = get_attributes(row)
        #get iris
        facility_iri = get_iris(facility)

        #create facility
        kg.add((facility_iri, us_frs['environmentalInterestType'], Literal(facility['interest'], datatype=XSD.string)))
        kg.add((facility_iri, us_frs['has'+facility['program']+'Id'], Literal(facility['program_id'], datatype=XSD.string)))

    return kg

## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True


if __name__ == "__main__":
    main()