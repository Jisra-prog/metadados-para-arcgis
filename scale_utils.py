# -*- coding: utf-8 -*-
"""Helpers for parsing and formatting cartographic scale denominators."""

import re


def parse_scale_denominator(value):
    """Parse common Brazilian/user scale inputs into a positive integer denominator.

    Accepted examples:
    - 50000
    - 1:50000
    - 50.000
    - 1:50.000
    - 50000,00
    """
    text = str(value or "").strip().lower()
    if not text:
        return None

    text = text.replace("escala", "").strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    text = text.replace(" ", "")

    if "," in text:
        integer_part = text.split(",", 1)[0].replace(".", "")
        digits = re.sub(r"\D", "", integer_part)
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", text):
        digits = text.replace(".", "")
    else:
        digits = re.sub(r"\D", "", text)

    if not digits:
        return None
    try:
        result = int(digits)
    except ValueError:
        return None
    return result if result > 0 else None


def format_scale(value):
    try:
        value = int(round(float(value)))
    except Exception:
        return "não informada"
    if value <= 0:
        return "não informada"
    return "1:" + f"{value:,}".replace(",", ".")
