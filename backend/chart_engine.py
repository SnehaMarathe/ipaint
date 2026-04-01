from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from math import floor
from typing import Dict, List, Tuple

import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


# ----------------------------
# Constants
# ----------------------------

SIGNS = [
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

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Ketu": swe.MEAN_NODE,  # computed as Rahu + 180
}


# ----------------------------
# Data classes
# ----------------------------

@dataclass
class GeoResult:
    latitude: float
    longitude: float
    timezone: str
    resolved_place: str


@dataclass
class PlanetPosition:
    name: str
    longitude: float
    sign: str
    sign_index: int
    degree_in_sign: float
    house: int
    retrograde: bool


# ----------------------------
# Helpers
# ----------------------------

def normalize_deg(value: float) -> float:
    return value % 360.0


def sign_index_from_longitude(lon: float) -> int:
    return int(normalize_deg(lon) // 30)


def sign_name_from_longitude(lon: float) -> str:
    return SIGNS[sign_index_from_longitude(lon)]


def degree_in_sign(lon: float) -> float:
    return normalize_deg(lon) % 30


def house_from_lagna(planet_lon: float, lagna_lon: float) -> int:
    lagna_sign = sign_index_from_longitude(lagna_lon)
    planet_sign = sign_index_from_longitude(planet_lon)
    return ((planet_sign - lagna_sign) % 12) + 1


def navamsa_sign_index(lon: float) -> int:
    sign_index = sign_index_from_longitude(lon)
    deg = degree_in_sign(lon)
    navamsa_part = int(deg / (30 / 9))  # 0..8

    # movable/fixed/dual rule
    if sign_index in [0, 3, 6, 9]:  # movable
        start = sign_index
    elif sign_index in [1, 4, 7, 10]:  # fixed
        start = (sign_index + 8) % 12
    else:  # dual
        start = (sign_index + 4) % 12

    return (start + navamsa_part) % 12


def nakshatra_details(lon: float) -> Dict[str, object]:
    span = 360 / 27
    idx = int(normalize_deg(lon) // span)
    within = normalize_deg(lon) - (idx * span)
    pada = int(within // (span / 4)) + 1
    return {
        "nakshatra": NAKSHATRAS[idx],
        "nakshatra_index": idx,
        "pada": pada,
        "lord": NAKSHATRA_LORDS[idx],
        "offset_within_nakshatra_deg": within,
        "fraction_elapsed": within / span,
        "fraction_remaining": 1 - (within / span),
    }


def geocode_birth_place(place: str) -> GeoResult:
    geolocator = Nominatim(user_agent="ipant_future_astrology_engine")
    location = geolocator.geocode(place, exactly_one=True, addressdetails=False)
    if not location:
        raise ValueError(f"Could not geocode place: {place}")

    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    if not tz_name:
        raise ValueError(f"Could not resolve timezone for: {place}")

    return GeoResult(
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=tz_name,
        resolved_place=location.address or place,
    )


def parse_birth_datetime_local(date_of_birth: str, time_of_birth: str, timezone_name: str) -> datetime:
    naive = datetime.strptime(f"{date_of_birth} {time_of_birth}", "%Y-%m-%d %H:%M")
    tz = pytz.timezone(timezone_name)
    return tz.localize(naive)


def localized_to_julian_ut(local_dt: datetime) -> float:
    utc_dt = local_dt.astimezone(pytz.utc)
    decimal_hours = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hours)


def set_sidereal_mode() -> None:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


# ----------------------------
# Core calculations
# ----------------------------

def compute_planet_positions(jd_ut: float, lagna_lon: float) -> List[PlanetPosition]:
    positions: List[PlanetPosition] = []

    for name, body in PLANETS.items():
        if name == "Ketu":
            continue

        data, retflag = swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        lon = normalize_deg(data[0])
        speed = data[3]
        positions.append(
            PlanetPosition(
                name=name,
                longitude=lon,
                sign=sign_name_from_longitude(lon),
                sign_index=sign_index_from_longitude(lon),
                degree_in_sign=degree_in_sign(lon),
                house=house_from_lagna(lon, lagna_lon),
                retrograde=(speed < 0),
            )
        )

    # Ketu is opposite Rahu
    rahu = next(p for p in positions if p.name == "Rahu")
    ketu_lon = normalize_deg(rahu.longitude + 180.0)
    positions.append(
        PlanetPosition(
            name="Ketu",
            longitude=ketu_lon,
            sign=sign_name_from_longitude(ketu_lon),
            sign_index=sign_index_from_longitude(ketu_lon),
            degree_in_sign=degree_in_sign(ketu_lon),
            house=house_from_lagna(ketu_lon, lagna_lon),
            retrograde=rahu.retrograde,
        )
    )
    return positions


def compute_lagna_and_houses(jd_ut: float, latitude: float, longitude: float) -> Tuple[float, List[float]]:
    cusps, ascmc = swe.houses_ex(
        jd_ut,
        latitude,
        longitude,
        b'W',  # whole sign houses for stable Vedic mapping
        swe.FLG_SIDEREAL,
    )
    lagna_lon = normalize_deg(ascmc[0])
    return lagna_lon, list(cusps)


def compute_vimshottari_from_moon(moon_lon: float) -> Dict[str, object]:
    details = nakshatra_details(moon_lon)
    starting_lord = details["lord"]
    fraction_remaining = details["fraction_remaining"]

    seq_index = DASHA_SEQUENCE.index(starting_lord)
    first_years_total = DASHA_YEARS[starting_lord]
    first_years_remaining = round(first_years_total * fraction_remaining, 2)

    sequence = []
    for i in range(9):
        lord = DASHA_SEQUENCE[(seq_index + i) % 9]
        years = DASHA_YEARS[lord]
        if i == 0:
            years = first_years_remaining
        sequence.append({"lord": lord, "years": years})

    return {
        "birth_nakshatra": details["nakshatra"],
        "birth_nakshatra_lord": starting_lord,
        "mahadasha_sequence_from_birth": sequence,
        "current_mahadasha_at_birth": starting_lord,
        "remaining_years_in_birth_mahadasha": first_years_remaining,
    }


def north_indian_house_map(lagna_lon: float, planets: List[PlanetPosition]) -> Dict[str, object]:
    lagna_sign_idx = sign_index_from_longitude(lagna_lon)
    houses = {}

    for house_num in range(1, 13):
        sign_idx = (lagna_sign_idx + house_num - 1) % 12
        houses[str(house_num)] = {
            "sign": SIGNS[sign_idx],
            "planets": [p.name for p in planets if p.house == house_num],
        }
    return houses


def d9_map(planets: List[PlanetPosition], lagna_lon: float) -> Dict[str, object]:
    lagna_d9_sign_idx = navamsa_sign_index(lagna_lon)
    houses = {}

    def d9_house_for_longitude(lon: float) -> int:
        sign_idx = navamsa_sign_index(lon)
        return ((sign_idx - lagna_d9_sign_idx) % 12) + 1

    for house_num in range(1, 13):
        sign_idx = (lagna_d9_sign_idx + house_num - 1) % 12
        houses[str(house_num)] = {
            "sign": SIGNS[sign_idx],
            "planets": [p.name for p in planets if d9_house_for_longitude(p.longitude) == house_num],
        }
    return houses


def build_chart(date_of_birth: str, time_of_birth: str, birth_place: str) -> Dict[str, object]:
    set_sidereal_mode()
    geo = geocode_birth_place(birth_place)
    local_dt = parse_birth_datetime_local(date_of_birth, time_of_birth, geo.timezone)
    jd_ut = localized_to_julian_ut(local_dt)
    lagna_lon, _ = compute_lagna_and_houses(jd_ut, geo.latitude, geo.longitude)
    planets = compute_planet_positions(jd_ut, lagna_lon)

    moon = next(p for p in planets if p.name == "Moon")
    sun = next(p for p in planets if p.name == "Sun")

    d1_houses = north_indian_house_map(lagna_lon, planets)
    d9_houses = d9_map(planets, lagna_lon)
    moon_nak = nakshatra_details(moon.longitude)
    dasha = compute_vimshottari_from_moon(moon.longitude)

    return {
        "input": {
            "date_of_birth": date_of_birth,
            "time_of_birth": time_of_birth,
            "birth_place": birth_place,
            "resolved_place": geo.resolved_place,
            "timezone": geo.timezone,
            "latitude": round(geo.latitude, 6),
            "longitude": round(geo.longitude, 6),
            "julian_day_ut": round(jd_ut, 8),
        },
        "summary_facts": {
            "lagna_sign": sign_name_from_longitude(lagna_lon),
            "lagna_degree": round(degree_in_sign(lagna_lon), 4),
            "moon_sign": moon.sign,
            "sun_sign": sun.sign,
            "nakshatra": moon_nak["nakshatra"],
            "nakshatra_pada": moon_nak["pada"],
        },
        "lagna_longitude": round(lagna_lon, 8),
        "planets": [asdict(p) for p in planets],
        "d1": {
            "chart_type": "Rasi",
            "houses": d1_houses,
        },
        "d9": {
            "chart_type": "Navamsha",
            "houses": d9_houses,
        },
        "vimshottari": dasha,
    }
