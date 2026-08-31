# -*- coding: utf-8 -*-
"""Read ISO 19115/19139 (including MGB 2.0 style documents) into MetadataRecord."""

import re
import xml.etree.ElementTree as ET

from .metadata_model import MetadataRecord, unique

GMD = "http://www.isotc211.org/2005/gmd"
GCO = "http://www.isotc211.org/2005/gco"
GML = "http://www.opengis.net/gml/3.2"
NS = {"gmd": GMD, "gco": GCO, "gml": GML}


def clean(value):
    if value is None:
        return ""
    return " ".join(str(value).split())


def text(element):
    if element is None:
        return ""
    return clean("".join(element.itertext()))


def first(root, paths):
    for path in paths:
        element = root.find(path, NS)
        if element is not None:
            value = text(element)
            if value:
                return value
    return ""


def code_value(element):
    if element is None:
        return ""
    return clean(element.attrib.get("codeListValue") or element.attrib.get("value") or text(element))


def normalize_language(value):
    value = clean(value).lower().replace("_", "-")
    aliases = {
        "pt": "por", "pt-br": "por", "por": "por", "português": "por", "portugues": "por",
        "en": "eng", "en-us": "eng", "eng": "eng", "english": "eng", "inglês": "eng", "ingles": "eng",
        "es": "spa", "es-es": "spa", "spa": "spa", "spanish": "spa", "español": "spa", "espanhol": "spa",
    }
    if value in aliases:
        return aliases[value]
    # Common free-text values produced by manually filled QGIS metadata.
    if value.startswith(("portugu", "pt/", "pt-")) or "portugu" in value:
        return "por"
    if value.startswith(("english", "ingl", "en/", "en-")):
        return "eng"
    if value.startswith(("spanish", "espan", "españ", "es/", "es-")):
        return "spa"
    return value or "por"


def _find_identification(root):
    return root.find(".//gmd:identificationInfo/gmd:MD_DataIdentification", NS)


def _read_dates(identification):
    dates = {}
    if identification is None:
        return dates
    for ci_date in identification.findall(".//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date", NS):
        date = first(ci_date, ["gmd:date/gco:Date", "gmd:date/gco:DateTime"])
        kind = code_value(ci_date.find("gmd:dateType/gmd:CI_DateTypeCode", NS)).lower()
        if date and kind:
            if kind == "creation":
                dates["created"] = date
            elif kind == "publication":
                dates["published"] = date
            elif kind == "revision":
                dates["revised"] = date
            else:
                dates.setdefault(kind, date)
    return dates


def _read_bbox(root):
    box = root.find(".//gmd:EX_GeographicBoundingBox", NS)
    if box is None:
        return None
    paths = {
        "west": "gmd:westBoundLongitude",
        "east": "gmd:eastBoundLongitude",
        "south": "gmd:southBoundLatitude",
        "north": "gmd:northBoundLatitude",
    }
    values = {}
    for key, path in paths.items():
        parent = box.find(path, NS)
        if parent is None:
            return None
        child = next(iter(parent), None)
        try:
            values[key] = float(text(child))
        except (TypeError, ValueError):
            return None
    return values["west"], values["east"], values["south"], values["north"]


def _read_scale(root):
    for path in [
        ".//gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer",
        ".//gmd:scaleDenominator/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer",
    ]:
        value = first(root, [path])
        if value:
            return value
    return ""


def _read_keywords(root):
    groups = {}
    all_keywords = []
    for block in root.findall(".//gmd:descriptiveKeywords/gmd:MD_Keywords", NS):
        kind = code_value(block.find("gmd:type/gmd:MD_KeywordTypeCode", NS)) or "keywords"
        values = []
        for element in block.findall("gmd:keyword", NS):
            value = text(element)
            if value:
                values.append(value)
                all_keywords.append(value)
        groups.setdefault(kind, [])
        groups[kind].extend(values)
    return unique(all_keywords), {key: unique(values) for key, values in groups.items()}


def _read_contacts(root):
    result = []
    seen = set()
    paths = [
        ".//gmd:contact/gmd:CI_ResponsibleParty",
        ".//gmd:pointOfContact/gmd:CI_ResponsibleParty",
        ".//gmd:distributorContact/gmd:CI_ResponsibleParty",
    ]
    for path in paths:
        for party in root.findall(path, NS):
            addresses = []
            for addr in party.findall(".//gmd:address/gmd:CI_Address", NS):
                addresses.append({
                    "type": "postal",
                    "address": first(addr, ["gmd:deliveryPoint/gco:CharacterString"]),
                    "city": first(addr, ["gmd:city/gco:CharacterString"]),
                    "administrativeArea": first(addr, ["gmd:administrativeArea/gco:CharacterString"]),
                    "postalCode": first(addr, ["gmd:postalCode/gco:CharacterString"]),
                    "country": first(addr, ["gmd:country/gco:CharacterString"]),
                })
            item = {
                "organization": first(party, ["gmd:organisationName/gco:CharacterString"]),
                "name": first(party, ["gmd:individualName/gco:CharacterString"]),
                "position": first(party, ["gmd:positionName/gco:CharacterString"]),
                "role": code_value(party.find("gmd:role/gmd:CI_RoleCode", NS)),
                "email": first(party, [".//gmd:electronicMailAddress/gco:CharacterString"]),
                "voice": first(party, [".//gmd:voice/gco:CharacterString"]),
                "fax": first(party, [".//gmd:facsimile/gco:CharacterString"]),
                "addresses": addresses,
            }
            key = tuple(str(item.get(k, "")) for k in ("organization", "name", "position", "role", "email"))
            if any(key) and key not in seen:
                seen.add(key)
                result.append(item)
    return result


