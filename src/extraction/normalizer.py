"""Value normalization module for currencies, dates, percentages, and quantities."""

import re
from typing import Any, Tuple, Optional
from datetime import datetime


def normalize_currency(val_str: str) -> Optional[float]:
    """Convert currency string like 'Rs 12.5 crores' or '3,30,40,000' to float value in Rupees."""
    if not val_str:
        return None
    s = str(val_str).lower().replace(",", "").replace("rs.", "").replace("rs", "").strip()

    try:
        if "crore" in s or "cr" in s:
            m = re.search(r"([\d\.]+)", s)
            if m:
                return float(m.group(1)) * 10_000_000
        elif "lakh" in s or "lac" in s:
            m = re.search(r"([\d\.]+)", s)
            if m:
                return float(m.group(1)) * 100_000
        else:
            m = re.search(r"([\d\.]+)", s)
            if m:
                return float(m.group(1))
    except (ValueError, AttributeError):
        pass

    return None


def normalize_date(date_str: str) -> Optional[str]:
    """Convert date string like '8 January 2024' or '15/12/2024' to 'YYYY-MM-DD'."""
    if not date_str:
        return None
    s = str(date_str).strip()

    formats = [
        "%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%B %d, %Y", "%b %d, %Y"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Regex fallback for month names
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m:
        day, month, year = m.groups()
        for fmt in ["%d %B %Y", "%d %b %Y"]:
            try:
                dt = datetime.strptime(f"{day} {month} {year}", fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    return s  # Return original if parsing fails


def normalize_percentage(pct_str: str) -> Optional[float]:
    """Convert '0.5%' or '100%' to float."""
    if not pct_str:
        return None
    m = re.search(r"([\d\.]+)\s*%", str(pct_str))
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    m_num = re.search(r"^[\d\.]+$", str(pct_str).strip())
    if m_num:
        try:
            return float(m_num.group(0))
        except ValueError:
            pass
    return None


def normalize_quantity(qty_str: str) -> Tuple[Optional[float], Optional[str]]:
    """Parse string into (float_value, unit). e.g., '8,500 cubic metres' -> (8500.0, 'cum')."""
    if not qty_str:
        return None, None
    s = str(qty_str).replace(",", "").strip().lower()

    m = re.search(r"([\d\.]+)\s*([a-zA-Z\s]+)?", s)
    if m:
        try:
            val = float(m.group(1))
            unit = m.group(2).strip() if m.group(2) else None
            return val, unit
        except ValueError:
            pass

    return None, None
