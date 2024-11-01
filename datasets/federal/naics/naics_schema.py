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

## data path
root_folder =Path(__file__).resolve().parent.parent.parent
print('root folder: ', root_folder)
data_dir =  root_folder / "data/naics/"
metadata_dir = None
output_dir = root_folder / "datasets/federal/naics/"

##namespaces
us_frs = Namespace(f"http://sawgraph.spatialai.org/v1/us-frs#")
us_frs_data = Namespace(f"http://sawgraph.spatialai.org/v1/us-frs-data#")
fio = Namespace(f"http://sawgraph.spatialai.org/v1/fio#")
naics = Namespace(f"http://sawgraph.spatialai.org/v1/fio/naics#")
sic = Namespace(f"http://sawgraph.spatialai.org/v1/fio/sic#")
coso = Namespace(f'http://sawgraph.spatialai.org/v1/contaminoso#')
geo = Namespace(f'http://www.opengis.net/ont/geosparql#')
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

    kg_turtle_file = "naics-schema.ttl".format(output_dir)
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger('Finished triplifying naics schema.')


def load_data():
    # df = pd.read_csv(data_dir / "industrysectors_ME.csv")
    df = pd.read_excel(data_dir / 'NAICS_2-6 digit_2022_Codes.xlsx')
    print(df.info())
    logger = logging.getLogger('Data loaded to dataframe.')
    # print(df)
    return df


def Initial_KG():
    # prefixes: Dict[str, str] = _PREFIX
    kg = Graph()
    # for prefix in prefixes:
    #    kg.bind(prefix, prefixes[prefix])
    kg.bind('fio', fio)
    kg.bind('us_frs', us_frs)
    kg.bind('us_frs_data', us_frs_data)
    kg.bind('naics', naics)
    kg.bind('sic', sic)
    kg.bind('coso', coso)
    kg.bind('geo', geo)
    return kg


def get_attributes(row):
    # this is specific to the imported file
    #if '-' in str(row['2022 NAICS US   Code']):
    #    print(row['2022 NAICS US   Code'], row['2022 NAICS US Title'])

    industry = {
        'code': row['2022 NAICS US   Code'],
        'name': row['2022 NAICS US Title'],
        'length': len(str(row['2022 NAICS US   Code'])),
        'year': 2022
    }
    #determine which class and parent class based on length
    if industry['length']<=2:
        industry['class'] = 'NAICS-IndustrySector'
    elif industry['length']== 3:
        industry['class'] = 'NAICS-IndustrySubsector'
        industry['sector'] = str(industry['code'])[:2]
    elif industry['length']==4:
        industry['class'] = 'NAICS-IndustryGroup'
        industry['subsector'] = str(industry['code'])[:3]
    elif industry['length'] in {5,6}:
        if industry['code'] not in {'31-33', '44-45', "48-49"}:
            industry['class'] = 'NAICS-IndustryCode'
            industry['group'] = str(industry['code'])[:4]
        else: #deal with sectors with multiple codes
            industry['class'] = 'NAICS-IndustrySector'
            industry['code'] = industry['code'][:2] #only take the first two digits (31, 44, or 48), the rest are manually added below
            #print(industry['code'], industry['name'])

    return industry


def get_iris(industry):
    extra_iris = {}
    # build iris for any entities
    if industry['class']: #make sure its a valid row
        industry_iri = naics[industry['class']+'-'+str(industry['code'])]
        extra_iris['class'] = naics[industry['class']]
    #build iris for parent class
    if 'sector' in industry.keys():
        extra_iris['sector'] = naics['NAICS-IndustrySector-'+ str(industry['sector'])]
    if 'subsector' in industry.keys():
        extra_iris['subsector'] = naics['NAICS-IndustrySubsector-'+ str(industry['subsector'])]
    if 'group' in industry.keys():
        extra_iris['group'] = naics['NAICS-IndustryGroup-'+ str(industry['group'])]

    extra_iris['class'] = naics[industry['class']]

    return industry_iri, extra_iris


def triplify(df):
    kg = Initial_KG()
    for idx, row in df.iterrows():
        # get attributes
        industry = get_attributes(row)
        if pd.isna(industry['code']):
            print(idx) #skip and report any blank rows
            continue
        # get iris
        industry_iri, extra_iris = get_iris(industry)

        # create industries (instances)
        kg.add((industry_iri, RDF.type, extra_iris['class'])) #make it an instance of the specific type
        kg.add((industry_iri, RDF.type, OWL.NamedIndividual))
        kg.add((industry_iri, RDFS.label, Literal(industry['name'], datatype=XSD.string)))
        kg.add((industry_iri, fio['ofYear'], Literal(industry['year'], datatype=XSD.gYear)))#year of code
        
        #same as 5 digit code if last digit is 0
        if industry['class']== 'NAICS-IndustryCode' and len(str(industry['code'])) == 6:
            if str(industry['code'])[5:6] == '0':
                #print(industry_iri, 'sameAs', str(industry['code'])[0:5])
                kg.add((industry_iri, OWL.sameAs, naics['NAICS-IndustryCode-'+str(industry['code'])[0:5]]))

        #link subcodes to parents
        if 'sector' in extra_iris.keys():
            kg.add((industry_iri, fio['subcodeOf'], extra_iris['sector']))

        elif 'subsector' in extra_iris.keys():
            kg.add((industry_iri, fio['subcodeOf'], extra_iris['subsector']))
           
        elif 'group' in extra_iris.keys():
            kg.add((industry_iri, fio['subcodeOf'], extra_iris['group']))
           
        else: #sector codes with no parent
            pass

    ##manual additions for industry with multiple sector codes
    kg.add((naics['NAICS-IndustrySector-32'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-IndustrySector-32'], RDFS.label, Literal('Manufacturing', datatype=XSD.string)))
    kg.add((naics['NAICS-IndustrySector-32'], OWL.sameAs, naics['NAICS-IndustrySector-31']))


    kg.add((naics['NAICS-IndustrySector-33'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-IndustrySector-33'], RDFS.label, Literal('Manufacturing', datatype=XSD.string)))
    kg.add((naics['NAICS-IndustrySector-33'], OWL.sameAs, naics['NAICS-IndustrySector-31']))


    kg.add((naics['NAICS-IndustrySector-45'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-IndustrySector-45'], RDFS.label, Literal('Retail Trade', datatype=XSD.string)))
    kg.add((naics['NAICS-IndustrySector-45'], OWL.sameAs, naics['NAICS-IndustrySector-44']))

    kg.add((naics['NAICS-IndustrySector-49'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-IndustrySector-49'], RDFS.label, Literal('Transportation and Warehousing', datatype=XSD.string)))
    kg.add((naics['NAICS-IndustrySector-49'], OWL.sameAs, naics['NAICS-IndustrySector-48']))


    return kg


## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True


if __name__ == "__main__":
    main()