def _read_constraints(root):
    result = []
    for block in root.findall(".//gmd:resourceConstraints", NS):
        for x in block.findall(".//gmd:useLimitation/gco:CharacterString", NS):
            if text(x):
                result.append(text(x))
        for x in block.findall(".//gmd:otherConstraints/gco:CharacterString", NS):
            if text(x):
                result.append(text(x))
        for label, path in [
            ("Restrição de acesso", ".//gmd:accessConstraints/gmd:MD_RestrictionCode"),
            ("Restrição de uso", ".//gmd:useConstraints/gmd:MD_RestrictionCode"),
        ]:
            for x in block.findall(path, NS):
                value = code_value(x)
                if value:
                    result.append(f"{label}: {value}")
    return unique(result)


def _read_categories(root):
    return unique(text(x) for x in root.findall(".//gmd:topicCategory/gmd:MD_TopicCategoryCode", NS))


def _read_temporal(root):
    result = []
    for period in root.findall(".//gmd:EX_TemporalExtent//gml:TimePeriod", NS):
        begin = first(period, ["gml:beginPosition"])
        end = first(period, ["gml:endPosition"])
        if begin or end:
            result.append((begin, end))
    for instant in root.findall(".//gmd:EX_TemporalExtent//gml:TimeInstant", NS):
        position = first(instant, ["gml:timePosition"])
        if position:
            result.append((position, position))
    return result


def _read_lineage(root):
    statements = [text(x) for x in root.findall(".//gmd:lineage//gmd:statement/gco:CharacterString", NS) if text(x)]
    sources = [text(x) for x in root.findall(".//gmd:lineage//gmd:source//gmd:description/gco:CharacterString", NS) if text(x)]
    return "\n".join(unique(statements)), unique(sources)


def _read_distribution(root):
    distributions = []
    formats = []
    for fmt in root.findall(".//gmd:distributionFormat/gmd:MD_Format", NS):
        item = {
            "name": first(fmt, ["gmd:name/gco:CharacterString"]),
            "version": first(fmt, ["gmd:version/gco:CharacterString"]),
            "specification": "",
        }
        if item["name"] or item["version"]:
            formats.append(item)
    distributions.extend(formats)

    links = []
    for online in root.findall(".//gmd:onLine/gmd:CI_OnlineResource", NS):
        item = {
            "url": first(online, ["gmd:linkage/gmd:URL"]),
            "name": first(online, ["gmd:name/gco:CharacterString"]),
            "description": first(online, ["gmd:description/gco:CharacterString"]),
            "type": code_value(online.find("gmd:function/gmd:CI_OnLineFunctionCode", NS)),
            "format": "",
            "mimeType": "",
            "size": "",
        }
        if any(item.values()):
            links.append(item)
    return distributions, links


def read_iso19139(path):
    tree = ET.parse(path)
    root = tree.getroot()
    identification = _find_identification(root)

    record = MetadataRecord()
    record.title = first(root, [".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString"])
    record.abstract = first(root, [".//gmd:identificationInfo//gmd:abstract/gco:CharacterString"])
    record.identifier = first(root, ["./gmd:fileIdentifier/gco:CharacterString", ".//gmd:fileIdentifier/gco:CharacterString"])
    record.parent_identifier = first(root, ["./gmd:parentIdentifier/gco:CharacterString"])

    language_element = None
    if identification is not None:
        language_element = identification.find("gmd:language/gmd:LanguageCode", NS)
    if language_element is None:
        language_element = root.find("gmd:language/gmd:LanguageCode", NS)
    record.language = normalize_language(code_value(language_element))

    scope = root.find("gmd:hierarchyLevel/gmd:MD_ScopeCode", NS)
    record.resource_type = code_value(scope) or "dataset"
    record.encoding = code_value(root.find("gmd:characterSet/gmd:MD_CharacterSetCode", NS)) or "utf8"

    record.dates = _read_dates(identification)
    record.edition = first(root, [".//gmd:identificationInfo//gmd:edition/gco:CharacterString"])
    record.metadata_date = first(root, ["./gmd:dateStamp/gco:Date", "./gmd:dateStamp/gco:DateTime"])

    record.keywords, record.keyword_groups = _read_keywords(root)
    record.categories = _read_categories(root)
    record.contacts = _read_contacts(root)
    record.constraints = _read_constraints(root)

    record.bbox = _read_bbox(root)
    record.bbox_description = first(root, [".//gmd:extent//gmd:description/gco:CharacterString"])
    record.temporal_extents = _read_temporal(root)
    record.scale = _read_scale(root)

    record.crs_authid = first(root, [".//gmd:referenceSystemIdentifier//gmd:code/gco:CharacterString"])
    record.crs_name = first(root, [".//gmd:referenceSystemIdentifier//gmd:codeSpace/gco:CharacterString"])

    record.lineage_statement, record.sources = _read_lineage(root)
    record.distributions, record.links = _read_distribution(root)

    record.metadata_standard_name = first(root, ["./gmd:metadataStandardName/gco:CharacterString"])
    record.metadata_standard_version = first(root, ["./gmd:metadataStandardVersion/gco:CharacterString"])

    extra = {}
    if record.parent_identifier:
        extra["Identificador do recurso pai"] = [record.parent_identifier]
    if record.bbox_description:
        extra["Descrição geográfica da extensão"] = [record.bbox_description]
    record.additional = extra
    return record
