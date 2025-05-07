import os
from typing import Dict
from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
import pandas as pd
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

code_dir = Path(__file__).resolve().parent.parent
#print(code_dir)
sys.path.insert(0, str(code_dir))
#from variable import NAME_SPACE, _PREFIX

## declare variables
logname = "log"
state = ' ME'

## data path
root_folder =Path(__file__).resolve().parent.parent.parent
data_dir = root_folder / "data/epa_pfas_analytic_tool/"
metadata_dir = None
output_dir = root_folder / "federal/us-frs"


epa_frs = Namespace(f"http://w3id.org/fio/v1/epa-frs#")
epa_frs_data = Namespace(f"http://w3id.org/fio/v1/epa-frs-data#")
fio = Namespace(f"http://w3id.org/fio/v1/fio#")
naics = Namespace(f"http://w3id.org/fio/v1/naics#")
sic = Namespace(f"http://w3id.org/fio/v1/sic#")

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
    kg = triplify(df, _PREFIX)

    kg_turtle_file = f"us-frs-data-pat-{state.strip()}.ttl".format(output_dir)
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger(f'Finished triplifying pfas analytics tool facilities - {state}.')

def load_data():
    #df = pd.read_csv(data_dir / f"industrysectors_{state}.csv")
    df = pd.read_excel(data_dir/ 'industrysectors_275aeff7-cbf1-46c2-92a9-67886bcbc0ee.xlsx')
    #filter to just one state
    df = df[df['State'] == state]
    #df = pd.read_json(data_dir / '')
    #replace - with nan
    df.replace(to_replace='-', value=pd.NA, inplace=True)
    print(df.info(verbose=True))
    logger = logging.getLogger('Data loaded to dataframe.')
    return df


def Initial_KG(_PREFIX: object) -> object:
    prefixes: Dict[str, str] = _PREFIX
    kg = Graph()
    for prefix in prefixes:
        kg.bind(prefix, prefixes[prefix])
    kg.bind('fio', fio)
    kg.bind('epa_frs', epa_frs)
    kg.bind('epa_frs_data', epa_frs_data)
    kg.bind('naics', naics)
    kg.bind('sic', sic)
    return kg

def clean_attributes(df):
    print(df.info())

    return df

def get_attributes(row):

    if pd.notnull(row['ECHO Facility Report']):
        echo_facility = row['ECHO Facility Report']
        echo_url, fac_id = echo_facility.rsplit('=')
    else:
        #airports have no FRS id
        return False
        #TO DO need a better identifier for non FRS facilities
        #fac_id = row['Facility']
        #print('error: ', row['Facility'])

    facility = {
        'facility_name': row['Facility'],
        'status': row['Status'],
        'facility_id': fac_id,
        'latitude': row['Latitude'],
        'longitude': row['Longitude'],
    }

    if pd.notnull(row['AIR_IDS']):
        facility['air_id']= row['AIR_IDS']
    if pd.notnull(row['CAA_PERMIT_TYPES']):
        facility['caa_permit_type']= row['CAA_PERMIT_TYPES']
    if pd.notnull(row['CAA_NAICS']):
        facility['caa_naics']= row['CAA_NAICS']
    if pd.notnull(row['CAA_SICS'] ):
        facility['caa_sics']= row['CAA_SICS']
    if pd.notnull(row['NPDES_IDS']):
        facility['npdes_id']= row['NPDES_IDS']
    if pd.notnull(row['CWA_NAICS']):
        facility['cwa_naics'] = row['CWA_NAICS']
    if pd.notnull(row['CWA_SICS'] ):
        facility['cwa_sic']= row['CWA_SICS']
    if pd.notnull(row['RCRA_IDS']):
        facility['rcra_id']= row['RCRA_IDS']
    if pd.notnull(row['RCRA_NAICS']):
        facility['rcra_naics']= row['RCRA_NAICS']
    if pd.notnull(row['SDWA_IDS']):
        facility['sdwa_id']= row['SDWA_IDS']
    if pd.notnull(row['SDWA_SYSTEM_TYPES'] ):
        facility['sdwa_type']= row['SDWA_SYSTEM_TYPES']
    if pd.notnull(row['TRI_IDS']):
        facility['tri_id']= row['TRI_IDS']

    return facility

def get_iris(facility):
    #remove airports with no frs_id
    if facility != False:
        facility_iri = epa_frs_data['d.'+'FRS-Facility.'+facility['facility_id']]
    else:
        return False
    return facility_iri


def triplify(df, _PREFIX):
    kg = Initial_KG(_PREFIX)

    df = clean_attributes(df)
    for idx, row in df.iterrows():
        facility = get_attributes(row)
        facility_iri = get_iris(facility)
        if facility != False:
            #create facility
            kg.add((facility_iri, RDF.type, epa_frs["FRS-Facility"]))
            kg.add((facility_iri, RDF.type, epa_frs["EPA-PFAS-Facility"]))

    return kg

## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True


if __name__ == "__main__":
    main()