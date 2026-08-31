# -*- coding: utf-8 -*-
"""Neutral metadata model shared by QGIS, ISO 19139 and ArcGIS XML writers."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


BBox = Tuple[float, float, float, float]  # west, east, south, north
TemporalExtent = Tuple[str, str]  # begin, end (ISO-8601 strings)


@dataclass
class MetadataRecord:
    title: str = ""
    abstract: str = ""
    identifier: str = ""
    parent_identifier: str = ""
    language: str = "por"
    resource_type: str = "dataset"
    encoding: str = "utf8"

    dates: Dict[str, str] = field(default_factory=dict)
    edition: str = ""

    keywords: List[str] = field(default_factory=list)
    keyword_groups: Dict[str, List[str]] = field(default_factory=dict)
    categories: List[str] = field(default_factory=list)

    contacts: List[dict] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    rights: List[str] = field(default_factory=list)
    licenses: List[str] = field(default_factory=list)
    fees: str = ""

    bbox: Optional[BBox] = None
    bbox_description: str = ""
    temporal_extents: List[TemporalExtent] = field(default_factory=list)
    # Escala equivalente / de referência dos dados (denominador 1:n).
    scale: str = ""
    # Faixa de escala apropriada do ArcGIS.
    # maximum = mais ampliado (denominador menor, ex. 25000)
    # minimum = mais reduzido (denominador maior, ex. 100000)
    scale_maximum: str = ""
    scale_minimum: str = ""

    crs_authid: str = ""
    crs_name: str = ""

    lineage_statement: str = ""
    sources: List[str] = field(default_factory=list)

    distributions: List[dict] = field(default_factory=list)
    links: List[dict] = field(default_factory=list)

    metadata_standard_name: str = ""
    metadata_standard_version: str = ""
    metadata_date: str = ""

    additional: Dict[str, List[str]] = field(default_factory=dict)


def unique(values):
    result = []
    for value in values or []:
        value = str(value).strip()
        if value and value not in result:
            result.append(value)
    return result
