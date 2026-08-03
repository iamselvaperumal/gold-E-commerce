import re
from functools import lru_cache
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import Q

from .models import JewelryProduct
from .serializers import JewelryProductSerializer


CATEGORY_ALIASES = {
    "rings": [
        "ring", "rings", "modhiram", "mothiram", "mothram", "motiram", "modiram",
        "modaram", "motharam", "modharam", "motharam", "mudhiram", "mudiram",
        "finger ring", "engagement ring", "wedding ring", "மோதிரம்",
    ],
    "necklaces": ["necklace", "necklaces", "haram", "aaram", "aram", "chain necklace", "நெக்லஸ்", "ஆரம்", "ஹாரம்"],
    "bangles": ["bangle", "bangles", "valayal", "valaial", "valaiyal", "வளையல்"],
    "bracelets": ["bracelet", "bracelets", "kaapu", "kappu", "காப்பு"],
    "earrings": ["earring", "earrings", "jimikki", "jhumka", "stud", "ear stud", "kammal", "கம்மல்", "ஜிமிக்கி"],
    "chains": ["chain", "chains", "sangili", "sankili", "சங்கிலி"],
    "pendants": ["pendant", "pendants", "locket", "dollar", "talar", "டாலர்", "பெண்டண்ட்"],
    "mangalsutra": ["mangalsutra", "thali", "thaali", "mangal sutra", "thaali kodi", "thali kodi", "தாலி"],
    "anklets": ["anklet", "anklets", "kolusu", "கொலுசு"],
    "nosepin": ["nose pin", "nosepin", "mookuthi", "mukuthi", "மூக்குத்தி"],
    "toerings": ["toe ring", "toe rings", "metti", "மெட்டி"],
    "cufflinks": ["cufflink", "cufflinks"],
    "brooches": ["brooch", "brooches"],
    "tiepins": ["tie pin", "tiepin", "tie pins"],
    "coins": ["coin", "coins", "bar", "bars", "காசு", "நாணயம்"],
}

METAL_ALIASES = {
    "gold": ["gold", "22k", "24k", "916", "thangam", "thanga", "tanga", "thangam gold", "தங்கம்", "தங்க"],
    "silver": ["silver", "999", "velli", "veli", "velliy", "வெள்ளி"],
    "diamond": ["diamond", "vairam", "vair", "வைரம்"],
    "platinum": ["platinum", "platina", "பிளாட்டினம்"],
}

GRADE_ALIASES = {
    "22k": ["22k", "22 karat", "twenty two", "916", "916 gold"],
    "24k": ["24k", "24 karat", "twenty four", "999 gold"],
    "18k": ["18k", "18 karat", "eighteen"],
    "999": ["999", "pure silver", "silver 999"],
    "920": ["920", "platinum 920"],
}

GENDER_ALIASES = {
    "men": ["men", "mens", "male", "gents", "boys", "ஆண்கள்"],
    "women": ["women", "womens", "ladies", "female", "girls", "பெண்கள்"],
    "kids": ["kid", "kids", "children", "child", "baby", "kulanthai", "kulanthaiku", "kulandhai", "kulandhaiku", "குழந்தை"],
}

OCCASION_ALIASES = {
    "wedding": ["wedding", "bridal", "marriage", "kalyanam", "திருமணம்"],
    "gifting": ["gift", "gifting", "birthday", "anniversary", "present", "பரிசு"],
    "daily": ["daily", "everyday", "office", "regular"],
}

TEXT_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50,
    "oru": 1, "onnu": 1, "rendu": 2, "irandu": 2, "moonnu": 3, "moonu": 3,
    "naalu": 4, "anju": 5, "aaru": 6, "elu": 7, "ettu": 8, "onbadhu": 9, "pathu": 10,
    "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5,
}

STOPWORDS = {
    "show", "need", "want", "please", "find", "search", "give", "me", "for", "under", "above",
    "below", "around", "near", "product", "products", "jewellery", "jewelry", "design", "designs",
    "venum", "kattu", "kaatu", "iruka", "irukku", "kudu", "paaru", "ennoda", "enoda", "enakku", "என்னோட",
    "பாரு", "வேண்டும்", "காட்டு",
}


try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover - package may be unavailable locally until installed
    fuzz = None


_whisper_model = None


