# -*- coding: utf-8 -*-
"""Write the neutral MetadataRecord to ArcGIS Metadata XML."""

import os
import re
import xml.etree.ElementTree as ET  # nosec B405 -- used only to construct/write XML
from datetime import datetime

from .metadata_model import unique


ROLE_CODES = {
    "resourceprovider": "001",
    "custodian": "002",
    "owner": "003",
    "user": "004",
    "distributor": "005",
    "originator": "006",
    "pointofcontact": "007",
    "principalinvestigator": "008",
    "processor": "009",
    "publisher": "010",
    "author": "011",
}


def clean(value):
    if value is None:
        return ""
    return " ".join(str(value).split())


def _add(parent, tag, value=None, attrib=None):
    element = ET.SubElement(parent, tag, attrib or {})
    if value not in (None, ""):
        element.text = str(value)
    return element


def _language_iso3(value):
    value = clean(value).lower().replace("_", "-")
    aliases = {
        "pt": "por", "pt-br": "por", "por": "por", "português": "por", "portugues": "por",
        "en": "eng", "en-us": "eng", "eng": "eng", "english": "eng", "inglês": "eng", "ingles": "eng",
        "es": "spa", "es-es": "spa", "spa": "spa", "spanish": "spa", "español": "spa", "espanhol": "spa",
    }
    if value in aliases:
        return aliases[value]
    if value.startswith(("portugu", "pt/", "pt-")) or "portugu" in value:
        return "por"
    if value.startswith(("english", "ingl", "en/", "en-")):
        return "eng"
    if value.startswith(("spanish", "espan", "españ", "es/", "es-")):
        return "spa"
    return value or "por"


def _xml_lang(value):
    return {"por": "pt", "eng": "en", "spa": "es"}.get(_language_iso3(value), "pt")


def _date_br(value):
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value or "")
    return f"{match.group(3)}/{match.group(2)}/{match.group(1)}" if match else (value or "")


def _summary(record):
    date = record.dates.get("created") or record.dates.get("published") or record.dates.get("revised")
    parts = []
    if record.title:
        parts.append(record.title.rstrip(". ") + ".")
    if record.identifier:
        parts.append(f"Identificador principal: {record.identifier}.")
    if record.language:
        parts.append(f"Linguagem: {_language_iso3(record.language)}.")
    parts.append(f"Data de criação: {_date_br(date) if date else 'não informada'}.")
    return " ".join(parts)


def _credits(contacts):
    result = []
    for contact in contacts or []:
        core = " — ".join(clean(contact.get(k)) for k in ("organization", "name", "position") if clean(contact.get(k)))
        role = clean(contact.get("role"))
        if role:
            core = (core + f" (papel: {role})").strip()
        email = clean(contact.get("email"))
        if email:
            core = (core + f" — {email}").strip()
        if core:
            result.append(core)
    return "; ".join(unique(result))


def _description(record):
    parts = []
    if clean(record.abstract):
        parts.append(record.abstract.strip())

    sections = []
    if record.parent_identifier:
        sections.append(("Identificador do recurso pai", [record.parent_identifier]))
    if record.bbox_description:
        sections.append(("Descrição geográfica da extensão", [record.bbox_description]))
    if record.metadata_standard_name:
        standard = record.metadata_standard_name
        if record.metadata_standard_version:
            standard += f" — versão {record.metadata_standard_version}"
        sections.append(("Padrão de metadados de origem", [standard]))
    if record.metadata_date:
        sections.append(("Data do metadado de origem", [_date_br(record.metadata_date)]))
    if record.edition:
        sections.append(("Edição", [record.edition]))
    if record.fees:
        sections.append(("Taxas", [record.fees]))

    for title, values in (record.additional or {}).items():
        if title in {"Identificador do recurso pai", "Descrição geográfica da extensão", "Taxas", "Codificação"}:
            continue
        sections.append((title, values))

    if sections:
        parts.append("\n\nINFORMAÇÕES ADICIONAIS DO METADADO DE ORIGEM:")
        for title, values in sections:
            values = unique(values)
            if not values:
                continue
            parts.append(f"{title}:")
            parts.extend(f"- {value}" for value in values)

    return "\n".join(parts).strip()


def _role_code(role):
    key = re.sub(r"[^a-z]", "", clean(role).lower())
    return ROLE_CODES.get(key, role or "007")


