import re
from urllib.parse import quote_plus, urlparse


ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$", re.IGNORECASE)

URL_PATTERNS = [
    re.compile(r"/dp/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/gp/product/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/product/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
]


def normalize_asin(value):
    """
    ASIN dəyərini təmizləyir və böyük hərflə qaytarır.
    Etibarsız dəyər üçün boş sətir qaytarır.
    """
    asin = str(value or "").strip().upper()

    if ASIN_PATTERN.fullmatch(asin):
        return asin

    return ""


def is_valid_asin(value):
    """
    Dəyərin etibarlı 10 simvolluq ASIN olub-olmadığını yoxlayır.
    """
    return bool(normalize_asin(value))


def extract_asin_from_url(url):
    """
    Amazon məhsul URL-indən ASIN çıxarır.

    Dəstəklənən formalar:
    /dp/ASIN
    /gp/product/ASIN
    /product/ASIN
    """
    url = str(url or "").strip()

    if not url:
        return ""

    for pattern in URL_PATTERNS:
        match = pattern.search(url)

        if match:
            return match.group(1).upper()

    return ""


def is_amazon_url(url):
    """
    URL-in Amazon domeninə aid olub-olmadığını yoxlayır.
    """
    url = str(url or "").strip()

    if not url:
        return False

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    return hostname == "amazon.de" or hostname.endswith(".amazon.de")


def build_product_url(asin, marketplace="amazon.de"):
    """
    ASIN əsasında təmiz canonical Amazon məhsul URL-i yaradır.
    """
    normalized_asin = normalize_asin(asin)

    if not normalized_asin:
        return ""

    marketplace = str(marketplace or "amazon.de").strip().lower()
    marketplace = marketplace.removeprefix("www.")

    return f"https://www.{marketplace}/dp/{normalized_asin}"


def build_search_url(query, marketplace="amazon.de"):
    """
    Məhsul adı əsasında Amazon axtarış fallback URL-i yaradır.
    """
    query = str(query or "").strip()

    if not query:
        return ""

    marketplace = str(marketplace or "amazon.de").strip().lower()
    marketplace = marketplace.removeprefix("www.")

    return f"https://www.{marketplace}/s?k={quote_plus(query)}"


def normalize_amazon_product_url(url, marketplace="amazon.de"):
    """
    Müxtəlif Amazon məhsul URL-lərini canonical /dp/ASIN formasına çevirir.
    """
    asin = extract_asin_from_url(url)

    if not asin:
        return ""

    return build_product_url(asin, marketplace=marketplace)
