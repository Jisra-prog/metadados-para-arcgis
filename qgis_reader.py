# -*- coding: utf-8 -*-
"""Read QgsLayerMetadata into the neutral MetadataRecord."""

from .metadata_model import MetadataRecord, unique
from .iso19139_reader import normalize_language


def _qdate_to_iso(qdate):
    try:
        if qdate is not None and qdate.isValid():
            # Date-only output is sufficient for ArcGIS citation dates.
            return qdate.date().toString("yyyy-MM-dd")
    except Exception:
        pass
    return ""


def _qdatetime_to_iso(qdt):
    try:
        if qdt is not None and qdt.isValid():
            return qdt.toString("yyyy-MM-ddTHH:mm:ss")
    except Exception:
        pass
    return ""


def _contact_to_dict(contact):
    addresses = []
    for addr in getattr(contact, "addresses", []) or []:
        addresses.append({
            "type": str(getattr(addr, "type", "") or ""),
            "address": str(getattr(addr, "address", "") or ""),
            "city": str(getattr(addr, "city", "") or ""),
            "administrativeArea": str(getattr(addr, "administrativeArea", "") or ""),
            "postalCode": str(getattr(addr, "postalCode", "") or ""),
            "country": str(getattr(addr, "country", "") or ""),
        })
    return {
        "organization": str(getattr(contact, "organization", "") or ""),
        "name": str(getattr(contact, "name", "") or ""),
        "position": str(getattr(contact, "position", "") or ""),
        "role": str(getattr(contact, "role", "") or ""),
        "email": str(getattr(contact, "email", "") or ""),
        "voice": str(getattr(contact, "voice", "") or ""),
        "fax": str(getattr(contact, "fax", "") or ""),
        "addresses": addresses,
    }


def _link_to_dict(link):
    return {
        "name": str(getattr(link, "name", "") or ""),
        "type": str(getattr(link, "type", "") or ""),
        "url": str(getattr(link, "url", "") or ""),
        "description": str(getattr(link, "description", "") or ""),
        "format": str(getattr(link, "format", "") or ""),
        "mimeType": str(getattr(link, "mimeType", "") or ""),
        "size": str(getattr(link, "size", "") or ""),
    }


def _transform_rect_to_wgs84(rect, source_crs):
    from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

    if not source_crs or not source_crs.isValid():
        return None
    target = QgsCoordinateReferenceSystem("EPSG:4326")
    try:
        if source_crs == target:
            transformed = rect
        else:
            transform = QgsCoordinateTransform(source_crs, target, QgsProject.instance())
            transformed = transform.transformBoundingBox(rect)
        return (
            float(transformed.xMinimum()),
            float(transformed.xMaximum()),
            float(transformed.yMinimum()),
            float(transformed.yMaximum()),
        )
    except Exception:
        return None


def _read_bbox(metadata, layer):
    from qgis.core import QgsRectangle

    boxes = []
    try:
        spatial_extents = metadata.extent().spatialExtents()
    except Exception:
        spatial_extents = []

    for extent in spatial_extents:
        try:
            bounds = extent.bounds
            rect = QgsRectangle(bounds.xMinimum(), bounds.yMinimum(), bounds.xMaximum(), bounds.yMaximum())
            source_crs = extent.extentCrs if extent.extentCrs.isValid() else metadata.crs()
            box = _transform_rect_to_wgs84(rect, source_crs)
            if box:
                boxes.append(box)
        except Exception:
            continue

    if not boxes:
        try:
            rect = layer.extent()
            source_crs = layer.crs()
            box = _transform_rect_to_wgs84(rect, source_crs)
            if box:
                boxes.append(box)
        except Exception:
            pass

    if not boxes:
        return None

    return (
        min(b[0] for b in boxes),
        max(b[1] for b in boxes),
        min(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _read_temporal(metadata):
    result = []
    try:
        ranges = metadata.extent().temporalExtents()
    except Exception:
        ranges = []
    for rng in ranges:
        try:
            begin = _qdatetime_to_iso(rng.begin())
            end = _qdatetime_to_iso(rng.end())
            if begin or end:
                result.append((begin, end))
        except Exception:
            continue
    return result


def read_qgis_layer(layer):
    from qgis.core import Qgis

    metadata = layer.metadata()
    record = MetadataRecord()

    record.title = str(metadata.title() or layer.name())
    record.abstract = str(metadata.abstract() or "")
    record.identifier = str(metadata.identifier() or layer.name())
    record.parent_identifier = str(metadata.parentIdentifier() or "")
    record.language = normalize_language(str(metadata.language() or "por"))
    record.resource_type = str(metadata.type() or "dataset")
    record.encoding = str(metadata.encoding() or "utf8")

    date_types = {
        "created": Qgis.MetadataDateType.Created,
        "published": Qgis.MetadataDateType.Published,
        "revised": Qgis.MetadataDateType.Revised,
        "superseded": Qgis.MetadataDateType.Superseded,
    }
    for name, enum_value in date_types.items():
        try:
            value = _qdate_to_iso(metadata.dateTime(enum_value))
            if value:
                record.dates[name] = value
        except Exception:
            pass

    keywords_map = metadata.keywords() or {}
    record.keyword_groups = {str(k): [str(v) for v in values] for k, values in keywords_map.items()}
    record.keywords = unique(v for values in record.keyword_groups.values() for v in values)
    try:
        record.categories = unique(str(v) for v in metadata.categories())
    except Exception:
        record.categories = unique(record.keyword_groups.get("gmd:topicCategory", []))

    record.contacts = [_contact_to_dict(c) for c in (metadata.contacts() or [])]
    record.constraints = unique(
        f"{str(getattr(c, 'type', '') or '').strip()}: {str(getattr(c, 'constraint', '') or '').strip()}".strip(": ")
        for c in (metadata.constraints() or [])
    )
    record.rights = unique(str(v) for v in (metadata.rights() or []))
    record.licenses = unique(str(v) for v in (metadata.licenses() or []))
    record.fees = str(metadata.fees() or "")

    record.bbox = _read_bbox(metadata, layer)
    record.temporal_extents = _read_temporal(metadata)

    crs = metadata.crs() if metadata.crs().isValid() else layer.crs()
    if crs and crs.isValid():
        record.crs_authid = str(crs.authid() or "")
        record.crs_name = str(crs.description() or "")

    history = unique(str(v) for v in (metadata.history() or []))
    record.lineage_statement = "\n".join(history)

    record.links = [_link_to_dict(link) for link in (metadata.links() or [])]
    for link in record.links:
        if link.get("format") or link.get("type"):
            record.distributions.append({
                "name": link.get("format") or link.get("name") or "",
                "version": "",
                "specification": link.get("type") or "",
            })

    record.metadata_standard_name = "QGIS Layer Metadata"
    record.metadata_standard_version = ""

    extra = {}
    if record.parent_identifier:
        extra["Identificador do recurso pai"] = [record.parent_identifier]
    if record.fees:
        extra["Taxas"] = [record.fees]
    if record.encoding:
        extra["Codificação"] = [record.encoding]
    record.additional = extra
    return record
