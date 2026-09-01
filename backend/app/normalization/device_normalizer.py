from typing import Dict, Optional, Tuple
from .text_normalizer import normalize_arabic_text

DEVICE_ALIASES: Dict[str, Tuple[str, bool]] = {
    # Exact Devices (is_ambiguous = False)
    "تربوهيلر": ("Turbohaler", False),
    "تيربوهيلر": ("Turbohaler", False),
    "turbohaler": ("Turbohaler", False),
    "إليبتا": ("Ellipta", False),
    "اليبتا": ("Ellipta", False),
    "ellipta": ("Ellipta", False),
    "ديسكوس": ("Diskus", False),
    "diskus": ("Diskus", False),
    "accuhaler": ("Accuhaler", False),
    "أكوهيلر": ("Accuhaler", False),
    "handihaler": ("HandiHaler", False),
    "هاندي هيلر": ("HandiHaler", False),
    "هانديهيلر": ("HandiHaler", False),
    "respimat": ("Respimat", False),
    "ريسبيمات": ("Respimat", False),
    "pari boy": ("PARI BOY", False),
    "باري بوي": ("PARI BOY", False),
    "pmdi": ("pMDI", False),
    "قلم أنسولين": ("Insulin Pen", False),
    "قلم انسولين": ("Insulin Pen", False),
    "insulin pen": ("Insulin Pen", False),

    # Ambiguous Inhaler Terms (is_ambiguous = True)
    "بخاخ": ("generic_inhaler", True),
    "بخاخة": ("generic_inhaler", True),
    "بخاخ صدر": ("generic_inhaler", True),
    "inhaler": ("generic_inhaler", True),
    "نيبولايزر": ("generic_nebulizer", True),
    "nebulizer": ("generic_nebulizer", True),
    "جهاز استنشاق": ("generic_inhaler", True)
}

def resolve_device(text: str) -> Optional[Tuple[str, bool]]:
    """
    Resolves device mention in text.
    Returns: (canonical_device_name, is_ambiguous)
    """
    clean = normalize_arabic_text(text)
    
    # Priority to exact devices first
    for alias_k, (dev_name, is_amb) in DEVICE_ALIASES.items():
        if not is_amb:
            norm_alias = normalize_arabic_text(alias_k)
            if norm_alias in clean:
                return (dev_name, False)

    # Check ambiguous terms
    for alias_k, (dev_name, is_amb) in DEVICE_ALIASES.items():
        if is_amb:
            norm_alias = normalize_arabic_text(alias_k)
            if norm_alias in clean:
                return (dev_name, True)

    return None

def is_ambiguous_device(device_name: str) -> bool:
    """Returns True if the device term is ambiguous (e.g. generic 'بخاخ')."""
    if not device_name:
        return True
    return device_name.lower() in ("generic_inhaler", "generic_nebulizer", "بخاخ", "inhaler")
