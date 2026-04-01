import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
    ("Rahu", swe.TRUE_NODE),
]

ZODIAC = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

DashaYears = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

DashaOrder = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]


@dataclass
class GeoResult:
    latitude: float
    longitude: float
    timezone: str
    display_name: str


def decimal_to_dms(value: float) -> str:
    degrees = int(value)
    minutes_full = abs((value - degrees) * 60)
    minutes = int(minutes_full)
    seconds = int(round((minutes_full - minutes) * 60))
    return f"{degrees}°{minutes:02d}'{seconds:02d}\""


def sign_index(longitude: float) -> int:
    return int(math.floor(longitude / 30.0)) % 12


def sign_name(longitude: float) -> str:
    return ZODIAC[sign_index(longitude)]


def degree_in_sign(longitude: float) -> float:
    return longitude % 30.0


def house_from_longitudes(asc_long: float, body_long: float) -> int:
    diff = (body_long - asc_long) % 360.0
    return int(diff // 30.0) + 1


def navamsa_sign_index(longitude: float) -> int:
    sign = sign_index(longitude)
    part = int((longitude % 30.0) // (30.0 / 9.0))
    movable = {0, 3, 6, 9}
    fixed = {1, 4, 7, 10}
    dual = {2, 5, 8, 11}
    if sign in movable:
        start = sign
    elif sign in fixed:
        start = (sign + 8) % 12
    else:
        start = (sign + 4) % 12
    return (start + part) % 12


def format_planet_label(name: str, retrograde: bool) -> str:
    return f"{name}{' (R)' if retrograde else ''}"


def geocode_place(place: str) -> GeoResult:
    geolocator = Nominatim(user_agent="ipant_future_app")
    location = geolocator.geocode(place, exactly_one=True, timeout=20)
    if not location:
        raise ValueError("Could not find the birthplace. Please try a more specific format like 'Pune, Maharashtra, India'.")

    tf = TimezoneFinder()
    timezone = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    if not timezone:
        raise ValueError("Could not determine timezone for this birthplace.")

    return GeoResult(
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=timezone,
        display_name=location.address,
    )


def parse_birth_datetime(dob: str, tob: str, timezone_name: str) -> Tuple[datetime, datetime]:
    naive = datetime.strptime(f"{dob} {tob}", "%d/%m/%Y %H:%M")
    tz = pytz.timezone(timezone_name)
    localized = tz.localize(naive)
    utc_dt = localized.astimezone(pytz.UTC)
    return localized, utc_dt


def julian_day(utc_dt: datetime) -> float:
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600,
        swe.GREG_CAL,
    )


def sidereal_longitude(jd_ut: float, body: int) -> Tuple[float, bool]:
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    result = swe.calc_ut(jd_ut, body, flags)[0]
    longitude = result[0] % 360
    retrograde = result[3] < 0
    return longitude, retrograde


def get_ascendant(jd_ut: float, latitude: float, longitude: float) -> float:
    houses, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b'P', swe.FLG_SIDEREAL)
    return ascmc[0] % 360


