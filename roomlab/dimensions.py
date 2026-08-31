import re

def parse_dimension(value: str | float | int) -> float:
    """Parse common imperial/metric dimension notation and return inches."""
    if isinstance(value, (int, float)):
        if value <= 0: raise ValueError("dimension must be positive")
        return float(value)
    s = str(value).strip().lower().replace("’", "'").replace("′", "'").replace("“", '"').replace("”", '"')
    if not s: raise ValueError("dimension is required")
    cm = re.fullmatch(r"([\d.]+)\s*(?:cm|centimeters?)", s)
    if cm: result = float(cm.group(1)) / 2.54
    else:
        feet = re.search(r"([\d.]+)\s*(?:feet|foot|ft|')", s)
        inches = re.search(r"([\d.]+)\s*(?:inches|inch|in|\")", s)
        if feet or inches: result = (float(feet.group(1)) * 12 if feet else 0) + (float(inches.group(1)) if inches else 0)
        elif re.fullmatch(r"[\d.]+", s): result = float(s)
        else: raise ValueError(f"invalid dimension: {value}")
    if result <= 0: raise ValueError("dimension must be positive")
    return round(result, 4)

def format_dimension(value: float, unit: str = "feet") -> str:
    if unit == "inches": return f'{value:g}”'
    if unit == "cm": return f'{value * 2.54:.1f} cm'
    feet, inches = divmod(round(value), 12)
    return f"{feet}’ {inches}”" if inches else f"{feet}’"

