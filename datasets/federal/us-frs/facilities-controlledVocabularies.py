import requests
import json
import urllib3
import geopandas
import pandas as pd
import xml.etree.ElementTree as ET
import math
import datetime
from datetime import date

from rdflib.namespace import OWL, XMLNS, XSD, RDF, RDFS, DCTERMS, GEO
from rdflib import Namespace
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from shapely.geometry import Point
from pathlib import Path

import logging

root_folder =Path(__file__).resolve().parent.parent.parent
metadata_dir = root_folder / "federal/us-frs/metadata/"
output_dir = root_folder / "federal/us-frs/ontology/"
logname = "log"
robust = False

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

replacements = str.maketrans({"(":"- ",
                     ")":"",
                     "&":"",
                     "/":"-",
                     ",":"",
                     ":":"-",
                     " ":"",
                     "#": "-"})

logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.info(f'triplifying controlled vocabulary FRS')


def load_data():
     interest_url = f'https://data.epa.gov/efservice/frs.frs_interest_ref/json'
     print(interest_url)
     resp = urllib3.request("GET", interest_url)
     interests= resp.json()

     print(len(interests), ' Environmental Interest Classes')

     agency_url = f'https://data.epa.gov/efservice/frs.frs_agency_ref/json'
     print(agency_url)
     resp2 = urllib3.request("GET", agency_url)
     agencies = resp2.json()

     print(len(agencies), ' Agencies')

     programs = pd.read_excel(metadata_dir / 'frs_program_abbreviations_and_names.xlsx')
     print(programs.shape[0], ' Programs')

     return interests, agencies, programs


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

    kg.add((epa_frs['controlledVocab'], RDF.type, OWL.Ontology))
    return kg


def clean_attributes(interests):
     interests = pd.DataFrame(interests)
     if robust:
         print(interests.info())


     #interests['interest_short'] = interests['interest_type'].apply(lambda x: (''.join(((f'{word.replace("-", "")}-' if word in ['NSR', 'NPDES', 'ICIS', 'OSHA', 'ICIS-'] else f'{word.title()}') if word in ['NSR', 'NPDES', 'ICIS', 'ICIS-','OSHA', 'MAJOR', 'MINOR', 'GAS', 'AIR', 'GEOTHERMAL', 'PESTICIDES', 'WATER', 'WIND', 'ACTIVITY', 'ASSISTANCE', 'ACTION', 'SURFACE', 'RESIDUAL','RADIOACTIVE'] else word[0]) for word in x.replace("(", "- ").replace("&", "").replace("-", "- ").replace("/", " ").split())) if len(x.split()) > 1 else x)
     interests['interest_short'] = interests['interest_type'].apply(lambda x: (''.join(((word if word in ['NSR', 'NPDES', 'ICIS', 'OSHA', 'ICIS-', 'CESQG', 'SQG', 'AFO','SW', 'BRAC', 'CZM', 'EPCRA', 'FRP', 'LQG', "II", "WIPP", 'NPL', 'TRI', 'TSCA', 'TSD', "UIC", 'VSQG', 'NESHAPS', 'SPCC'] else word.title()) for word in x.translate(replacements).split()))))
     interests['program_short'] = interests['program_category'].apply(lambda x: ''.join((word) for word in str(x).translate(replacements).title().split()))
     #print(interests.interest_short.unique())
     #print(interests.program_short.unique())
     return interests


def clean_agencies(agencies):

    agencies = pd.DataFrame(agencies)
    if robust:
        print(agencies.info())
    agencies = pd.concat([agencies, agencies['federal_agency_name'].str.split(pat=": ", expand=True)],axis=1)
    if robust:
        print(agencies.info())
    #print(agencies[0].unique())
    #print(agencies[1].unique())

    return agencies


def clean_programs(programs):
    programs['PGM_SYS'] = programs['PGM_SYS_ACRNM'].apply(lambda x: x.translate(replacements).upper()) 
    programs = programs[programs['Comments'].isnull()] #only keep programs with no comments (i.e. remove programs that are not public)
    return programs


def get_iris(data):
     iri = {}
     if 'program_category' in data.keys():
        iri['interest'] = epa_frs_data[f"d.EnvironmentalInterestType.{data['interest_short']}"]
        iri['program_cat'] = epa_frs[data['program_short']]
        if data['program_short'] == 'HazardousWasteProgram': #clean up duplicate sub-class
            iri['program_cat'] = epa_frs['HazardousWastePrograms']
     if 'federal_agency_code' in data.keys():
        iri['agency'] = epa_frs_data[f"d.Agency.{data['federal_agency_code']}"]
        iri['class']= epa_frs[f"Agency.{''.join(data[0].split(' '))}"]
     if 'PGM_SYS' in data.keys():
         iri['pgm_sys'] = epa_frs_data[f"d.ProgramInformationSystem.{data['PGM_SYS']}"]  #epa_frs[f"{data['PGM_SYS']}-Facility"]
         #iri['pgm_id_relation'] = epa_frs[f"hasIdentifier.{data['PGM_SYS']}"]
         #iri['pgm_industry_relation'] = epa_frs[f"ofIndustry.{data['PGM_SYS']}"]

     return iri


