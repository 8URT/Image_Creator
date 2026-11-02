"""Mauritius weather forecast via Tomorrow.io + MMS French bulletin."""

from __future__ import annotations

import os
import re
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any

import requests

MMS_BULLETIN_URL = (
    "https://metservice.intnet.mu/forecast-bulletin-french-mauritius.php"
)
MMS_RODRIGUES_BULLETIN_URL = (
    "https://metservice.intnet.mu/forecast-bulletin-french-rodrigues.php"
)

try:
    from zoneinfo import ZoneInfo
    MAURITIUS_TZ = ZoneInfo("Indian/Mauritius")
except Exception:
    MAURITIUS_TZ = timezone(timedelta(hours=4))

WEATHER_CODE_FR = {
    1000: "Ensoleillé",
    1100: "Plutôt ensoleillé",
    1101: "Partiellement nuageux",
    1102: "Nuageux",
    1001: "Couvert",
    2000: "Brume",
    2100: "Brume",
    4000: "Bruine",
    4001: "Pluie",
    4200: "Pluie légère",
    4201: "Forte pluie",
    5000: "Neige",
    5001: "Averses de neige",
    5100: "Neige légère",
    5101: "Forte neige",
    6000: "Bruine verglaçante",
    6001: "Pluie verglaçante",
    6200: "Pluie verglaçante légère",
    6201: "Forte pluie verglaçante",
    7000: "Grêle",
    7101: "Forte grêle",
    7102: "Grêle légère",
    8000: "Orage",
}

WEATHER_CODE_ICON = {
    1000: "☀️",
    1100: "🌤️",
    1101: "⛅",
    1102: "🌥️",
    1001: "☁️",
    2000: "🌫️",
    2100: "🌫️",
    4000: "🌦️",
    4001: "🌧️",
    4200: "🌦️",
    4201: "🌧️",
    5000: "❄️",
    5001: "🌨️",
    5100: "🌨️",
    5101: "❄️",
    6000: "🧊",
    6001: "🧊",
    6200: "🧊",
    6201: "🧊",
    7000: "🧊",
    7101: "🧊",
    7102: "🧊",
    8000: "⛈️",
}

_FR_WEEKDAYS = ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim")
_FR_MONTHS = (
    "jan", "fév", "mar", "avr", "mai", "juin",
    "juil", "aoû", "sep", "oct", "nov", "déc",
)

_weather_forecast_cache: dict[str, Any] = {"expires_at": 0.0, "payload": None}
_CACHE_TTL_SECONDS = 900


def _weather_round(value: Any, suffix: str = "") -> str:
    if value is None:
        return "—"
    try:
        return f"{int(round(float(value)))}{suffix}"
    except (TypeError, ValueError):
        return "—"


def _code_label(code: int | None) -> str:
    if code is None:
        return "—"
    if code in WEATHER_CODE_FR:
        return WEATHER_CODE_FR[code]
    if 1000 <= code < 2000:
        return "Nuageux"
    if 2000 <= code < 3000:
        return "Brume"
    if 4000 <= code < 5000:
        return "Pluie"
    if 5000 <= code < 6000:
        return "Neige"
    if 6000 <= code < 7000:
        return "Verglas"
    if 7000 <= code < 8000:
        return "Grêle"
    if code >= 8000:
        return "Orage"
    return "—"


def _code_icon(code: int | None) -> str:
    if code is None:
        return "☁️"
    if code in WEATHER_CODE_ICON:
        return WEATHER_CODE_ICON[code]
    if 1000 <= code < 2000:
        return "☁️"
    if 4000 <= code < 5000:
        return "🌧️"
    if 5000 <= code < 6000:
        return "❄️"
    if code >= 8000:
        return "⛈️"
    return "☁️"


def _day_label(iso_time: str | None) -> str:
    if not iso_time:
        return "—"
    try:
        raw = iso_time.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone(MAURITIUS_TZ)
        return f"{_FR_WEEKDAYS[local.weekday()]} {local.day} {_FR_MONTHS[local.month - 1]}"
    except Exception:
        return iso_time[:10] if iso_time else "—"