def get_nakshatra(moon_long: float) -> Dict[str, str]:
    segment = 360 / 27
    idx = int(moon_long // segment)
    nak = NAKSHATRAS[idx]
    pada = int((moon_long % segment) // (segment / 4)) + 1
    ruler = DashaOrder[idx % 9]
    return {"name": nak, "pada": str(pada), "ruler": ruler}


def get_vimshottari(moon_long: float, birth_dt_local: datetime) -> Dict[str, List[Dict[str, str]]]:
    segment = 360 / 27
    idx = int(moon_long // segment)
    start_lord = DashaOrder[idx % 9]
    progress_in_nak = (moon_long % segment) / segment
    balance_years = DashaYears[start_lord] * (1 - progress_in_nak)

    sequence = []
    order_start = DashaOrder.index(start_lord)
    current = birth_dt_local
    first_end = current.replace(year=current.year)  # keep type
    # add first partial mahadasha
    sequence.append({
        "lord": start_lord,
        "start": current.strftime("%d %b %Y"),
        "end": add_years_fraction(current, balance_years).strftime("%d %b %Y"),
        "years": f"{balance_years:.2f}",
        "type": "balance"
    })
    current = add_years_fraction(current, balance_years)
    for i in range(1, 8):
        lord = DashaOrder[(order_start + i) % len(DashaOrder)]
        years = DashaYears[lord]
        end = add_years_fraction(current, years)
        sequence.append({
            "lord": lord,
            "start": current.strftime("%d %b %Y"),
            "end": end.strftime("%d %b %Y"),
            "years": str(years),
            "type": "full"
        })
        current = end
    return {"current_balance_lord": start_lord, "sequence": sequence}


def add_years_fraction(dt: datetime, years: float) -> datetime:
    days = years * 365.2425
    return dt + timedelta_days(days)


def timedelta_days(days: float):
    from datetime import timedelta
    seconds = days * 24 * 3600
    return timedelta(seconds=seconds)


def north_chart_map(asc_sign_idx: int, placements_by_house: Dict[int, List[str]]) -> Dict[str, Dict[str, str]]:
    sign_in_house = {house: ZODIAC[(asc_sign_idx + house - 1) % 12] for house in range(1, 13)}
    out = {}
    for house in range(1, 13):
        out[str(house)] = {
            "house": str(house),
            "sign": sign_in_house[house],
            "planets": ", ".join(placements_by_house.get(house, [])),
        }
    return out


def build_full_chart(name: str, dob: str, tob: str, place: str) -> Dict:
    geo = geocode_place(place)
    local_dt, utc_dt = parse_birth_datetime(dob, tob, geo.timezone)
    jd_ut = julian_day(utc_dt)

    asc_long = get_ascendant(jd_ut, geo.latitude, geo.longitude)
    asc_sign_idx = sign_index(asc_long)

    planets_detail = {}
    d1_houses = {i: [] for i in range(1, 13)}
    d9_houses = {i: [] for i in range(1, 13)}

    moon_long = None

    for planet_name, planet_code in PLANETS:
        longitude, retrograde = sidereal_longitude(jd_ut, planet_code)
        house = house_from_longitudes(asc_long, longitude)
        d9_sign_idx = navamsa_sign_index(longitude)
        d9_house = ((d9_sign_idx - asc_sign_idx) % 12) + 1

        if planet_name == "Rahu":
            ketu_long = (longitude + 180.0) % 360
            ketu_house = house_from_longitudes(asc_long, ketu_long)
            ketu_d9_idx = navamsa_sign_index(ketu_long)
            ketu_d9_house = ((ketu_d9_idx - asc_sign_idx) % 12) + 1

            planets_detail["Rahu"] = {
                "sign": sign_name(longitude),
                "degree": round(degree_in_sign(longitude), 2),
                "house": house,
                "longitude": round(longitude, 4),
                "retrograde": retrograde,
                "navamsa_sign": ZODIAC[d9_sign_idx],
                "navamsa_house": d9_house,
            }
            planets_detail["Ketu"] = {
                "sign": sign_name(ketu_long),
                "degree": round(degree_in_sign(ketu_long), 2),
                "house": ketu_house,
                "longitude": round(ketu_long, 4),
                "retrograde": retrograde,
                "navamsa_sign": ZODIAC[ketu_d9_idx],
                "navamsa_house": ketu_d9_house,
            }
            d1_houses[house].append(format_planet_label("Rahu", retrograde))
            d1_houses[ketu_house].append(format_planet_label("Ketu", retrograde))
            d9_houses[d9_house].append(format_planet_label("Rahu", retrograde))
            d9_houses[ketu_d9_house].append(format_planet_label("Ketu", retrograde))
            continue

        planets_detail[planet_name] = {
            "sign": sign_name(longitude),
            "degree": round(degree_in_sign(longitude), 2),
            "house": house,
            "longitude": round(longitude, 4),
            "retrograde": retrograde,
            "navamsa_sign": ZODIAC[d9_sign_idx],
            "navamsa_house": d9_house,
        }
        d1_houses[house].append(format_planet_label(planet_name, retrograde))
        d9_houses[d9_house].append(format_planet_label(planet_name, retrograde))
        if planet_name == "Moon":
            moon_long = longitude

    if moon_long is None:
        raise ValueError("Moon longitude could not be calculated.")

    nak = get_nakshatra(moon_long)
    vim = get_vimshottari(moon_long, local_dt)

    chart = {
        "name": name,
        "birth_details": {
            "date_of_birth": dob,
            "time_of_birth": tob,
            "place_of_birth": place,
            "resolved_place": geo.display_name,
            "timezone": geo.timezone,
            "latitude": round(geo.latitude, 6),
            "longitude": round(geo.longitude, 6),
            "local_datetime": local_dt.strftime("%d %b %Y, %I:%M %p"),
            "utc_datetime": utc_dt.strftime("%d %b %Y, %I:%M %p UTC"),
        },
        "core": {
            "lagna_sign": sign_name(asc_long),
            "lagna_degree": round(degree_in_sign(asc_long), 2),
            "moon_sign": sign_name(moon_long),
            "sun_sign": planets_detail["Sun"]["sign"],
            "nakshatra": nak["name"],
            "pada": nak["pada"],
            "nakshatra_ruler": nak["ruler"],
        },
        "planets": planets_detail,
        "rasi_d1": north_chart_map(asc_sign_idx, d1_houses),
        "navamsa_d9": north_chart_map(asc_sign_idx, d9_houses),
        "vimshottari": vim,
        "summary": build_rule_based_summary(sign_name(asc_long), sign_name(moon_long), planets_detail),
    }
    return chart


def build_rule_based_summary(lagna: str, moon: str, planets: Dict[str, Dict]) -> Dict[str, str]:
    career_notes = []
    relationship_notes = []
    wealth_notes = []

    if planets["Saturn"]["house"] == 10 or planets["Saturn"]["house"] == 11:
        career_notes.append("Saturn supports durable career growth through disciplined effort and delayed but steady rewards.")
    if planets["Mars"]["house"] in (1, 3, 10):
        career_notes.append("Mars adds initiative, courage, and a push toward leadership or independent work.")
    if planets["Jupiter"]["house"] in (2, 5, 9, 11):
        wealth_notes.append("Jupiter strengthens support for learning, advisory roles, and long-range wealth building.")
    if planets["Venus"]["house"] in (1, 4, 7, 10):
        relationship_notes.append("Venus supports charm, aesthetics, and relationship awareness in public life.")
    if planets["Rahu"]["house"] in (10, 11):
        career_notes.append("Rahu can bring unconventional opportunities, foreign links, and sudden career jumps.")
    if planets["Moon"]["house"] in (1, 5, 9):
        relationship_notes.append("Moon in a trinal house increases emotional responsiveness and intuitive judgment.")

    return {
        "personality": f"Lagna in {lagna} and Moon in {moon} create a blend of outward style and inner emotional pattern that shapes decision-making strongly.",
        "career": " ".join(career_notes) or "Career growth is best when your work combines discipline, visibility, and real responsibility.",
        "relationships": " ".join(relationship_notes) or "Relationships improve when emotional clarity and steady communication stay stronger than impulse.",
        "wealth": " ".join(wealth_notes) or "Wealth is most stable when built through consistent planning instead of quick speculation.",
    }


def chart_prompt_context(chart: Dict) -> str:
    core = chart.get("core", {})
    birth = chart.get("birth_details", {})
    summary = chart.get("summary", {})
    planets = chart.get("planets", {})

    planet_lines = []
    for name, info in planets.items():
        planet_lines.append(
            f"{name}: {info['sign']} {info['degree']}°, House {info['house']}, Navamsa {info['navamsa_sign']} House {info['navamsa_house']}"
        )

    lines = [
        f"Name: {chart.get('name', 'User')}",
        f"Birth: {birth.get('date_of_birth')} {birth.get('time_of_birth')} at {birth.get('resolved_place', birth.get('place_of_birth', ''))}",
        f"Lagna: {core.get('lagna_sign')} {core.get('lagna_degree')}°",
        f"Moon sign: {core.get('moon_sign')}",
        f"Sun sign: {core.get('sun_sign')}",
        f"Nakshatra: {core.get('nakshatra')} Pada {core.get('pada')} ruled by {core.get('nakshatra_ruler')}",
        "Planetary positions:",
        *planet_lines,
        "Rule-based chart themes:",
        f"Personality: {summary.get('personality', '')}",
        f"Career: {summary.get('career', '')}",
        f"Relationships: {summary.get('relationships', '')}",
        f"Wealth: {summary.get('wealth', '')}",
    ]
    return "\n".join(lines)
