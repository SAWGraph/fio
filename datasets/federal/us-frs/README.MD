# Overview of the raw dataset

* **Name of dataset:** Facility Registry Service
* **Source Agency:** EPA
* **Data source location:** [FRS State Downloads](https://www.epa.gov/frs/epa-state-combined-csv-download-files)
*note: there are many ways to access FRS data, such as via ECHO, state downloads contain industry codes*
* **Additional Data source:** 
    * [Industry Sectors Data](https://echo.epa.gov/trends/pfas-tools#data) *note: this identifies facilities the epa suspects are using pfas*
    * [Additional FRS identifiers](https://frs-public.epa.gov/ords/frs_public2/ez_frs_column.list?table_name=D_EF_FAC.V_PUB_FRS_FACILITY_SITE_GEOPGM)
[program reference](https://usepa.servicenowservices.com/oeca_icis/en/list-of-program-system-acronyms-found-in-icis?id=kb_article_view&sys_kb_id=42327c7f1bfc1954fd044262f54bcb8f)
* **Metadata description:** 
    * [Facility State File Documentation 1132012_new](https://www.epa.gov/frs/epa-state-combined-csv-download-files) (comes with state download)
    * [Environmental Interest Types](https://www.epa.gov/sites/default/files/2020-01/documents/interest_types.pdf)
* **Format of data returned:** csv (also available by REST)
* **Data update interval:**
* **General Comments**:

## Schema Diagram
![US FRS Schema](./FIO%20-%20facility.png)
* [WIP](https://lucid.app/lucidchart/0b649dc4-e466-4d29-ae34-5c0f113f5a46/edit?viewport_loc=-1067%2C1107%2C3523%2C1881%2CcJplkqIup7-.&invitationId=inv_0e3483a0-96fc-4faf-8c17-1a5bf73fd23b)


## Raw Data Attribute List and Mappings with Ontology

FRS State Downloads - 11 csv files per state

### ME_FACILITY_FILE.csv

**CODE**: \us-frs\facilities_echo.py

| Attribute    | Description  | Lift to Graph | Ontology Property    |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|----------------------------------------------|
| FRS_FACILITY_DETAIL_REPORT_URL | report url   |   |    |
| REGISTRY_ID  | registry id to uniquely identify facility  | Yes     | us_frs:FRS-Facility (URI)  us_frs:facilityId |
| PRIMARY_NAME | public or commercial name      | Yes     | us_frs:Facility rdfs:Label   |
| LOCATION_ADDRESS   |  | ? |     |
| SUPPLEMENTAL_LOCATION    | text that provides additional information about a place, including a building name with its secondary unit and number, an industrial park name, an installation name or descriptive text where no formal address is available. | ? |    |
| CITY_NAME    | locality name - nameof city, town village or other locality within whose boundaries (the majority of) the facility site is located.  |   |    |
| COUNTY_NAME  |  | No      |    |
| FIPS_CODE    | county fips code (state and county)  | Yes     | kwg-ont:sfWithin kwg-ont:AdministrativeRegion_2      |
| STATE_CODE   | USPS abbreviation for state    |   |    |
| STATE_NAME   |  |   |    |
| COUNTRY_NAME |  |   |    |
| POSTAL_CODE  | 5 digit zip code and 4 digit extension code (if available)   |   |    |
| FEDERAL_FACILITY_CODE    | Yes/No the facility is property of the Federal Government    | Yes     | rdf:type us_frs:Federal-Facility |
| FEDERAL_AGENCY_NAME      | name of federal agency (derived from FEDERAL_AGENCY_CODE lookup)   | Yes     | fio:ofAgency   |
| TRIBAL_LAND_CODE   | Yes if tribal land |   |    |
| TRIBAL_LAND_NAME   | Name of Tribal Reservation, statistical area, or Public Domain Allotment.      | ?    |  |
| CONGRESSIONAL_DIST_NUM   |  | ?  |    |
| CENSUS_BLOCK_CODE  |  | ?  |    |
| HUC_CODE     | The Hydrologic Unit Code (HUC) that represents a geographic area representing part or all of a surface drainage basin, a combination of drainage basins, or a distinct hydrologic feature. | ?   | kwg-ont:sfWithin     |
| EPA_REGION_CODE    | The code that represents an EPA Region.    | ? |    |
| SITE_TYPE_NAME     | Allowable Values: [ Stationary, Monitoring Site, Brownfields Site, Water System ,  Contamination Addressed,  Contaminated Site,  Potentially Contaminated Site  ]  | Yes     |  added to URI -> rdfs:subClassOf us_frs:FRS-Facility  |
| LOCATION_DESCRIPTION     | Descriptive information about location of facility, including directions.      |   |    |
| CREATE_DATE  | date first posted to database  |   |    |
| UPDATE_DATE  | most recent calendar update    | ? |    |
| US_MEXICO_BORDER_IND     | An indicator that the facility is located within 62.5 miles (100 km) of the United States - Mexico Border. Only applicable to facilities in California, Arizona, New Mexico, and Texas.    |   |    |
| PGM_SYS_ACRNMS     | list of program acronyms the facility is tracked by    | from other tables | |
| LATITUDE83   |  | Yes     |    |
| LONGITUDE83  |  | Yes     |    |
| CONVEYOR     | Identification of the party that transmitted the latitude and longitude  |   |    |
| COLLECT_DESC | Method used to determine Lat/Long    |   |    |
| ACCURACY_VALUE     | Measure of accuracy in meters of latitude/longitude    |   |    |
| REF_POINT_DESC     | Name that identifies the place for which geographic coordinates were established     |   |    |
| HDATUM_DESC  | Horizontal reference datum used in determining latitude longitude coordinates  |   |    |
| SOURCE_DESC  | Name of party responsible for providing lat/long coordinates |   |    |

### ME_NAICS_FILE.csv
many to one relation with facility file

**CODE**: \us-frs\industries-echo.py

| Attribute   | Description    | Lift to Graph | Ontology Property/Class      |
|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|------------------------------------------------------|
| REGISTRY_ID |    | Yes     | us_frs:FRS-Facility    |
| PGM_SYS_ACRNM     | The abbreviated name that represents the name of an information management system for an environmental program.      | Yes     | used of URI predicate  fio:ofIndustry sub properties    |
| PGM_SYS_ID  | The identification number, such as the permit number assigned by an information management system that represents a facility site, waste site, operable unit, or other feature tracked by that Environmental Information System. |   |      |
| INTEREST_TYPE     | The environmental permit or regulatory program that applies to the facility site | ? |      |
| NAICS_CODE  | The code that represents a subdivision of an industry that accommodates user needs in the United States (six-digits).      | Yes     | fio:ofIndustry naics:NAICS-Industry      |
| PRIMARY_INDICATOR | The name that indicates whether the associated NAICS Code represents the primary activity occurring at the facility site   | Yes     | us_frs:primary_industry or us_frs:secondary_industry |
| CODE_DESCRIPTION  | The text that represents a subdivision of an industry that accommodates user needs in the United States  |   |      |

### ME_SIC_FILE.csv

many to one relation with facility file

**CODE**: \us-frs\industries-echo.py

| Attribute   | Description     | Lift to Graph | Ontology Property |
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|-------------------|
| REGISTRY_ID |     |   |
| PGM_SYS_ACRNM     | The abbreviated name that represents the name of an information management system for an environmental program. |   |
| PGM_SYS_ID  | The identification number, such as the permit number, assigned by an information management system that represents a facility site, waste site, operable unit, or other feature tracked by that Environmental Information System. |   |
| INTEREST_TYPE     | The environmental permit or regulatory program that applies to the facility site  |   |
| SIC_CODE    | The code that represents the economic activity of a company (4-digits).     |   |
| PRIMARY_INDICATOR | The name that indicates whether the associated SIC Code represents the primary activity occurring at the facility site      |   |
| CODE_DESCRIPTION  | The text that represents a subdivision of an industry that accommodates user needs in the United States   |   |

### ALTERNATIVE NAME FILE

Not currently triplified

| Attribute | Description | Lift to Graph | Ontology Property |
|-----------------------|-------------|---------------|-------------------|
| REGISTRY_ID     | |   |
| PGM_SYS_ACRNM   | |   |
| PGM_SYS_ID      | |   |
| ALTERNATIVE_NAME      | |   |
| ALTERNATIVE_NAME_TYPE | |   |

### ORGANIZATION FILE

Not currently triplified

Describes organizations affiliated with a facility

| Attribute  | Description  | Lift to Graph | Ontology Property |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|---------------------------------------------------------------|
| "REGISTRY_ID"    |  |   |   |
| "PGM_SYS_ACRNM"  |  |   |   |
| "PGM_SYS_ID"     |  |   |   |
| "INTEREST_TYPE"  |  |   |   |
| "AFFILIATION_TYPE"     | The name that describes the capacity or function that an organization or individual serves for a facility site [Legally Responsible Entity, Legal Operator, Waste Treater, Waste Handler, Land Owner, Parent Corporation, Owner/Operator][ Report Certifier, Regulatory Contact, Public Contact, Technical Contact, Owner, Operator] | Yes     | fio:hasAffiliation, mapped out under us_frs: as subproperties |
| "START_DATE"     |  |   |   |
| "END_DATE" |  |   |   |
| "ORG_NAME" | Yes    | rdfs:label    |   |
| "ORG_TYPE" | Yes    | maps to subclass of Prov:Organization |   |
| "DUNS_NUMBER"    | The Data Universal Numbering System (DUNS) number assigned by Dun and Bradstreet to identify unique business establishments    |   |   |
| "DIVISION_NAME"  |  |   |   |
| "PHONE_NUMBER"   |  |   |   |
| "ALTERNATE_PHONE"      |  |   |   |
| "FAX_NUMBER"     |  |   |   |
| "EMAIL_ADDRESS"  |  |   |   |
| "EIN"      | The unique tax identification number issued by the Internal Revenue Service to the employer.     | ? |   |
| "STATE_BUSINESS_ID"    | The uniform business number assigned to an official business by a state. | ? |   |
| "MAILING_ADDRESS"      |  |   |   |
| "SUPPLEMENTAL_ADDRESS" |  |   |   |
| "CITY_NAME"      |  |   |   |
| "STATE_CODE"     |  |   |   |
| "STATE_NAME"     |  |   |   |
| "POSTAL_CODE"    |  |   |   |
| "COUNTRY_NAME"   |  |   |  |    |

### ME_ENVIRONMENTAL_INTEREST_FILE.csv

Provides identifiers across all EPA agency subprograms and state system identifiers. 

Many to one with facility table. 

**CODE**: \us-frs\environmentalInterest-echo.py

| Attribute      | Description  | Lift to Graph | Ontology Property   |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|---------------------------------|
| REGISTRY_ID    |  |   |   |
| PGM_SYS_ACRNM  | The abbreviated name that represents the name of an information management system for an environmental program. Program System Definitions can be viewed at <http://www.epa.gov/enviro/html/fii/prog_sys.html> |  Yes |   builds predicate for us_frs:has___Id      |
| PGM_SYS_ID     | The identification number, such as the permit number, assigned by an information management system     | Yes     | us_frs:has____Id xsd:string |
| INTEREST_TYPE  | The environmental permit or regulatory program that applies to the facility site     | Yes     | us_frs:environmentalInterestType xsd:string|
| FED_STATE_CODE | A flag which indicates whether the environmental interest data was provided by a federal or state environmental information system.  |   |   |
| START_DATE     | Date the agency became interested in the facility site for a particular environmental interest type    |   |   |
| START_DATE_QUALIFIER | The qualifier that specifies the meaning of the date being used as an approximation for the environmental interest start date. |   |   |
| END_DATE | Date the agency ceased to be interested in the facility site for a particular environmental interest type    |   |   |
| END_DATE_QUALIFIER   | The qualifier that specifies the meaning of the date being used as an approximation for the environmental interest end date.   |   |   |
| SOURCE_OF_DATA | The source of the associated environmental interest data.    |   |   |
| LAST_REPORTED_DATE   | The most recent date the corresponding environmental interest data was reported to the Source of Data. |   |   |
| CREATE_DATE    | A system-generated value that represents the calendar date and time the corresponding information was posted to the database.  |   |   |
| UPDATE_DATE    | A system-generated value that represents the most recent calendar date and time that the corresponding information was updated in the database   |   |   |
| ACTIVE_STATUS  | The status of the environmental interest at the facility or site   |   |   |

### Contact File

Not currently triplified

"REGISTRY_ID"| "PGM_SYS_ACRNM"| "PGM_SYS_ID"| "INTEREST_TYPE"| "AFFILIATION_TYPE"| "START_DATE"| "END_DATE"| "FULL_NAME"| "TITLE"| "PHONE_NUMBER"| "ALTERNATE_PHONE"| "FAX_NUMBER"| "EMAIL_ADDRESS"| "MAILING_ADDRESS"| "SUPPLEMENTAL_ADDRESS"| "CITY_NAME"| "STATE_CODE"| "STATE_NAME"| "POSTAL_CODE"| "COUNTRY_NAME"

### Mailing Address

Not currently triplified

"REGISTRY_ID"| "PGM_SYS_ACRNM"| "PGM_SYS_ID"| "INTEREST_TYPE"| "AFFILIATION_TYPE"| "START_DATE"| "END_DATE"| "MAILING_ADDRESS"| "SUPPLEMENTAL_ADDRESS"| "CITY_NAME"| "STATE_CODE"| "STATE_NAME"| "POSTAL_CODE"| "COUNTRY_NAME"

### Program File

Not currently triplified

"PGM_SYS_ACRNM"| "PGM_SYS_ID"| "REGISTRY_ID"| "PRIMARY_NAME"| "LOCATION_ADDRESS"| "SUPPLEMENTAL_LOCATION"| "CITY_NAME"| "COUNTY_NAME"| "FIPS_CODE"| "STATE_CODE"| "STATE_NAME"| "COUNTRY_NAME"| "POSTAL_CODE"| "FEDERAL_FACILITY_CODE"| "FEDERAL_AGENCY_CODE"| "TRIBAL_LAND_CODE"| "TRIBAL_LAND_NAME"| "LEGISLATIVE_DIST_NUM"| "HUC_CODE_8"| "HUC_CODE_12"| "EPA_REGION_CODE"| "SITE_TYPE_NAME"| "DATA_QUALITY_CODE"| "LAST_REPORTED_DATE"| "STD_NAME"| "STD_LOC_ADDRESS"| "STD_HOUSE_NUMBER"| "STD_STREET_NAME"| "STD_BASE_NAME"| "STD_PREFIX"| "STD_SUFFIX"| "STD_STYPE_BEFORE"| "STD_STYPE_AFTER"| "STD_POSTAL_CODE"| "STD_CITY_NAME"| "STD_COUNTY_NAME"| "STD_STATE_CODE"| "STD_COUNTY_FIPS"| "STD_COUNTRY"| "STD_FULL_ADDRESS"| "ADDR_TYPE"| "LINK_MTHD"| "LOCATION_DESCRIPTION"| "CREATE_DATE"| "UPDATE_DATE"| "USER_ID"| "SENSITIVE_IND"| "USER_COMMENT"| "PUBLIC_IND"| "REFRESH_DATE"| "SMALL_BUS_IND"| "ENV_JUSTICE_CODE"| "PARENT_PGM_SYS_ID"| "STAND_ALONE_FLAG"| "SOURCE_OF_DATA"

### Program GIS File

Not currently triplified

"PGM_SYS_ACRNM"| "PGM_SYS_ID"| "LATITUDE83"| "LONGITUDE83"| "CONVEYOR"| "COLLECT_DESC"| "ACCURACY_VALUE"| "REF_POINT_DESC"| "HDATUM_DESC"| "SOURCE_DESC"| "STATE_CODE"

### Supplemental Interest File

Not currently triplified

"REGISTRY_ID"| "PGM_SYS_ACRNM"| "PGM_SYS_ID"| "INTEREST_TYPE"| "SUP_PGM_SYS_ACRNM"| "SUP_PGM_SYS_ID"| "SUP_INTEREST_TYPE"| "START_DATE"| "START_DATE_QUALIFIER"| "END_DATE"| "END_DATE_QUALIFIER"| "SOURCE_OF_DATA"| "LAST_REPORTED_DATE"| "REPORTED_SUP_INTEREST_TYPE"| "CREATE_DATE"| "UPDATE_DATE"


### Additional- EPA PFAS analytics tool industry sectors

**CODE**: \us-frs\facilities_pat.py

| Attribute | Description | Lift to Graph | Ontology Property |
|-----------------------|-------------|---------------|-------------------|
|**Facility**     |  | Yes     |  URI rdf:type us_frs:EPA-PFAS-Facility     | 
| Region
| State|
| State (Other)| City| Status| Industry| ECHO Facility Report| FAC_PERCENT_MINORITY| FAC_DERIVED_TRIBES| FAC_POP_DEN| EJSCREEN_FLAG_US| EJSCREEN Report| EPA Programs| Federal Facility| Federal Agency| Latitude| Longitude| Count| FAC_COUNTY| FAC_FIPS_CODE| FAC_INDIAN_CNTRY_FLG| FAC_COLLECTION_METHOD| FAC_DERIVED_HUC| FAC_DERIVED_WBD| FAC_DERIVED_CD113| FAC_DERIVED_CB2010| FAC_MAJOR_FLAG| FAC_ACTIVE_FLAG| FAC_INSPECTION_COUNT| FAC_DATE_LAST_INSPECTION| FAC_DAYS_LAST_INSPECTION| FAC_INFORMAL_COUNT| FAC_DATE_LAST_INFORMAL_ACTION| FAC_FORMAL_ACTION_COUNT| FAC_DATE_LAST_FORMAL_ACTION| FAC_TOTAL_PENALTIES| FAC_PENALTY_COUNT| FAC_DATE_LAST_PENALTY| FAC_LAST_PENALTY_AMT| FAC_QTRS_WITH_NC| FAC_PROGRAMS_WITH_SNC| FAC_COMPLIANCE_STATUS| FAC_SNC_FLG| AIR_FLAG| NPDES_FLAG| SDWIS_FLAG| RCRA_FLAG| TRI_FLAG| GHG_FLAG| AIR_IDS| CAA_PERMIT_TYPES| CAA_NAICS| CAA_SICS| NPDES_IDS| CWA_PERMIT_TYPES| CWA_NAICS| CWA_SICS| RCRA_IDS| RCRA_PERMIT_TYPES| RCRA_NAICS| SDWA_IDS| SDWA_SYSTEM_TYPES| SDWA_COMPLIANCE_STATUS| SDWA_SNC_FLAG| TRI_IDS| TRI_RELEASES_TRANSFERS| TRI_ON_SITE_RELEASES| TRI_OFF_SITE_TRANSFERS| TRI_REPORTER| FAC_IMP_WATER_FLG