def _pick_code(values: dict) -> int | None:
    for key in ("weatherCodeMax", "weatherCodeMin", "weatherCode"):
        if values.get(key) is not None:
            try:
                return int(values[key])
            except (TypeError, ValueError):
                continue
    return None


def _temp_string(values: dict) -> str:
    tmin = values.get("temperatureMin")
    tmax = values.get("temperatureMax")
    tavg = values.get("temperatureAvg")
    if tmin is not None and tmax is not None:
        try:
            return f"{int(round(float(tmin)))}–{int(round(float(tmax)))} °C"
        except (TypeError, ValueError):
            pass
    if tmax is not None:
        return f"{_weather_round(tmax)} °C"
    if tavg is not None:
        return f"{_weather_round(tavg)} °C"
    return "—"


def _precip_string(values: dict) -> str:
    for key in ("precipitationProbabilityAvg", "precipitationProbabilityMax"):
        if values.get(key) is not None:
            return _weather_round(values[key], " %")
    return "—"


def _humidity_string(values: dict) -> str:
    for key in ("humidityAvg", "humidityMax"):
        if values.get(key) is not None:
            return _weather_round(values[key], " %")
    return "—"


# Port Louis area / Port Mathurin
DEFAULT_MAURITIUS_LOCATION = "-20.1609,57.5012"
DEFAULT_RODRIGUES_LOCATION = "-19.7244,63.4271"


