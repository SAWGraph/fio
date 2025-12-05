import os
from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS, GEO, DCTERMS
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
#print('root folder: ', root_folder)
data_dir =  root_folder / "data/naics/"
metadata_dir = None
output_dir = root_folder / "datasets/federal/naics/"

##namespaces
epa_frs = Namespace(f"http://w3id.org/fio/v1/epa-frs#")
epa_frs_data = Namespace(f"http://w3id.org/fio/v1/epa-frs-data#")
fio = Namespace(f"http://w3id.org/fio/v1/fio#")
naics = Namespace(f"http://w3id.org/fio/v1/naics#")
sic = Namespace(f"http://w3id.org/fio/v1/sic#")
coso = Namespace(f'http://w3id.org/coso/v1/contaminoso#')

## initiate log file
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.info("Running triplification for naics")


def main():
    '''main function initializes all other functions'''
    df = load_data()
    kg = triplify(df)

    kg_turtle_file = "naics-2022.ttl".format(output_dir)
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger('Finished triplifying naics schema.')


def load_data():
    # df = pd.read_csv(data_dir / "industrysectors_ME.csv")
    df = pd.read_excel(data_dir / 'NAICS_2-6 digit_2022_Codes.xlsx')
    df2 = pd.read_excel(data_dir / '2022_NAICS_Structure.xlsx')
    df2.index = df2['2022 NAICS Code']
    print(df.info())
    print(df2.info())
    df = df.join(df2, on='2022 NAICS US   Code', how='left')
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
    kg.bind('epa_frs', epa_frs)
    kg.bind('epa_frs_data', epa_frs_data)
    kg.bind('naics', naics)
    kg.bind('sic', sic)
    kg.bind('coso', coso)
    return kg


def get_attributes(row):
    # this is specific to the imported file
    #if '-' in str(row['2022 NAICS US   Code']):
    #    print(row['2022 NAICS US   Code'], row['2022 NAICS US Title'])

    industry = {
        'code': row['2022 NAICS US   Code'],
        'name': row['2022 NAICS US Title'],
        'length': len(str(row['2022 NAICS US   Code'])),
        'year': 2022,
        'change': row['Change Indicator']
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

    return industry


def get_iris(industry):
    extra_iris = {}
    # build iris for any entities
    if industry['class']: #make sure its a valid row
        industry_iri = naics['NAICS-'+str(industry['code'])]
        extra_iris['class'] = naics[industry['class']]
    #build iris for parent class
    if 'sector' in industry.keys():
        extra_iris['sector'] = naics['NAICS-'+ str(industry['sector'])]
    if 'subsector' in industry.keys():
        extra_iris['subsector'] = naics['NAICS-'+ str(industry['subsector'])]
    if 'group' in industry.keys():
        extra_iris['group'] = naics['NAICS-'+ str(industry['group'])]

    extra_iris['class'] = naics[industry['class']]

    return industry_iri, extra_iris


def triplify(df):
    kg = Initial_KG()
    for idx, row in df.iterrows():
        # get attributes
        industry = get_attributes(row)
        if pd.isna(industry['code']):
            #print(idx, row) #skip and report any blank rows
            #continue
            pass
        # get iris
        industry_iri, extra_iris = get_iris(industry)

        # create industries (instances)
        kg.add((industry_iri, RDF.type, extra_iris['class'])) #make it an instance of the specific type
        kg.add((industry_iri, RDF.type, OWL.NamedIndividual))
        kg.add((industry_iri, DCTERMS.identifier, Literal(industry['code'], datatype=XSD.string)))
        kg.add((industry_iri, RDFS.label, Literal(industry['name'], datatype=XSD.string)))
        kg.add((industry_iri, fio['ofYear'], Literal(industry['year'], datatype=XSD.gYear)))#year of code

        #determine deprication and 2017 mapping
        '''Note for Indicator field:     * = title change, no content change
                                    ** = new code for 2022 NAICS
                                  *** = re-used code, content change (with or without title change)
                                **** = re-used code, content change at lower level with insignificant
                                           impact at this level (with or without title change)
        '''
        if industry['change'] in ['','*',"****"] or pd.isna(industry['change']):
            #print(industry_iri, 'no change')
            kg.add((industry_iri, fio['ofYear'], Literal('2017', datatype=XSD.gYear)))
        if industry['change'] in ['***']:
            #print(industry_iri+'-2017', 'changed')
            kg.add((industry_iri+'-2017', RDF.type, extra_iris['class']))
            kg.add((industry_iri, DCTERMS.identifier, Literal(industry['code'], datatype=XSD.string)))
            kg.add((industry_iri+'-2017', fio['ofYear'], Literal('2017', datatype=XSD.gYear)))#year of code
            kg.add((industry_iri+'-2017', fio['yearDeprecated'], Literal('2017', datatype=XSD.gYear)))#year of code
        
        #same as 5 digit code if last digit is 0
        if industry['class']== 'NAICS-IndustryCode' and len(str(industry['code'])) == 6:
            if str(industry['code'])[5:6] == '0':
                #print(industry_iri, 'sameAs', str(industry['code'])[0:5])
                kg.add((industry_iri, OWL.sameAs, naics['NAICS-'+str(industry['code'])[0:5]]))
            else:
                #add an extra link between 5 and 6 digit codes
                #print(industry_iri,str(industry['code'])[0:5])
                kg.add((industry_iri, fio['subcodeOf'], naics['NAICS-'+str(industry['code'])[0:5]]))

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
    kg.add((naics['NAICS-32'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-32'], RDFS.label, Literal('Manufacturing', datatype=XSD.string)))
    kg.add((naics['NAICS-32'], OWL.sameAs, naics['NAICS-31']))


    kg.add((naics['NAICS-33'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-33'], RDFS.label, Literal('Manufacturing', datatype=XSD.string)))
    kg.add((naics['NAICS-33'], OWL.sameAs, naics['NAICS-31']))


    kg.add((naics['NAICS-45'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-45'], RDFS.label, Literal('Retail Trade', datatype=XSD.string)))
    kg.add((naics['NAICS-45'], OWL.sameAs, naics['NAICS-44']))

    kg.add((naics['NAICS-49'], RDF.type, naics['NAICS-IndustrySector']))
    kg.add((naics['NAICS-49'], RDFS.label, Literal('Transportation and Warehousing', datatype=XSD.string)))
    kg.add((naics['NAICS-49'], OWL.sameAs, naics['NAICS-48']))


    return kg


## utility functions

def is_valid(value):
    if math.isnan(float(value)):
        return False
    else:
        return True


if __name__ == "__main__":
    main()