def _bool_setting(name, default=False):
    value = getattr(settings, name, default)
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def normalize_text(value):
    value = (value or "").strip().lower()
    value = re.sub(r"[₹,/-]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _contains_alias(text, aliases):
    padded = f" {text} "
    for alias in aliases:
        alias_text = normalize_text(alias)
        if not alias_text:
            continue
        if f" {alias_text} " in padded or alias_text in text:
            return True
    return False


def _best_alias(text, alias_map):
    for canonical, aliases in alias_map.items():
        if _contains_alias(text, aliases):
            return canonical
    if fuzz:
        words = [word for word in re.split(r"\W+", text) if len(word) > 2]
        best = (None, 0)
        for canonical, aliases in alias_map.items():
            for alias in aliases:
                for word in words:
                    score = fuzz.partial_ratio(word, normalize_text(alias))
                    if score > best[1]:
                        best = (canonical, score)
        if best[1] >= 86:
            return best[0]
    return None


def _extract_number(text):
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if match:
        try:
            return Decimal(match.group(1))
        except InvalidOperation:
            return None
    for word, number in TEXT_NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            return Decimal(number)
    return None


def _extract_weight(text):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|milligram|milligrams|g|gm|gram|grams)", text)
    if match:
        value = Decimal(match.group(1))
        unit = match.group(2)
        return value / Decimal(1000) if unit.startswith("m") else value

    gram_words = ["gram", "grams", "gm", "g", "pavun", "sovereign", "சவரன்", "கிராம்"]
    if any(word in text for word in gram_words):
        value = _extract_number(text)
        if value is not None:
            if "pavun" in text or "sovereign" in text or "சவரன்" in text:
                return value * Decimal("8")
            return value
    return None


def _extract_price(text):
    match = re.search(r"(?:under|below|less than|within|budget|rs|rupees|₹)\s*(\d+(?:\.\d+)?)\s*(k|lakh|lakhs)?", text)
    if not match:
        return None
    value = Decimal(match.group(1))
    suffix = match.group(2)
    if suffix == "k":
        value *= Decimal(1000)
    elif suffix in {"lakh", "lakhs"}:
        value *= Decimal(100000)
    return value


def _keyword_tokens(text):
    known_aliases = []
    for mapping in (CATEGORY_ALIASES, METAL_ALIASES, GRADE_ALIASES, GENDER_ALIASES, OCCASION_ALIASES):
        for aliases in mapping.values():
            known_aliases.extend(normalize_text(alias) for alias in aliases)
    cleaned = text
    for alias in sorted(known_aliases, key=len, reverse=True):
        if alias:
            cleaned = cleaned.replace(alias, " ")
    return [word for word in re.split(r"\W+", cleaned) if len(word) > 2 and word not in STOPWORDS]


def extract_intent(transcript, language=None):
    text = normalize_text(transcript)
    category = _best_alias(text, CATEGORY_ALIASES)
    metal = _best_alias(text, METAL_ALIASES)
    grade = _best_alias(text, GRADE_ALIASES)
    gender = _best_alias(text, GENDER_ALIASES)
    occasion = _best_alias(text, OCCASION_ALIASES)
    weight = _extract_weight(text)
    max_price = _extract_price(text)
    keywords = _keyword_tokens(text)

    matched = sum(1 for item in [category, metal, grade, gender, occasion, weight, max_price] if item) + min(len(keywords), 2)
    confidence = min(0.95, 0.35 + matched * 0.12)
    if category and metal:
        confidence = max(confidence, 0.72)
    elif category or keywords:
        confidence = max(confidence, 0.62)
    missing_fields = []
    if not category and not keywords:
        missing_fields.append("product_type")
    if category == "coins" and not metal:
        missing_fields.append("metal")

    return {
        "raw_text": transcript or "",
        "normalized_text": text,
        "language": language or getattr(settings, "VOICE_DEFAULT_LANGUAGE", "ta"),
        "category": category,
        "metal": metal,
        "grade": grade,
        "gender": gender,
        "occasion": occasion,
        "weight_grams": str(weight) if weight is not None else None,
        "max_price": str(max_price) if max_price is not None else None,
        "keywords": keywords[:8],
        "missing_fields": missing_fields,
        "confidence": round(confidence, 2),
    }


def apply_clarification(intent, field, value):
    allowed = {"product_type", "category", "metal", "grade", "gender", "occasion"}
    if field not in allowed:
        return intent
    updated = dict(intent or {})
    normalized_value = normalize_text(value)
    if field in {"product_type", "category"}:
        resolved = _best_alias(normalized_value, CATEGORY_ALIASES)
        if resolved:
            updated["category"] = resolved
    elif field == "metal":
        resolved = _best_alias(normalized_value, METAL_ALIASES)
        if resolved:
            updated["metal"] = resolved
    elif field == "grade":
        resolved = _best_alias(normalized_value, GRADE_ALIASES)
        if resolved:
            updated["grade"] = resolved
    elif field == "gender":
        resolved = _best_alias(normalized_value, GENDER_ALIASES)
        if resolved:
            updated["gender"] = resolved
    elif field == "occasion":
        resolved = _best_alias(normalized_value, OCCASION_ALIASES)
        if resolved:
            updated["occasion"] = resolved
    updated["missing_fields"] = [item for item in updated.get("missing_fields", []) if item not in {field, "product_type" if field == "category" else field}]
    updated["confidence"] = max(float(updated.get("confidence") or 0), 0.72)
    return updated