def triplify(interests, agencies, programs):
    kg = Initial_KG()

    #Reformat the raw data attributes
    interests = clean_attributes(interests)
    agencies = clean_agencies(agencies)
    programs = clean_programs(programs)

    # Triplify Interests
    for idx, interest in interests.iterrows():
         iri = get_iris(interest)
         # interest
         kg.add((iri['interest'], RDF.type, epa_frs['EnvironmentalInterestType'] ))
         kg.add((iri['interest'], RDFS.label, Literal(interest['interest_type'], datatype=XSD.string)))
         # description (interest_desc)
         kg.add((iri['interest'], DCTERMS.description, Literal(interest['interest_desc'], datatype=XSD.string)))
         # program category
         if interest['program_short'] != 'None':
            kg.add((iri['interest'], RDF.type, iri['program_cat']))
            #kg.add((iri['program_cat'], RDFS.subClassOf, epa_frs['ProgramCategory']))
            if interest['program_category'] != 'None':
                kg.add((iri['program_cat'], RDFS.label, Literal(interest['program_category'], datatype=XSD.string)))
                kg.add((iri['program_cat'], RDFS.subClassOf, epa_frs['EnvironmentalInterestType']))
                kg.add((iri['program_cat'], RDF.type, OWL.Class))
            else:
                kg.add((iri['interest'], RDF.type, epa_frs['ProgramCategory']))
            #print(list(kg.triples((iri['program'], DCTERMS.description, None))))
            if interest['program_category_desc'] != 'None' and list(kg.triples((iri['program_cat'], DCTERMS.description, None))) == []: #only program add desc first time
                kg.add((iri['program_cat'], DCTERMS.description, Literal(interest['program_category_desc'], datatype=XSD.string)))
         else:
             kg.add((iri['interest'],RDF.type, epa_frs['EnvironmentalInterestType']))
    #add missing interest
    kg.add((epa_frs_data['d.EnvironmentalInterestType.Potw'], RDF.type, epa_frs['EnvironmentalInterestType']))
    kg.add((epa_frs_data['d.EnvironmentalInterestType.Potw'], RDFS.label,Literal("Publicly Owned Treatment Works", datatype=XSD.string)))
             

    #program category description

    # Triplify Agencies
    for idx, agency in agencies.iterrows():
        iri = get_iris(agency)

        kg.add((iri['agency'], RDF.type, OWL.NamedIndividual))
        
        if pd.notnull(agency[1]) and agency[1] != 'not otherwise classified':
            kg.add((iri['agency'], RDFS.label, Literal(agency[1])))
            kg.add((iri['agency'], RDF.type, iri['class']))
            kg.add((iri['class'], RDF.type, OWL.Class))
            kg.add((iri['class'], RDFS.label, Literal(agency[0])))
            kg.add((iri['class'], RDFS.subClassOf, epa_frs['Agency']))
        else:
            kg.add((iri['agency'], RDFS.label, Literal(agency[0])))
            kg.add((iri['agency'], RDF.type, epa_frs['Agency']))

    # Triplify Programs

    for idx, program in programs.iterrows():
        iri = get_iris(program)
        kg.add((iri['pgm_sys'], RDF.type, epa_frs['ProgramInformationSystem']))
        #kg.add((iri['pgm_sys'], RDFS.subClassOf, epa_frs['FRS-Facility']))
        kg.add((iri['pgm_sys'], RDFS.label, Literal(program['PGM_SYS_NAME'])))
        kg.add((iri['pgm_sys'], DCTERMS.description, Literal(program['PGM_SYS_DESC'])))

        #kg.add((iri['pgm_id_relation'], RDF.type, OWL.DatatypeProperty))
        #kg.add((iri['pgm_id_relation'], RDFS.label, Literal(f"has {program['PGM_SYS_ACRNM']} identifier")))
        #kg.add((iri['pgm_id_relation'], DCTERMS.description, Literal(f"connects a facility to the identifier in {program['PGM_SYS_NAME']}")))
        #kg.add((iri['pgm_id_relation'], RDFS.subPropertyOf, DCTERMS.identifier))
        #kg.add((iri['pgm_id_relation'], RDFS.domain, iri['pgm_sys']))

        #kg.add((iri['pgm_industry_relation'], RDF.type, OWL.ObjectProperty))
        #kg.add((iri['pgm_industry_relation'], RDFS.label, Literal(f"of Industry in {program['PGM_SYS_ACRNM']}")))
        #kg.add((iri['pgm_industry_relation'], DCTERMS.description, Literal(f"connects a facility to an industry in {program['PGM_SYS_NAME']}")))
        #kg.add((iri['pgm_industry_relation'], RDFS.subPropertyOf, fio['ofIndustry']))
        #kg.add((iri['pgm_industry_relation'], RDFS.domain, iri['pgm_sys']))

    return kg

def main():
    '''main function initializes all other functions'''
    interests, agencies, programs = load_data()
    kg = triplify(interests, agencies, programs)
    kg_turtle_file = output_dir / f"epa-frs-controlledVocab.ttl"
    kg.serialize(kg_turtle_file, format='turtle')
    logger = logging.getLogger('Finished triplifying pfas analytics tool facilities.')


if __name__ == "__main__":
    main()