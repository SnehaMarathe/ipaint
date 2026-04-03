from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Tuple
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_ABBR = {"Aries":"Ar","Taurus":"Ta","Gemini":"Ge","Cancer":"Cn","Leo":"Le","Virgo":"Vi","Libra":"Li","Scorpio":"Sc","Sagittarius":"Sg","Capricorn":"Cp","Aquarius":"Aq","Pisces":"Pi"}
NAKSHATRAS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
NAKSHATRA_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury","Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury","Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
DASHA_SEQUENCE = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
PLANETS = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN,"Rahu":swe.MEAN_NODE}

def set_sidereal() -> None:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

def norm_deg(value: float) -> float:
    return value % 360.0

def sign_index(lon: float) -> int:
    return int(norm_deg(lon) // 30)

def sign_name(lon: float) -> str:
    return SIGNS[sign_index(lon)]

def degree_in_sign(lon: float) -> float:
    return round(norm_deg(lon) % 30, 2)

def resolve_place(place: str) -> Tuple[str, float, float, str]:
    geolocator = Nominatim(user_agent="ipant_future")
    location = geolocator.geocode(place, exactly_one=True)
    if not location:
        raise ValueError(f"Could not resolve birthplace: {place}")
    timezone_name = TimezoneFinder().timezone_at(lng=location.longitude, lat=location.latitude)
    if not timezone_name:
        raise ValueError(f"Could not determine timezone for: {place}")
    return location.address or place, float(location.latitude), float(location.longitude), timezone_name

def parse_local_dt(date_str: str, time_str: str, timezone_name: str) -> datetime:
    naive = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
    return pytz.timezone(timezone_name).localize(naive)

def to_jd_ut(local_dt: datetime) -> float:
    utc_dt = local_dt.astimezone(pytz.utc)
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)

def house_from_lagna(planet_lon: float, lagna_lon: float) -> int:
    return ((sign_index(planet_lon) - sign_index(lagna_lon)) % 12) + 1

def navamsa_sign(lon: float) -> str:
    s_idx = sign_index(lon)
    deg = norm_deg(lon) % 30
    part = int(deg / (30 / 9))
    if s_idx in [0,3,6,9]:
        start = s_idx
    elif s_idx in [1,4,7,10]:
        start = (s_idx + 8) % 12
    else:
        start = (s_idx + 4) % 12
    return SIGNS[(start + part) % 12]

def navamsa_house(lon: float, lagna_lon: float) -> int:
    return ((SIGNS.index(navamsa_sign(lon)) - SIGNS.index(navamsa_sign(lagna_lon))) % 12) + 1

def nakshatra_info(lon: float):
    span = 360 / 27
    idx = int(norm_deg(lon) // span)
    within = norm_deg(lon) - (idx * span)
    pada = int(within // (span / 4)) + 1
    lord = NAKSHATRA_LORDS[idx]
    frac_elapsed = within / span
    return NAKSHATRAS[idx], pada, lord, frac_elapsed

def format_date(d: datetime) -> str:
    return d.strftime("%d %b %Y")

def vimshottari_from_moon(moon_lon: float, birth_dt: datetime) -> Dict[str, object]:
    nak, pada, lord, frac_elapsed = nakshatra_info(moon_lon)
    remaining_years = DASHA_YEARS[lord] * (1 - frac_elapsed)
    sequence = []
    seq_idx = DASHA_SEQUENCE.index(lord)
    start = birth_dt
    end = birth_dt + timedelta(days=remaining_years * 365.2425)
    sequence.append({"lord": lord, "start": format_date(start), "end": format_date(end), "years": round(remaining_years, 2)})
    start = end
    for i in range(1, 9):
        dlord = DASHA_SEQUENCE[(seq_idx + i) % 9]
        years = DASHA_YEARS[dlord]
        end = start + timedelta(days=years * 365.2425)
        sequence.append({"lord": dlord, "start": format_date(start), "end": format_date(end), "years": years})
        start = end
    return {"birth_nakshatra": nak, "current_balance_lord": lord, "sequence": sequence}

def build_chart_map(lagna_lon: float, placements: Dict[str, Dict[str, object]], mode: str = "d1") -> Dict[str, Dict[str, str]]:
    result = {}
    base_sign_idx = sign_index(lagna_lon) if mode == "d1" else SIGNS.index(navamsa_sign(lagna_lon))
    for house in range(1, 13):
        result[str(house)] = {"sign": SIGN_ABBR[SIGNS[(base_sign_idx + house - 1) % 12]], "planets": ""}
    grouped = {i: [] for i in range(1, 13)}
    for planet, info in placements.items():
        h = info["house"] if mode == "d1" else info["navamsa_house"]
        grouped[h].append(planet)
    for house in range(1, 13):
        result[str(house)]["planets"] = " ".join(grouped[house])
    return result

def compute_placements(jd_ut: float, lagna_lon: float) -> Dict[str, Dict[str, object]]:
    placements = {}
    for name, body in PLANETS.items():
        data, _ = swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        lon = norm_deg(data[0]); speed = data[3]
        placements[name] = {
            "longitude": round(lon, 6),
            "sign": sign_name(lon),
            "degree": degree_in_sign(lon),
            "house": house_from_lagna(lon, lagna_lon),
            "retrograde": bool(speed < 0),
            "navamsa_sign": navamsa_sign(lon),
            "navamsa_house": navamsa_house(lon, lagna_lon),
        }
    ketu_lon = norm_deg(placements["Rahu"]["longitude"] + 180)
    placements["Ketu"] = {
        "longitude": round(ketu_lon, 6),
        "sign": sign_name(ketu_lon),
        "degree": degree_in_sign(ketu_lon),
        "house": house_from_lagna(ketu_lon, lagna_lon),
        "retrograde": placements["Rahu"]["retrograde"],
        "navamsa_sign": navamsa_sign(ketu_lon),
        "navamsa_house": navamsa_house(ketu_lon, lagna_lon),
    }
    return placements

def build_chart(name: str, date_of_birth: str, time_of_birth: str, place_of_birth: str) -> Dict[str, object]:
    set_sidereal()
    resolved_place, latitude, longitude, timezone_name = resolve_place(place_of_birth)
    local_dt = parse_local_dt(date_of_birth, time_of_birth, timezone_name)
    jd_ut = to_jd_ut(local_dt)
    cusps, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b'W', swe.FLG_SIDEREAL)
    lagna_lon = norm_deg(ascmc[0])
    placements = compute_placements(jd_ut, lagna_lon)
    moon_lon = placements["Moon"]["longitude"]
    moon_nak, moon_pada, _, _ = nakshatra_info(moon_lon)
    return {
        "name": name,
        "birth_details": {
            "date_of_birth": date_of_birth,
            "time_of_birth": time_of_birth,
            "place_of_birth": place_of_birth,
            "resolved_place": resolved_place,
            "timezone": timezone_name,
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
        },
        "core": {
            "lagna_sign": sign_name(lagna_lon),
            "lagna_degree": degree_in_sign(lagna_lon),
            "moon_sign": placements["Moon"]["sign"],
            "sun_sign": placements["Sun"]["sign"],
            "nakshatra": moon_nak,
            "pada": moon_pada,
        },
        "planets": placements,
        "rasi_d1": build_chart_map(lagna_lon, placements, "d1"),
        "navamsa_d9": build_chart_map(lagna_lon, placements, "d9"),
        "vimshottari": vimshottari_from_moon(moon_lon, local_dt),
    }