def fetch_tomorrow_weather_forecast(location: str | None = None) -> list[dict]:
    api_key = os.environ.get("TOMORROW_IO_API_KEY", "").strip()
    if not api_key:
        raise ValueError("TOMORROW_IO_API_KEY is not configured")

    location = (location or os.environ.get("WEATHER_LOCATION") or DEFAULT_MAURITIUS_LOCATION).strip()
    units = os.environ.get("WEATHER_UNITS", "metric").strip() or "metric"

    response = requests.get(
        "https://api.tomorrow.io/v4/weather/forecast",
        params={
            "location": location,
            "timesteps": "1d",
            "units": units,
            "apikey": api_key,
        },
        headers={"accept-encoding": "gzip"},
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()

    daily = payload.get("timelines", {}).get("daily")
    if isinstance(daily, list):
        return daily

    timelines = payload.get("timelines")
    if isinstance(timelines, list):
        for block in timelines:
            if block.get("timestep") == "1d":
                return block.get("intervals") or block.get("values") or []
    return []


def _avg_temp_display(day: dict | None) -> tuple[int | None, str]:
    if not day:
        return None, "—"
    tmin = day.get("temp_min")
    tmax = day.get("temp_max")
    try:
        if tmin is not None and tmax is not None:
            avg = int(round((float(tmin) + float(tmax)) / 2))
            return avg, f"{avg}°C"
    except (TypeError, ValueError):
        pass
    temp = (day.get("temp") or "").strip()
    if temp and temp != "—":
        return None, temp.replace(" ", "")
    return None, "—"


def today_card_from_day(day: dict | None, region: str) -> dict[str, Any]:
    day = day or {}
    temp_avg, temp_display = _avg_temp_display(day)
    return {
        "region": region,
        "icon": day.get("icon") or "⛅",
        "condition": day.get("prevision") or "—",
        "temp_avg": temp_avg,
        "temp_display": temp_display,
        "humidity": day.get("humidity"),
        "humidity_display": None,
    }


def extract_mms_station_humidity(page_text: str) -> dict[str, int]:
    """Parse Humidity: N% from MMS 'Current conditions' station cards."""
    text = page_text or ""
    stations: dict[str, int] = {}
    # Blocks look like: Current conditions \n Station \n ... \n Humidity: 78%
    pattern = re.compile(
        r"(?is)Current\s+conditions\s+(.+?)\s+Humidity:\s*(\d{1,3})\s*%",
    )
    for match in pattern.finditer(text):
        block = re.sub(r"\s+", " ", match.group(1)).strip()
        # Station name is the first line-ish token(s) before condition/temp
        name = block.split(" °")[0].strip()
        # Drop trailing condition words if glued; keep leading station label
        name = re.split(
            r"(?i)\b(cloudy|partly cloudy|clear|sunny|rain|fair|overcast)\b",
            name,
            maxsplit=1,
        )[0].strip(" -")
        name = re.sub(r"\s*\(.*?\)\s*", " ", name).strip()
        if not name:
            continue
        try:
            stations[name] = int(match.group(2))
        except (TypeError, ValueError):
            continue
    return stations


def _humidity_for_region(stations: dict[str, int], region: str) -> tuple[int | None, str | None]:
    if not stations:
        return None, None
    keys = list(stations.keys())
    if region == "Rodrigues":
        preferred = [k for k in keys if re.search(r"(?i)rodrigues", k)]
    else:
        preferred = [
            k
            for k in keys
            if re.search(r"(?i)port\s*louis|vacoas|plaisance", k)
            and not re.search(r"(?i)rodrigues", k)
        ]
        # Prefer Port Louis when present
        port = [k for k in preferred if re.search(r"(?i)port\s*louis", k)]
        if port:
            preferred = port
    if not preferred:
        preferred = keys
    values = [stations[k] for k in preferred if k in stations]
    if not values:
        return None, None
    avg = int(round(sum(values) / len(values)))
    return avg, f"{avg}%"


def normalize_forecast_days(
    raw_days: list[dict],
    max_days: int = 5,
    *,
    start_from_tomorrow: bool = False,
) -> list[dict]:
    max_days = max(1, min(7, int(max_days or 5)))
    today_iso = datetime.now(MAURITIUS_TZ).date().isoformat()
    normalized: list[dict] = []

    for entry in raw_days:
        values = entry.get("values") or {}
        if not isinstance(values, dict):
            values = {}
        code = _pick_code(values)
        iso_time = entry.get("time") or ""
        date_str = iso_time[:10] if iso_time else ""
        if start_from_tomorrow and date_str and date_str <= today_iso:
            continue
        normalized.append(
            {
                "date": date_str,
                "day_label": _day_label(iso_time),
                "weather_code": code,
                "icon": _code_icon(code),
                "prevision": _code_label(code),
                "temp_min": values.get("temperatureMin"),
                "temp_max": values.get("temperatureMax"),
                "temp": _temp_string(values),
                "precipitation": _precip_string(values),
                "humidity": _humidity_string(values),
            }
        )
        if len(normalized) >= max_days:
            break
    return normalized


def build_weather_brief_from_days(days: list[dict]) -> str:
    if not days:
        return ""
    day = days[0]
    return (
        f"{day.get('day_label', '—')} : {day.get('prevision', '—')} "
        f"({day.get('temp', '—')}, précip. {day.get('precipitation', '—')}, "
        f"humidité {day.get('humidity', '—')})"
    )


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        if tag in ("br", "p", "div", "h1", "h2", "h3", "li", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        if tag in ("p", "div", "h1", "h2", "h3", "li", "tr"):
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        text = data.strip()
        if text:
            self.parts.append(text + " ")


def html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    text = unescape("".join(parser.parts))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_mms_daily_excerpt(page_text: str) -> str:
    """Keep Situation générale + early 24h forecast lines only.

    Stops before max-temp / wind / sea / tides sections.
    """
    lower = page_text.lower()
    start = lower.find("situation générale")
    if start < 0:
        raise ValueError("Could not find 'Situation générale' on MMS bulletin")

    chunk = page_text[start:]
    stop_markers = (
        "La température maximale",
        "Le vent sera",
        "Mer agitée",
        "Marées hautes",
        "Marées basses",
        "Coucher du soleil",
        "Lever du soleil",
        "La pression atmosphérique",
    )
    end = len(chunk)
    for marker in stop_markers:
        idx = chunk.find(marker)
        if idx >= 0:
            end = min(end, idx)

    excerpt = chunk[:end].strip()
    # Drop section headings; keep only the forecast body as one line.
    excerpt = re.sub(
        r"(?i)situation\s+g[ée]n[ée]rale\s*:\s*",
        " ",
        excerpt,
    )
    excerpt = re.sub(
        r"(?i)pr[ée]visions\s+pour\s+les\s+prochaines\s+24\s+heures\s*:\s*",
        " ",
        excerpt,
    )
    excerpt = re.sub(r"\s+", " ", excerpt).strip()
    if not excerpt:
        raise ValueError("MMS daily excerpt was empty")
    return excerpt


def _clean_mms_value(value: str) -> str:
    value = re.sub(r"\s+", " ", (value or "")).strip(" .")
    value = value.replace("\xa0", " ")
    return value


def extract_mms_details(page_text: str) -> list[dict[str, str]]:
    """Parse tides / sun / pressure lines for bottom-of-post icons."""
    patterns = [
        ("high_tide", "🌊", "Marées hautes", r"(?i)mar[ée]es\s+hautes\s*:\s*(.+?)(?=\n|Mar[ée]es\s+basses|Coucher|Lever|La pression|$)"),
        ("low_tide", "🌊", "Marées basses", r"(?i)mar[ée]es\s+basses\s*:\s*(.+?)(?=\n|Coucher|Lever|La pression|$)"),
        ("sunset", "🌇", "Coucher du soleil", r"(?i)coucher\s+du\s+soleil\s*:\s*(.+?)(?=\n|Lever|La pression|$)"),
        ("sunrise", "🌅", "Lever du soleil", r"(?i)lever\s+du\s+soleil(?:\s*\([^)]*\))?\s*:\s*(.+?)(?=\n|La pression|$)"),
        (
            "pressure",
            "📉",
            "Pression",
            r"(?i)(?:la\s+)?pression\s+atmosph[ée]rique(?:\s+[àa]\s+\S+)?\s*:\s*(.+?)(?=\n|$)",
        ),
    ]
    details: list[dict[str, str]] = []
    for key, icon, label, pattern in patterns:
        match = re.search(pattern, page_text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        value = _clean_mms_value(match.group(1))
        if not value:
            continue
        # Compact tide wording: drop "demain" / "et", use "/"
        if key in ("high_tide", "low_tide"):
            value = re.sub(r"(?i)\s*et\s+demain\s*", " / ", value)
            value = re.sub(r"(?i)\bdemain\b\s*", "", value)
            value = re.sub(r"(?i)\s+et\s+", " / ", value)
            value = re.sub(r"\s*/\s*", " / ", value)
            value = re.sub(r"\s+", " ", value).strip(" /")
        if key == "pressure":
            # e.g. "1015 hectopascals" -> "1015 hPa"
            num = re.search(r"(\d{3,4})", value)
            if num:
                value = f"{num.group(1)} hPa"
            else:
                value = re.sub(r"(?i)hectopascals?", "hPa", value)
                value = re.sub(r"\s+", " ", value).strip()
        details.append(
            {
                "key": key,
                "icon": icon,
                "label": label,
                "value": value,
            }
        )
    return details


_FR_MONTH_NAME_TO_INDEX = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}


def _mms_condition_from_text(text: str) -> tuple[str, str]:
    """Pick today's condition + icon from MMS bulletin wording."""
    lower = (text or "").lower()
    checks = (
        ("orage", "Orage", "⛈️"),
        ("forte pluie", "Forte pluie", "🌧️"),
        ("averses", "Averses", "🌦️"),
        ("pluie", "Pluie", "🌧️"),
        ("bruine", "Bruine", "🌦️"),
        ("brouillard", "Brume", "🌫️"),
        ("brume", "Brume", "🌫️"),
        ("mi-couvert", "Mi-couvert", "⛅"),
        ("partiellement nuageux", "Partiellement nuageux", "⛅"),
        ("parfois nuageux", "Nuageux", "☁️"),
        ("nuageux", "Nuageux", "☁️"),
        ("couvert", "Couvert", "☁️"),
        ("beau temps", "Beau", "☀️"),
        ("essentiellement beau", "Beau", "☀️"),
        ("ensoleillé", "Ensoleillé", "☀️"),
        ("ensoleille", "Ensoleillé", "☀️"),
        (" beau", "Beau", "☀️"),
    )
    for needle, label, icon in checks:
        if needle in lower:
            return label, icon
    return "Variable", "⛅"


# Known new moon reference (UTC) for synodic-month phase estimate.
_NEW_MOON_REF = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
_SYNODIC_MONTH_DAYS = 29.530588853
_MOON_PHASES = (
    (0.0625, "Nouvelle lune", "🌑"),
    (0.1875, "Premier croissant", "🌒"),
    (0.3125, "Premier quartier", "🌓"),
    (0.4375, "Lune gibbeuse croissante", "🌔"),
    (0.5625, "Pleine lune", "🌕"),
    (0.6875, "Lune gibbeuse décroissante", "🌖"),
    (0.8125, "Dernier quartier", "🌗"),
    (0.9375, "Dernier croissant", "🌘"),
    (1.0001, "Nouvelle lune", "🌑"),
)


def moon_phase_for_date(dt: datetime) -> dict[str, Any]:
    """Approximate moon phase for a calendar date (Mauritius local day)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MAURITIUS_TZ)
    utc = dt.astimezone(timezone.utc)
    days = (utc - _NEW_MOON_REF).total_seconds() / 86400.0
    phase = (days % _SYNODIC_MONTH_DAYS) / _SYNODIC_MONTH_DAYS
    label, icon = "Nouvelle lune", "🌑"
    for edge, name, emoji in _MOON_PHASES:
        if phase < edge:
            label, icon = name, emoji
            break
    return {
        "moon_phase": label,
        "moon_icon": icon,
        "moon_illumination": round(abs(0.5 - abs(phase - 0.5)) * 2 * 100),
    }


def extract_mms_today_summary(
    page_text: str,
    excerpt: str = "",
    region: str = "Île Maurice",
) -> dict[str, Any]:
    """Today hero card from MMS figures (Maurice or Rodrigues)."""
    now = datetime.now(MAURITIUS_TZ)
    hero_date = now
    date_label = f"{_FR_WEEKDAYS[now.weekday()]} {now.day} {_FR_MONTHS[now.month - 1]}"

    date_match = re.search(
        r"(?i)émis\s+à\s+\S+\s+(\w+)\s+(\d{1,2})\s+(\w+)\s+(\d{4})",
        page_text or "",
    )
    if date_match:
        weekday_raw, day_raw, month_raw, year_raw = date_match.groups()
        month_idx = _FR_MONTH_NAME_TO_INDEX.get(month_raw.lower())
        try:
            day_i = int(day_raw)
            year_i = int(year_raw)
            if month_idx:
                hero_date = datetime(year_i, month_idx, day_i, 12, 0, tzinfo=MAURITIUS_TZ)
                date_label = f"{_FR_WEEKDAYS[hero_date.weekday()]} {hero_date.day} {_FR_MONTHS[hero_date.month - 1]}"
            else:
                date_label = f"{weekday_raw[:3].capitalize()} {day_i} {month_raw[:3].lower()}"
        except (TypeError, ValueError):
            pass

    temp_values: list[int] = []
    for a, b in re.findall(
        r"(?i)entre\s+(\d{1,2})\s+et\s+(\d{1,2})\s+degr",
        page_text or "",
    ):
        try:
            temp_values.extend([int(a), int(b)])
        except (TypeError, ValueError):
            continue

    temp_avg = None
    temp_display = "—"
    if temp_values:
        temp_avg = int(round(sum(temp_values) / len(temp_values)))
        temp_display = f"{temp_avg}°C"

    condition, icon = _mms_condition_from_text(excerpt or page_text or "")
    moon = moon_phase_for_date(hero_date)
    return {
        "region": region,
        "date_label": date_label,
        "condition": condition,
        "icon": icon,
        "temp_avg": temp_avg,
        "temp_display": temp_display,
        **moon,
    }


def _fetch_mms_page(url: str) -> str:
    response = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ImageCreatorWeather/1.0)"},
    )
    response.raise_for_status()
    return html_to_text(response.text)


def fetch_mms_bulletin() -> dict[str, Any]:
    page_text = _fetch_mms_page(MMS_BULLETIN_URL)
    excerpt = extract_mms_daily_excerpt(page_text)
    return {
        "mms_bulletin": excerpt,
        "mms_details": extract_mms_details(page_text),
        "mms_today": extract_mms_today_summary(page_text, excerpt, region="Île Maurice"),
        "mms_humidity_stations": extract_mms_station_humidity(page_text),
    }


def fetch_mms_rodrigues_bulletin() -> dict[str, Any]:
    """Official Rodrigues French bulletin from MMS."""
    page_text = _fetch_mms_page(MMS_RODRIGUES_BULLETIN_URL)
    try:
        excerpt = extract_mms_daily_excerpt(page_text)
    except ValueError:
        # Fallback: keep forecast body before tides/sun if heading differs slightly
        lower = page_text.lower()
        start = lower.find("prévisions pour les prochaines 24")
        if start < 0:
            start = 0
        chunk = page_text[start:]
        end = len(chunk)
        for marker in ("Marées hautes", "Coucher du soleil", "La pluviométrie"):
            idx = chunk.find(marker)
            if idx >= 0:
                end = min(end, idx)
        excerpt = re.sub(r"\s+", " ", chunk[:end]).strip()
    today = extract_mms_today_summary(page_text, excerpt, region="Rodrigues")
    return {
        "mms_bulletin_rodrigues": excerpt,
        "mms_today_rodrigues": today,
        "mms_humidity_stations": extract_mms_station_humidity(page_text),
    }


def fetch_weather_forecast() -> dict[str, Any]:
    now = time.time()
    cached = _weather_forecast_cache.get("payload")
    if cached and _weather_forecast_cache.get("expires_at", 0) > now:
        return cached

    result: dict[str, Any] = {
        "brief": "",
        "mms_bulletin": "",
        "mms_details": [],
        "mms_today": None,
        "days": [],
        "days_rodrigues": [],
        "error": None,
    }
    errors: list[str] = []

    humidity_stations: dict[str, int] = {}
    try:
        mms = fetch_mms_bulletin()
        result["mms_bulletin"] = mms.get("mms_bulletin") or ""
        result["mms_details"] = mms.get("mms_details") or []
        result["mms_today"] = mms.get("mms_today")
        humidity_stations = mms.get("mms_humidity_stations") or {}
    except Exception as exc:
        errors.append(f"MMS: {exc}")

    mms_rod_today: dict[str, Any] = {}
    try:
        mms_rod = fetch_mms_rodrigues_bulletin()
        mms_rod_today = mms_rod.get("mms_today_rodrigues") or {}
        result["mms_bulletin_rodrigues"] = mms_rod.get("mms_bulletin_rodrigues") or ""
        if not humidity_stations:
            humidity_stations = mms_rod.get("mms_humidity_stations") or {}
    except Exception as exc:
        errors.append(f"MMS Rodrigues: {exc}")

    result["mms_humidity_stations"] = humidity_stations
    mau_hum, mau_hum_disp = _humidity_for_region(humidity_stations, "Île Maurice")
    rod_hum, rod_hum_disp = _humidity_for_region(humidity_stations, "Rodrigues")

    mauritius_loc = os.environ.get("WEATHER_LOCATION") or DEFAULT_MAURITIUS_LOCATION
    rodrigues_loc = os.environ.get("WEATHER_LOCATION_RODRIGUES") or DEFAULT_RODRIGUES_LOCATION
    max_days = int(os.environ.get("WEATHER_FORECAST_DAYS", "5") or 5)

    day0: dict = {}
    day0_rod: dict = {}
    try:
        raw_days = fetch_tomorrow_weather_forecast(mauritius_loc)
        if not raw_days:
            errors.append("No daily forecast data returned")
        else:
            # Hero fallback uses today; 5-day widgets start tomorrow
            today_days = normalize_forecast_days(raw_days, max_days=1, start_from_tomorrow=False)
            day0 = today_days[0] if today_days else {}
            days = normalize_forecast_days(raw_days, max_days=max_days, start_from_tomorrow=True)
            if not days:
                errors.append("No daily forecast data returned")
            else:
                result["days"] = days
                result["brief"] = build_weather_brief_from_days(days)
    except Exception as exc:
        errors.append(str(exc))

    try:
        raw_rodrigues = fetch_tomorrow_weather_forecast(rodrigues_loc)
        if raw_rodrigues:
            today_rod = normalize_forecast_days(raw_rodrigues, max_days=1, start_from_tomorrow=False)
            day0_rod = today_rod[0] if today_rod else {}
            result["days_rodrigues"] = normalize_forecast_days(
                raw_rodrigues, max_days=max_days, start_from_tomorrow=True
            )
    except Exception as exc:
        errors.append(f"Rodrigues: {exc}")

    # Today hero: Maurice (left) + Rodrigues (right) — prefer official MMS bulletins
    today = result.get("mms_today") if isinstance(result.get("mms_today"), dict) else {}

    mauritius = today_card_from_day(day0, "Île Maurice")
    if today.get("temp_avg") is not None:
        mauritius["temp_avg"] = today.get("temp_avg")
        mauritius["temp_display"] = today.get("temp_display") or mauritius["temp_display"]
    if today.get("icon"):
        mauritius["icon"] = today["icon"]
    if today.get("condition") and today.get("condition") != "Variable":
        mauritius["condition"] = today["condition"]
    elif day0.get("prevision"):
        mauritius["condition"] = day0.get("prevision")
    if mau_hum is not None:
        mauritius["humidity"] = mau_hum
        mauritius["humidity_display"] = mau_hum_disp

    rodrigues = today_card_from_day(day0_rod, "Rodrigues")
    if mms_rod_today.get("temp_avg") is not None:
        rodrigues["temp_avg"] = mms_rod_today.get("temp_avg")
        rodrigues["temp_display"] = mms_rod_today.get("temp_display") or rodrigues["temp_display"]
    if mms_rod_today.get("icon"):
        rodrigues["icon"] = mms_rod_today["icon"]
    if mms_rod_today.get("condition") and mms_rod_today.get("condition") != "Variable":
        rodrigues["condition"] = mms_rod_today["condition"]
    if rod_hum is not None:
        rodrigues["humidity"] = rod_hum
        rodrigues["humidity_display"] = rod_hum_disp

    today.update(
        {
            "region": "Île Maurice",
            "icon": mauritius.get("icon"),
            "condition": mauritius.get("condition"),
            "temp_avg": mauritius.get("temp_avg"),
            "temp_display": mauritius.get("temp_display"),
            "mauritius": mauritius,
            "rodrigues": rodrigues,
        }
    )
    if day0.get("day_label") and not today.get("date_label"):
        today["date_label"] = day0.get("day_label")
    if not today.get("moon_icon"):
        today.update(moon_phase_for_date(datetime.now(MAURITIUS_TZ)))
    result["mms_today"] = today

    if errors and not result["mms_bulletin"] and not result["days"]:
        result["error"] = "; ".join(errors)
        return result

    if errors:
        result["error"] = "; ".join(errors)

    # Prefer MMS bulletin text for the Post title line.
    if result["mms_bulletin"] or result["days"]:
        _weather_forecast_cache["payload"] = result
        _weather_forecast_cache["expires_at"] = now + _CACHE_TTL_SECONDS
    return result