def _write_contact(parent, tag, contact):
    node = ET.SubElement(parent, tag)
    _add(node, "rpIndName", clean(contact.get("name")))
    _add(node, "rpOrgName", clean(contact.get("organization")))
    _add(node, "rpPosName", clean(contact.get("position")))

    info = ET.SubElement(node, "rpCntInfo")
    phone = ET.SubElement(info, "cntPhone")
    _add(phone, "voiceNum", clean(contact.get("voice")))
    _add(phone, "faxNum", clean(contact.get("fax")))

    addresses = contact.get("addresses") or [{}]
    for address in addresses:
        addr = ET.SubElement(info, "cntAddress")
        _add(addr, "delPoint", clean(address.get("address")))
        _add(addr, "city", clean(address.get("city")))
        _add(addr, "adminArea", clean(address.get("administrativeArea")))
        _add(addr, "postCode", clean(address.get("postalCode")))
        _add(addr, "country", clean(address.get("country")))
        if clean(contact.get("email")):
            _add(addr, "eMailAdd", clean(contact.get("email")))

    role = ET.SubElement(node, "role")
    _add(role, "RoleCd", attrib={"value": _role_code(contact.get("role"))})
    return node


def _write_temporal_extent(data, begin, end):
    if not (begin or end):
        return
    ext = ET.SubElement(data, "dataExt")
    temp_ele = ET.SubElement(ext, "tempEle")
    temp_extent = ET.SubElement(temp_ele, "TempExtent")
    ex_temp = ET.SubElement(temp_extent, "exTemp")
    primitive = ET.SubElement(ex_temp, "TM_GeometricPrimitive")
    if begin and end and begin != end:
        period = ET.SubElement(primitive, "TM_Period")
        _add(period, "begin", begin)
        _add(period, "end", end)
    else:
        instant = ET.SubElement(primitive, "TM_Instant")
        _add(instant, "tmPosition", begin or end)


def _write_crs(root, authid, name):
    authid = clean(authid)
    name = clean(name)
    if not authid and not name:
        return

    authority = ""
    code = authid
    if ":" in authid:
        authority, code = authid.split(":", 1)

    ref_info = ET.SubElement(root, "refSysInfo")
    ref_system = ET.SubElement(ref_info, "RefSystem")
    ref_id = ET.SubElement(ref_system, "refSysID")
    if code:
        _add(ref_id, "identCode", attrib={"code": code})
    if authority:
        _add(ref_id, "idCodeSpace", authority)
    if name:
        _add(ref_id, "idVersion", name)


