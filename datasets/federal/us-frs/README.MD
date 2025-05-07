# Overview of the raw dataset

* **Name of dataset:** Facility Registry Service
* **Source Agency:** EPA
* **Data source location:**
  * [Envirofacts Data Service API](https://data.epa.gov/efservice/) (note: requires further query parameters to resolve, e.g. [example 1](https://data.epa.gov/efservice/FRS_FACILITY_SITE/STD_STATE_CODE/=/ME/COUNT), [example 2](https://data.epa.gov/efservice/FRS_FACILITY_SITE/STD_STATE_CODE/=/ME/rows/0:2/JSON) )
  * [FRS State Downloads](https://www.epa.gov/frs/epa-state-combined-csv-download-files)
*note: there are many ways to access FRS data, such as via ECHO, state downloads contain industry codes*
* **Additional Data source:**
  * [Industry Sectors Data](https://echo.epa.gov/trends/pfas-tools#data) *note: this identifies facilities the epa suspects are using pfas*
  * [Additional FRS identifiers](https://frs-public.epa.gov/ords/frs_public2/ez_frs_column.list?table_name=D_EF_FAC.V_PUB_FRS_FACILITY_SITE_GEOPGM)
  * [program reference](https://usepa.servicenowservices.com/oeca_icis/en/list-of-program-system-acronyms-found-in-icis?id=kb_article_view&sys_kb_id=42327c7f1bfc1954fd044262f54bcb8f)
* **Metadata description:**
  * [Envirofacts api documentation](https://www.epa.gov/enviro/envirofacts-data-service-api)
  * [Envirofacts model page](https://enviro.epa.gov/envirofacts/metadata/model)
  * [Envirofacts table model(example)](https://enviro.epa.gov/envirofacts/metadata/table/frs/v_pub_frs_naics_ez)
  * [frs data dictionary](https://www.epa.gov/sites/default/files/2015-09/documents/frs_data_dictionary.pdf)
  * [Facility State File Documentation 1132012_new](https://www.epa.gov/frs/epa-state-combined-csv-download-files) (comes with state download)
  * [Environmental Interest Types](https://www.epa.gov/sites/default/files/2020-01/documents/interest_types.pdf)
* **Format of data returned:** json, zip of csv (state downloads)
* **Data update interval:**
* **General Comments**:

## Schema Diagram

![US FRS Schema](./ontology/FIO%20-%20facility.png)

* [WIP](https://lucid.app/lucidchart/0b649dc4-e466-4d29-ae34-5c0f113f5a46/edit?viewport_loc=-1067%2C1107%2C3523%2C1881%2CcJplkqIup7-.&invitationId=inv_0e3483a0-96fc-4faf-8c17-1a5bf73fd23b)

## Raw Data Attribute List and Mappings with Ontology

 FRS State Downloads (11 csv files per state), or API access via table

### FRS_FACILITY_SITE api table (joined with GEO_FACILITY_POINT) / *_FACILITY_FILE.csv

**API CODE**: \us-frs\facilities_api.py

**from file code(outdated):**\us-frs\older_scripts\facilities_statedownload.py

**[REFERENCE](https://enviro.epa.gov/envirofacts/metadata/table/frs/frs_program_facility)**

| State download Attribute    | API Attribute |  Description  | Lift to Graph | Ontology Property    |
|--------------|--------------|---------------|----------------------|------|
| FRS_FACILITY_DETAIL_REPORT_URL | - | report url   |   |    |
| REGISTRY_ID  | registry_id | registry id to uniquely identify facility  | Yes     | epa-frs:FRS-Facility (in URI)  epa-frs:hasFRSid (xsd:string, owl:subPropertyOf dcterms:identifier ) |
| PRIMARY_NAME | primary_name| public or commercial name| Yes    | epa-frs:FRS-Facility dcterms:alternative (xsd:string) |
| | std_name| The primary name after a set of standardization rules are applied for comparison purposes. The rules include removing special characters and certain words (e.g., "/", "Inc.") and replacing abbreviated words with standardized equivalents (e.g., "Assoc" becomes "Association"). | Yes | epa-frs:FRS-Facility rdfs:label  |
| LOCATION_ADDRESS   |location_address | The address that describes the physical (geographic) location of the front door or main entrance of a facility site, including urban-style street address or rural address.| (only use standardized form) |    |
| _ |  std_full_address | The standardized complete address including STD_LOC_ADDRESS STD_CITY_NAME STD_STATE_CODE  AND STD_POSTAL_CODE.  | Yes | epa-frs:FRS-Facility schema:address (xsd:string)|
| | std_stype_before | | No | |
| | std_base_name | The name of the street or road, not including the prefix, suffix, or pre- or postdirectional codes. | No ||
| | std_street_name| The name assigned to a street or road, not including other urban-style street address components.| No ||
| | std_stype_after || No ||
| | std_loc_address|| No ||
| | std_suffix|| No ||
| | std_house_number || No ||
| | std_prefix|| No ||
| SUPPLEMENTAL_LOCATION |  supplemental_location  | text that provides additional information about a place, including a building name with its secondary unit and number, an industrial park name, an installation name or descriptive text where no formal address is available. | |    |
| CITY_NAME    | city_name, std_city_name | locality name - nameof city, town village or other locality within whose boundaries (the majority of) the facility site is located.  |   |    |
| COUNTY_NAME  | county_name, std_county_name |  | No      |    |
| FIPS_CODE    | fips_code, std_county_fips| county fips code (state and county)  | Yes     | epa-frs:FRS-Facility kwg-ont:sfWithin kwg-ont:AdministrativeRegion_2      |
| STATE_CODE   | state_code, std_state_code | USPS abbreviation for state    |  For initial filter only |    |
| STATE_NAME   | state_name |   | No  |    |
| COUNTRY_NAME | country_name, std_country |   | No  |    |
| POSTAL_CODE  | postal_code, std_postal_code |  5 digit zip code and 4 digit extension code (if available)   | No  |    |
| FEDERAL_FACILITY_CODE | federal_facility_code   | Yes/No the facility is property of the Federal Government    | Yes     | epa-frs:FRS-Facility epa-frs:ofFacilityType epa-frs-data:d.Federal-Facility |
| FEDERAL_AGENCY_NAME  |     | name of federal agency (derived from FEDERAL_AGENCY_CODE lookup)   | yes | epa-frs:Agency rdfs:label (in controlled vocab script) |
| | federal_agency_code | The Federal Agency/Bureau code. The five character code consists of a letter followed by  four numbers. There are four possible letters that can occupy the first character position: 'C' for Civilian Federal Agency; 'D' for Department of Defense; 'E' for Department of Energy; 'X' for Unknown. The second and third characters represent the agency code, while the fourth and fifth characters represent the bureau code. | Yes | epa-frs:FRS-Facility prov:wasAttributedTo epa-frs:Agency (in URI) |
| TRIBAL_LAND_CODE | tribal_land_code  | Code indicating whether or not the facility site is located on tribal land.  | Yes  |  epa-frs:FRS-Facility epa-frs:ofFacilityType epa-frs-data:d.Tribal-Facility  |
| TRIBAL_LAND_NAME | tribal_land_name | Name of Tribal Reservation, statistical area, or Public Domain Allotment.      | ?    |  |
| CONGRESSIONAL_DIST_NUM | legislative_dist_num  | The number that represents a Legislative District within a state. | No |    |
| CENSUS_BLOCK_CODE | |  | No |    |
| HUC_CODE   |  | The Hydrologic Unit Code (HUC) that represents a geographic area representing part or all of a surface drainage basin, a combination of drainage basins, or a distinct hydrologic feature. | No  |    |
| EPA_REGION_CODE  | epa_region_code | The code that represents an EPA Region.    | No |    |
| SITE_TYPE_NAME   | site_type_name | The descriptive name for the type of site the facility occupies.  Allowable Values: [ Stationary, Monitoring Site, Brownfields Site, Water System ,  Contamination Addressed,  Contaminated Site,  Potentially Contaminated Site  ]  | Yes     |  added to URI -> rdfs:subClassOf us_frs:FRS-Facility  |
| LOCATION_DESCRIPTION  |  location_description | Descriptive information about location of facility, including directions.      |  No |    |
| CREATE_DATE | create_date | date first posted to database  |  Yes |  epa-frs:FRS-Facility dcterms:created xsd:date  |
| UPDATE_DATE | update_date, last_reported_date | A system-generated value that represents the most recent calendar date and time the corresponding information was updated in the database.  | Yes | epa-frs:FRS-Facility schema:dateModified xsd:date   |
| US_MEXICO_BORDER_IND  |   | An indicator that the facility is located within 62.5 miles (100 km) of the United States - Mexico Border. Only applicable to facilities in California, Arizona, New Mexico, and Texas.    | No  |    |
| PGM_SYS_ACRNMS  |   | list of program acronyms the facility is tracked by    | from other tables | |
| LATITUDE83   | frs.GEO_FACILITY_POINT.latitude83 | | Yes     |  epa-frs:FRS-Facility geo:hasGeometry/geo:asWKT  |
| LONGITUDE83  | frs.GEO_FACILITY_POINT.longitude83 | | Yes     |  epa-frs:FRS-Facility geo:hasGeometry/geo:asWKT  |
| CONVEYOR     | - (geo_pgm_facility_coordinate) | Identification of the party that transmitted the latitude and longitude  |  No |    |
| COLLECT_DESC | - (geo_pgm_facility_coordinate) | Method used to determine Lat/Long    | No  |    |
| ACCURACY_VALUE | - (geo_pgm_facility_coordinate) | Measure of accuracy in meters of latitude/longitude    |  No |    |
| REF_POINT_DESC |  - (geo_pgm_facility_coordinate) | Name that identifies the place for which geographic coordinates were established     |  No |    |
| HDATUM_DESC  | - (geo_pgm_facility_coordinate) | Horizontal reference datum used in determining latitude longitude coordinates  |  No |    |
| SOURCE_DESC  | - (geo_pgm_facility_coordinate) | Name of party responsible for providing lat/long coordinates |  No |    |
| | user_id | The user ID of the person who entered the data or the method by which the data was entered into the system. | No | |
| | refresh_date | The date the data was last extracted from the data source. | No ||
| | parent_registry_id |  The unique identification number, assigned by the EPA Facility Registry System, to the parent facility site (for example, the SDWIS water system). | ? ||
| | env_justice_code| Note:Dropped from schema in April 2025. The code that identifies the type of environmental justice concern affecting the facility or enforcement action.| No ||
| | small_bus_ind| | Yes | epa-frs:FRS-Facility epa-frs:ofFacilityType epa-frs-data:d.SmallBusiness-Facility|
| | interest_status_code| Null | no ||
| | review_reason| The reason the record is flagged for manual review. | No ||
| | sensitive_ind|Indicates whether or not the associated data is enforcement sensitive. | No ||
| | operating_status|| No ||
| | stand_alone_flag | Indicates whether or not the facility is standalone (i.e., only one environmental interest is linked to the facility) or multimedia (more than one environmental interest is linked to the facility).'Y' means the facility is standalone, and 'N' means the facility is not standalone.| No ||
| | icis_identifier | This column is not currently being used. | No ||
| | public_ind | Indicates whether or not the associated data is accessible by the public on the Internet. |No - only public data accessed ||
| | review_flag |A flag that indicates the record requires a manual review due to changes from a data source | No ||
| | data_quality_code| Quality of the location | No ||
| | addr_type|The type of address given in the LOCATION_ADDRESS column (i.e., standard urban, PO Box). | No ||

### frs.v_pub_frs_naics_ez / ME_NAICS_FILE.csv

many to one relation with facility file

**OLD CODE**: \us-frs\industries-echo.py

| Attribute   | API attribute | Description    | Lift to Graph | Ontology Property/Class      |
|-------------| --------------|----------------|---------------| ---------------------------- |
|  | city_name | | No | |
| CODE_DESCRIPTION| code_description | The text that represents a subdivision of an industry that accommodates user needs in the United States  | No (pull from Census bureau files)  |      |
| | country_name | | No | |
| | county_name | | No | |
| | epa_region_code | | No | |
| | latitude83 | | No(from other table) | |
| | legislative_dist_num| | No | |
| | location_address | | No | |
| | longitude83 | | No | |
| NAICS_CODE | naics_code| The code that represents a subdivision of an industry that accommodates user needs in the United States (six-digits). | Yes     | fio:ofIndustry naics:NAICS-Industry (in URI)      |
 PGM_SYS_ACRNM|  pgm_sys_acrnm    | The abbreviated name that represents the name of an information management system for an environmental program.      | Yes     | owl:subclassOf epa-frs:FRS-Facility (also in iri of fio:ofIndustry and dcterms:identifier subproperties )  |
| REGISTRY_ID | registry_id |  | Yes     | us_frs:FRS-Facility    |
|
| PGM_SYS_ID  | | The identification number, such as the permit number assigned by an information management system that represents a facility site, waste site, operable unit, or other feature tracked by that Environmental Information System. |   |      |
| INTEREST_TYPE |    | The environmental permit or regulatory program that applies to the facility site | ? |      |

| PRIMARY_INDICATOR | | The name that indicates whether the associated NAICS Code represents the primary activity occurring at the facility site   | Yes     | us_frs:primary_industry or us_frs:secondary_industry |

### ME_SIC_FILE.csv

many to one relation with facility file

**CODE**: \us-frs\industries-echo.py

| Attribute   | Description     | Lift to Graph | Ontology Property |
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|-------------------|
| REGISTRY_ID |     |   | |
| PGM_SYS_ACRNM     | The abbreviated name that represents the name of an information management system for an environmental program. |   | |
| PGM_SYS_ID  | The identification number, such as the permit number, assigned by an information management system that represents a facility site, waste site, operable unit, or other feature tracked by that Environmental Information System. |   | |
| INTEREST_TYPE|     | The environmental permit or regulatory program that applies to the facility site  |   |
| SIC_CODE |   | The code that represents the economic activity of a company (4-digits).     |   |
| PRIMARY_INDICATOR|  | The name that indicates whether the associated SIC Code represents the primary activity occurring at the facility site      |   |
| CODE_DESCRIPTION |  | The text that represents a subdivision of an industry that accommodates user needs in the United States   |   |

### ALTERNATIVE NAME FILE

Not currently triplified

| Attribute | Description | Lift to Graph | Ontology Property |
|-----------------------|-------------|---------------|-------------------|
| REGISTRY_ID     | |   | |
| PGM_SYS_ACRNM   | |   | |
| PGM_SYS_ID      | |   | |
| ALTERNATIVE_NAME      | |   | |
| ALTERNATIVE_NAME_TYPE | |   | |

### ORGANIZATION FILE

Not currently triplified

Describes organizations affiliated with a facility

| Attribute  | Description  | Lift to Graph | Ontology Property |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|---------------------------------------------------------------|
| "REGISTRY_ID"    |  |   |   |
| "PGM_SYS_ACRNM"  |  |   |   |
| "PGM_SYS_ID"     |  |   |   |
| "INTEREST_TYPE"  |  |   |   |
| "AFFILIATION_TYPE"     | The name that describes the capacity or function that an organization or individual serves for a facility site (Legally Responsible Entity, Legal Operator, Waste Treater, Waste Handler, Land Owner, Parent Corporation, Owner/Operator)( Report Certifier, Regulatory Contact, Public Contact, Technical Contact, Owner, Operator) | Yes     | fio:hasAffiliation, mapped out under us_frs: as subproperties |
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
| "COUNTRY_NAME"   |  |   |  |

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
| Region ||||
| State||||
| State (Other)||||
| City Status||||
| Industry||||
| ECHO Facility Report||||
| FAC_PERCENT_MINORITY||||
| FAC_DERIVED_TRIBES||||
| FAC_POP_DEN||||
| EJSCREEN_FLAG_US||||
| EJSCREEN Report||||
| EPA Programs||||
| Federal Facility||||
| Federal Agency||||
| Latitude||||
| Longitude||||
| Count||||
| FAC_COUNTY||||
| FAC_FIPS_CODE||||
| FAC_INDIAN_CNTRY_FLG||||
| FAC_COLLECTION_METHOD||||
| FAC_DERIVED_HUC||||
| FAC_DERIVED_WBD||||
| FAC_DERIVED_CD113||||
| FAC_DERIVED_CB2010||||
| FAC_MAJOR_FLAG||||
| FAC_ACTIVE_FLAG||||
| FAC_INSPECTION_COUNT||||
| FAC_DATE_LAST_INSPECTION||||
| FAC_DAYS_LAST_INSPECTION||||
| FAC_INFORMAL_COUNT||||
| FAC_DATE_LAST_INFORMAL_ACTION||||
| FAC_FORMAL_ACTION_COUNT||||
| FAC_DATE_LAST_FORMAL_ACTION||||
| FAC_TOTAL_PENALTIES||||
| FAC_PENALTY_COUNT||||
| FAC_DATE_LAST_PENALTY||||
| FAC_LAST_PENALTY_AMT||||
| FAC_QTRS_WITH_NC||||
| FAC_PROGRAMS_WITH_SNC||||
| FAC_COMPLIANCE_STATUS||||
| FAC_SNC_FLG||||
| AIR_FLAG||||
| NPDES_FLAG||||
| SDWIS_FLAG||||
| RCRA_FLAG||||
| TRI_FLAG||||
| GHG_FLAG||||
| AIR_IDS||||
| CAA_PERMIT_TYPES||||
| CAA_NAICS||||
| CAA_SICS||||
| NPDES_IDS||||
| CWA_PERMIT_TYPES||||
| CWA_NAICS||||
| CWA_SICS||||
| RCRA_IDS||||
| RCRA_PERMIT_TYPES||||
| RCRA_NAICS||||
| SDWA_IDS||||
| SDWA_SYSTEM_TYPES||||
| SDWA_COMPLIANCE_STATUS||||
| SDWA_SNC_FLAG||||
| TRI_IDS||||
| TRI_RELEASES_TRANSFERS||||
| TRI_ON_SITE_RELEASES||||
| TRI_OFF_SITE_TRANSFERS||||
| TRI_REPORTER||||
| FAC_IMP_WATER_FLG ||||

### API tables

* FRS_AGENCY_REF
* FRS_ALTERNATIVE_ID
* FRS_ALTERNATIVE_ID_HISTORY
* FRS_ALT_NAME
* FRS_ALT_NAME_HISTORY
* FRS_CODE_DESCRIPTION
* FRS_COMMENT
* FRS_CONTACT
* FRS_CONTACT_HISTORY
* *FRS_FACILITY_SITE
* FRS_INTEREST
* FRS_INTEREST_HISTORY
* FRS_INTEREST_REF
* FRS_MAILING_ADDRESS
* FRS_MAILING_ADDRESS_HISTORY
* FRS_NAICS
* FRS_NAICS_HISTORY
* FRS_ORGANIZATION
* FRS_ORG_HISTORY
* FRS_OUTFALL_FEATURE
* FRS_PGM_FACILITY_HISTORY
* FRS_PROGRAM_FACILITY
* FRS_PROGRAM_TRIBE
* FRS_RELEASE_POINT
* FRS_RELEASE_POINT_UNIT
* FRS_REL_PT_ALT_ID
* FRS_SIC
* FRS_SIC_HISTORY
* FRS_SITE_HISTORY
* FRS_STATE_REF
* FRS_SUPPLEMENTAL_INTEREST
* FRS_SUP_INTEREST_HISTORY
* FRS_SYSTEM_REF
* FRS_TRIBE_REF
* FRS_UNIT
* FRS_UNIT_ALT_ID
* FRS_USER_REGISTRY
* FRS_USER_REGISTRY_HISTORY
* FRS_ZIP_CODE_REF
* GEO_ASSIGN_ACC_LK
* GEO_COLLECT_MTH_LK
* GEO_CONVEYOR
* GEO_FACILITY_POINT
* GEO_GEOMETRIC_TYPE_LK
* GEO_HORIZ_DATUM_LK
* GEO_PGM_FACILITY_COORDiNATE
* GEO_REF_POINT_LK
* GEO_SOURCE_LK
* GEO_SUB_ID_REF
* GEO_VERIFY_LK
* GEO_VERT_DATUM_LK
* GEO_VERT_METHOD_LK
* *MV_GEO_FACILITY_POINT
* *V_GEO_PGM_COORDINATE_ALL
