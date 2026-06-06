import re

LANGUAGE_KEYWORDS = {
    "tamil":     ["tamil", "tam", "[tam]", "(tam)"],
    "hindi":     ["hindi", "hin", "[hin]", "(hindi)", "bollywood"],
    "english":   ["english", "eng", "[eng]", "(eng)", "hollywood"],
    "telugu":    ["telugu", "tel", "[tel]", "(telugu)"],
    "malayalam": ["malayalam", "mal", "[mal]", "(mal)"],
    "kannada":   ["kannada", "kan", "[kan]", "(kannada)"],
    "bengali":   ["bengali", "ben", "[ben]", "(bengali)"],
    "marathi":   ["marathi", "mar", "[mar]"],
    "punjabi":   ["punjabi", "pun", "[pun]"],
    "dual":      ["dual audio", "dual", "[dual]"],
    "multi":     ["multi audio", "multi", "[multi]"],
}

QUALITY_KEYWORDS = {
    "4k":    ["4k", "2160p", "uhd"],
    "1080p": ["1080p", "fullhd", "fhd", "bluray", "bdrip", "webrip.1080"],
    "720p":  ["720p", "hd", "hdtv", "webrip.720", "webhd"],
    "480p":  ["480p", "dvdrip", "dvdscr"],
    "360p":  ["360p", "cam", "camrip", "hdcam"],
}


def detect_language(filename: str) -> str:
    name = filename.lower()
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return lang
    return "unknown"


def detect_quality(filename: str) -> str:
    name = filename.lower()
    for quality, keywords in QUALITY_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return quality
    return "unknown"


def parse_movie_info(filename: str) -> dict:
    language = detect_language(filename)
    quality  = detect_quality(filename)
    name     = re.sub(r"\.(mkv|mp4|avi|mov|wmv|webm)$", "", filename, flags=re.IGNORECASE)

    all_tags = [kw for kws in LANGUAGE_KEYWORDS.values() for kw in kws]
    all_tags += [kw for kws in QUALITY_KEYWORDS.values() for kw in kws]
    all_tags += ["www.", ".com", "@", "cinemacityhub", "hdmovies", "mkvcage",
                 "tamilblasters", "moviesda", "isaimini", "tamilgun"]

    clean = name
    for tag in sorted(all_tags, key=len, reverse=True):
        clean = re.sub(re.escape(tag), " ", clean, flags=re.IGNORECASE)

    clean = re.sub(r"[\[\](){}]", " ", clean)
    clean = re.sub(r"[\._\-]+",   " ", clean)
    clean = re.sub(r"\s{2,}",     " ", clean).strip()

    return {"clean_name": clean.title(), "language": language, "quality": quality}