def build_arcgis_tree(record):
    language = _language_iso3(record.language)
    root = ET.Element("metadata", {"xml:lang": _xml_lang(language)})

    esri = ET.SubElement(root, "Esri")
    _add(esri, "CreaDate", datetime.now().strftime("%Y%m%d"))
    _add(esri, "CreaTime", datetime.now().strftime("%H%M%S00"))
    _add(esri, "ArcGISFormat", "1.0")
    _add(esri, "SyncOnce", "TRUE")
    _add(esri, "ArcGISProfile", "ItemDescription")
    if record.resource_type:
        _add(esri, "resourceType", record.resource_type)

    props = ET.SubElement(ET.SubElement(esri, "DataProperties"), "itemProps")
    _add(props, "itemName", record.identifier or record.title)

    # ArcGIS "Appropriate Scale Range".
    # v1.2.1 preserves explicit min/max support, but when only the
    # reference scale is available it reproduces the successful v1.1
    # behavior by using the same denominator in both limits.
    range_maximum = record.scale_maximum or record.scale
    range_minimum = record.scale_minimum or record.scale
    if range_maximum or range_minimum:
        scale_range = ET.SubElement(esri, "scaleRange")
        if range_minimum:
            _add(scale_range, "minScale", range_minimum)
        if range_maximum:
            _add(scale_range, "maxScale", range_maximum)

    md_lang = ET.SubElement(root, "mdLang")
    _add(md_lang, "languageCode", attrib={"value": language})
    md_char = ET.SubElement(root, "mdChar")
    _add(md_char, "CharSetCd", attrib={"value": record.encoding or "utf8"})
    _add(root, "mdDateSt", record.metadata_date or datetime.now().strftime("%Y-%m-%d"))
    if record.metadata_standard_name:
        _add(root, "mdStanName", record.metadata_standard_name)
    if record.metadata_standard_version:
        _add(root, "mdStanVer", record.metadata_standard_version)

    if record.contacts:
        _write_contact(root, "mdContact", record.contacts[0])

    data = ET.SubElement(root, "dataIdInfo")
    citation = ET.SubElement(data, "idCitation")
    _add(citation, "resTitle", record.title)

    dates = ET.SubElement(citation, "date")
    if record.dates.get("created"):
        _add(dates, "createDate", record.dates["created"])
    if record.dates.get("published"):
        _add(dates, "pubDate", record.dates["published"])
    if record.dates.get("revised"):
        _add(dates, "reviseDate", record.dates["revised"])
    if record.dates.get("superseded"):
        _add(dates, "supersDate", record.dates["superseded"])

    if record.edition:
        _add(citation, "resEd", record.edition)
    if record.identifier:
        cit_id = ET.SubElement(citation, "citId")
        _add(cit_id, "identCode", record.identifier)

    _add(data, "idPurp", _summary(record))
    _add(data, "idAbs", _description(record))

    credits = _credits(record.contacts)
    if credits:
        _add(data, "idCredit", credits)

    for contact in record.contacts:
        _write_contact(data, "idPoC", contact)

    data_lang = ET.SubElement(data, "dataLang")
    _add(data_lang, "languageCode", attrib={"value": language})

    keywords = unique(record.keywords)
    if keywords:
        search_keys = ET.SubElement(data, "searchKeys")
        for keyword in keywords:
            _add(search_keys, "keyword", keyword)

    for vocabulary, values in (record.keyword_groups or {}).items():
        values = unique(values)
        if not values or vocabulary == "gmd:topicCategory":
            continue
        theme = ET.SubElement(data, "themeKeys")
        thesaurus = ET.SubElement(theme, "thesaName")
        _add(thesaurus, "resTitle", vocabulary)
        for value in values:
            _add(theme, "keyword", value)

    for category in unique(record.categories):
        topic = ET.SubElement(data, "tpCat")
        _add(topic, "TopicCatCd", attrib={"value": category})

    limitations = unique((record.constraints or []) + (record.rights or []) + (record.licenses or []))
    if limitations:
        res_const = ET.SubElement(data, "resConst")
        consts = ET.SubElement(res_const, "Consts")
        _add(consts, "useLimit", " | ".join(limitations))

    if record.bbox:
        west, east, south, north = record.bbox
        ext = ET.SubElement(data, "dataExt")
        if record.bbox_description:
            _add(ext, "exDesc", record.bbox_description)
        geo_ele = ET.SubElement(ext, "geoEle")
        box = ET.SubElement(geo_ele, "GeoBndBox", {"esriExtentType": "search"})
        _add(box, "westBL", f"{west:.8f}")
        _add(box, "eastBL", f"{east:.8f}")
        _add(box, "southBL", f"{south:.8f}")
        _add(box, "northBL", f"{north:.8f}")
        _add(box, "exTypeCode", "1")

    for begin, end in record.temporal_extents:
        _write_temporal_extent(data, begin, end)

    if record.scale:
        scale = ET.SubElement(data, "dataScale")
        equivalent = ET.SubElement(scale, "equScale")
        _add(equivalent, "rfDenom", record.scale)

    if record.lineage_statement or record.sources:
        dq_info = ET.SubElement(root, "dqInfo")
        lineage = ET.SubElement(dq_info, "dataLineage")
        if record.lineage_statement:
            _add(lineage, "statement", record.lineage_statement)
        for source in unique(record.sources):
            source_node = ET.SubElement(lineage, "dataSource")
            _add(source_node, "srcDesc", source)
            if record.scale:
                src_scale = ET.SubElement(source_node, "srcScale")
                _add(src_scale, "rfDenom", record.scale)

    if record.distributions or record.links:
        dist_info = ET.SubElement(root, "distInfo")
        distributor = ET.SubElement(dist_info, "distributor")
        for distribution in record.distributions:
            fmt = ET.SubElement(distributor, "distorFormat")
            _add(fmt, "formatName", clean(distribution.get("name")))
            _add(fmt, "formatVer", clean(distribution.get("version")))
            _add(fmt, "formatSpec", clean(distribution.get("specification")))
        for link in record.links:
            if not clean(link.get("url")):
                continue
            transfer = ET.SubElement(distributor, "distorTran")
            online = ET.SubElement(transfer, "onLineSrc")
            _add(online, "linkage", clean(link.get("url")))
            _add(online, "protocol", clean(link.get("type")))
            _add(online, "orName", clean(link.get("name")))
            _add(online, "orDesc", clean(link.get("description")))

    _write_crs(root, record.crs_authid, record.crs_name)
    return root


def write_arcgis_xml(record, output_path):
    root = build_arcgis_tree(record)
    ET.indent(root, space="  ")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="UTF-8", xml_declaration=True)

    generated_tags = root.findall("./dataIdInfo/searchKeys/keyword")
    if len(generated_tags) != len(unique(record.keywords)):
        raise RuntimeError("Falha na validação das Tags do XML ArcGIS.")
    return output_path