def clarification_payload(intent):
    missing = intent.get("missing_fields") or []
    if not missing:
        return None
    field = missing[0]
    if field == "metal":
        return {
            "field": "metal",
            "question": "Which metal should I search?",
            "options": ["gold", "silver", "diamond", "platinum"],
        }
    return {
        "field": "category",
        "question": "Which jewellery type should I search?",
        "options": ["rings", "necklaces", "bangles", "chains", "coins", "earrings"],
    }


def _decimal_value(value):
    try:
        return Decimal(str(value)) if value not in {None, ""} else None
    except InvalidOperation:
        return None


def search_products(intent, request=None):
    base_qs = JewelryProduct.objects.filter(is_active=True).prefetch_related("images")
    qs = base_qs
    if intent.get("category"):
        qs = qs.filter(category=intent["category"])
    if intent.get("metal"):
        qs = qs.filter(metal=intent["metal"])
    if intent.get("grade"):
        qs = qs.filter(grade__icontains=intent["grade"])
    if intent.get("gender"):
        qs = qs.filter(gender__icontains=intent["gender"])
    if intent.get("occasion"):
        qs = qs.filter(Q(occasion__icontains=intent["occasion"]) | Q(wedding_category__icontains=intent["occasion"]))

    max_price = _decimal_value(intent.get("max_price"))
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    keywords = intent.get("keywords") or []
    keyword_qs = qs
    for word in keywords[:4]:
        keyword_qs = keyword_qs.filter(
            Q(name__icontains=word) |
            Q(description__icontains=word) |
            Q(tag__icontains=word) |
            Q(occasion__icontains=word) |
            Q(wedding_category__icontains=word)
        )

    # Spoken transliterations can leave harmless words behind as keywords.
    # Prefer strict keyword matches, but fall back to category/metal matches instead of returning zero.
    products = list(keyword_qs[:120])
    if keywords and not products and intent.get("category"):
        products = list(qs[:120])
    weight = _decimal_value(intent.get("weight_grams"))
    tolerance = Decimal(str(getattr(settings, "VOICE_WEIGHT_TOLERANCE_GRAMS", 0.5)))

    def score(product):
        value = 0
        if intent.get("category") and product.category == intent["category"]:
            value += 20
        if intent.get("metal") and product.metal == intent["metal"]:
            value += 20
        if intent.get("grade") and intent["grade"] in (product.grade or "").lower():
            value += 8
        if product.tag:
            value += 3
        product_weight = _decimal_value(product.net_weight)
        if weight is not None and product_weight is not None:
            diff = abs(product_weight - weight)
            if diff <= tolerance:
                value += 25
            else:
                value += max(0, 12 - int(diff))
        text = normalize_text(" ".join([product.name or "", product.description or "", product.tag or "", product.occasion or "", product.wedding_category or ""]))
        value += sum(3 for word in keywords if word in text)
        return value

    products.sort(key=score, reverse=True)
    limit = int(getattr(settings, "VOICE_RESULT_LIMIT", 20))
    serializer = JewelryProductSerializer(products[:limit], many=True, context={"request": request})
    return serializer.data


def transcribe_audio(file_path, language_hint=None):
    global _whisper_model
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError("Voice model dependency is not installed on the backend.") from exc

    if _whisper_model is None:
        _whisper_model = WhisperModel(
            getattr(settings, "WHISPER_MODEL", "small"),
            device=getattr(settings, "WHISPER_DEVICE", "cpu"),
            compute_type=getattr(settings, "WHISPER_COMPUTE_TYPE", "int8"),
        )

    task = "translate" if _bool_setting("VOICE_TRANSLATE_TO_ENGLISH", False) else "transcribe"
    segments, info = _whisper_model.transcribe(
        file_path,
        language=language_hint or None,
        task=task,
        vad_filter=True,
    )
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    detected_language = getattr(info, "language", None) or language_hint or getattr(settings, "VOICE_DEFAULT_LANGUAGE", "ta")
    return transcript, detected_language
