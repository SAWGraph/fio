"""Shared helpers for the FRS triplification scripts: setup, API access, IRI cleaning and common triples."""
import json
import logging
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd
import urllib3
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, PROV, XSD

## paths
FRS_DIR = Path(__file__).resolve().parent                  # datasets/federal/us-frs
DATASETS_DIR = FRS_DIR.parent.parent                       # datasets
OUTPUT_DIR = FRS_DIR / "triples"
LOG_NAME = "log"

## namespaces
epa_frs = Namespace("http://w3id.org/fio/v1/epa-frs#")
epa_frs_data = Namespace("http://w3id.org/fio/v1/epa-frs-data#")
fio = Namespace("http://w3id.org/fio/v1/fio#")
naics = Namespace("http://w3id.org/fio/v1/naics#")
sic = Namespace("http://w3id.org/fio/v1/sic#")
kwgr = Namespace("http://stko-kwg.geog.ucsb.edu/lod/resource/")
kwg_ont = Namespace("http://stko-kwg.geog.ucsb.edu/lod/ontology/")
coso = Namespace("http://w3id.org/coso/v1/contaminoso#")
schema = Namespace("http://schema.org/")


## setup
def setup_logging(logname=LOG_NAME):
    '''Log to a file (appending), keeping urllib3 quiet except for retries and failures'''
    logging.basicConfig(filename=logname,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_state(prompt="state abbreviation?"):
    '''State abbreviation from the command line (python script.py ME), otherwise ask for it'''
    if len(sys.argv) > 1:
        return sys.argv[1].strip().upper()
    return input(prompt)


def new_graph():
    '''An empty graph with the prefixes used by the FRS datasets'''
    kg = Graph()
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


## API access
def get_json(url, timeout=100, retries=5, wait=10):
    """GET url and return the parsed JSON.

    The Envirofacts service sometimes answers with an empty body or an HTML error page (timeouts, 5xx,
    rate limiting). Retry those with a growing pause, and raise if every attempt fails so that a state is
    never written from a partial download.
    """
    last_problem = None
    for attempt in range(1, retries + 1):
        try:
            resp = urllib3.request("GET", url, timeout=timeout)
            if resp.status == 200:
                return resp.json()
            last_problem = f"HTTP {resp.status}: {resp.data[:200]!r}"
        except (urllib3.exceptions.HTTPError, json.JSONDecodeError) as e:
            last_problem = f"{type(e).__name__}: {e}"
        logging.warning(f"Attempt {attempt}/{retries} failed for {url} ({last_problem})")
        print(f"attempt {attempt}/{retries} failed ({last_problem})")
        if attempt < retries:
            time.sleep(wait * attempt)
    logging.error(f"Giving up on {url} after {retries} attempts ({last_problem})")
    raise RuntimeError(f"Could not get valid JSON from {url} after {retries} attempts: {last_problem}")


def fetch_all(url_template, timeout=30, page_size=10000, total=None, test_size=None, verbose=False):
    '''Get every row of a paged Envirofacts query as a list of dictionaries.

    url_template holds {start} and {limit}. The API's row range is 1-based and includes both ends, so pages
    run 1:10000, 10001:20000 and so on. Stops at an empty page or a server error, after `total` rows if given,
    or after one page of test_size rows when testing.'''
    rows = []
    if test_size:
        page_size = test_size
    start = 1
    while total is None or start <= total:
        limit = start - 1 + page_size
        url = url_template.format(start=start, limit=limit)
        print(url)
        page = get_json(url, timeout=timeout)
        if page == []:
            break  # no results left
        if verbose:
            print(page[0])
        if 'error' in page[0].keys():
            print(page[0]['error'])  # stop if an error is returned from the server
            logging.error(f"Server returned an error for {url}: {page[0]['error']}")
            break
        rows.extend(page)
        print(f'retrieved to {limit}')
        start += page_size
        if test_size:
            break
    print(len(rows), ' facilities found')
    return rows


## IRI cleaning
# the replacements the program/record scripts apply to identifiers
IRI_REPLACEMENTS = str.maketrans({"(": "-",
                                  ")": "",
                                  "&": "",
                                  "/": "-",
                                  ",": "",
                                  ":": "-",
                                  ";": "-",
                                  " ": "",
                                  "#": "-",
                                  "�": "",
                                  "+": "p",
                                  "]": "",
                                  "{": "",
                                  "\\": "_",
                                  "`": ""})

# characters a Turtle IRI cannot contain, in addition to whitespace and control characters
_IRI_FORBIDDEN = set('<>"{}|^`\\')

# distinct raw values that had to be cleaned since the last summary: raw -> cleaned
_iri_changed = {}


def _sanitize(text):
    '''Replace whitespace, control/format/private-use characters and characters forbidden in an IRI with _'''
    return ''.join('_' if (unicodedata.category(c)[0] in 'CZ' or c in _IRI_FORBIDDEN) else c for c in text)


def clean_iri_part(value):
    '''Make an identifier safe to use inside an IRI. None/NaN are returned unchanged.

    The data sometimes has stray line breaks, tabs or control characters inside identifiers (e.g. a tab in
    'KY00000<tab>2108900005'). Leading and trailing whitespace is removed, the usual replacements are applied,
    and anything else that cannot appear in an IRI becomes an underscore.'''
    if value is None or value != value:
        return value
    raw = str(value)
    text = raw.strip().translate(IRI_REPLACEMENTS)
    cleaned = _sanitize(text)
    if cleaned != text or raw.strip() != raw:
        _iri_changed[raw] = cleaned
    return cleaned


def safe_local(local_name):
    '''Final guard for a complete IRI local name: nothing invalid gets into the graph even if a piece was not cleaned.'''
    cleaned = _sanitize(local_name)
    if cleaned != local_name:
        _iri_changed[local_name] = cleaned
    return cleaned


def report_cleaned(max_examples=20):
    '''Print and log a one-line summary of the values cleaned so far, with examples in the log, then reset.'''
    if not _iri_changed:
        return
    summary = f'cleaned {len(_iri_changed)} distinct values with characters that are invalid in an IRI: {_iri_changed}'
    print(summary)
    logging.warning(summary)
    for raw, cleaned in list(_iri_changed.items())[:max_examples]:
        logging.warning(f'  IRI value {raw!r} -> {cleaned!r}')
    _iri_changed.clear()


## shared triples
INTEREST_ACRONYMS = ['NSR', 'NPDES', 'ICIS', 'OSHA', 'ICIS-', 'CESQG', 'SQG', 'AFO', 'SW', 'BRAC', 'CZM', 'EPCRA', 'FRP',
                     'LQG', "II", "WIPP", 'NPL', 'TRI', 'TSCA', 'TSD', "UIC", 'VSQG', 'NESHAPS', 'SPCC']


def format_interest_type(value):
    '''Environmental interest type description to a CamelCase IRI part, keeping program acronyms upper case'''
    if pd.isna(value):
        return None
    cleaned = clean_iri_part(value)
    if cleaned is None:
        return None
    return ''.join(word if word in INTEREST_ACRONYMS else word.title() for word in cleaned.split())


def add_record_dates(kg, iri, facility):
    '''Add the start, end, created and modified times of a program record.

    A start date qualified as CLS is the date the facility closed, so it also ends the record.'''
    def stamp(value):
        return Literal(value.strftime('%Y-%m-%dT%H:%M:%S'), datatype=XSD.dateTime)

    if pd.notnull(facility.start_date):
        kg.add((iri, PROV.startedAtTime, stamp(facility['start_date'])))
        if facility.start_date_qualifier == 'CLS':
            kg.add((iri, PROV.endedAtTime, stamp(facility['start_date'])))
    if pd.notnull(facility.end_date):
        kg.add((iri, PROV.endedAtTime, stamp(facility['end_date'])))
    if pd.notnull(facility.create_date):
        kg.add((iri, DCTERMS.created, stamp(facility['create_date'])))
    if pd.notnull(facility.update_date):
        kg.add((iri, DCTERMS.modified, stamp(facility['update_date'])))
