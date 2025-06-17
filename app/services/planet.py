# astro_calculator.py
from datetime import datetime

import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from skyfield.api import load, Topos


class PlanetSignCalculator:
    """Calcula signo e grau de qualquer planeta usando Skyfield."""

    _ZODIAC_SIGNS = [
        "Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem",
        "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes",
    ]

    def __init__(self) -> None:
        # recursos “pesados” carregados só uma vez
        self._geolocator = Nominatim(user_agent="astro_api")
        self._tz_finder = TimezoneFinder()
        self._eph = load("de421.bsp")          # efemérides JPL (grátis)
        self._ts = load.timescale()
        self._earth = self._eph["earth"]

    # ---------- API pública ----------

    async def planet_sign(
        self,
        birth_date: str,      # "YYYY-MM-DD"
        birth_time: str,      # "HH:MM"
        birth_place: str,     # "Cidade, País"
        planet_name: str,     # "Sun", "Moon", "Mars"...
    ) -> tuple[str, float]:
        """Retorna (signo, grau) do planeta na data/hora/local informados."""

        lat, lon, dt_utc = await self._local_to_utc(birth_date, birth_time, birth_place)
        longitude = self._planet_longitude(dt_utc, lat, lon, planet_name)
        signo = self._sign_from_degree(longitude)
        grau = longitude % 30
        return signo, grau

    # ---------- utilidades internas ----------

    async def _local_to_utc(self, date_str: str, time_str: str, place: str):
        """Resolve lat/lon e converte data-hora local → UTC."""
        # Suporta tanto 'YYYY-MM-DD' quanto 'DD/MM/YYYY'
        try:
            dt_local = datetime.fromisoformat(f"{date_str}T{time_str}")
        except ValueError:
            dt_local = datetime.strptime(f"{date_str}T{time_str}", "%d/%m/%YT%H:%M")

        location = self._geolocator.geocode(place)
        if not location:
            raise ValueError(f"Local não encontrado: {place}")

        tz_str = self._tz_finder.timezone_at(lng=location.longitude, lat=location.latitude) or "UTC"
        tz = pytz.timezone(tz_str)
        dt_utc = tz.localize(dt_local).astimezone(pytz.utc)
        return location.latitude, location.longitude, dt_utc

    def _planet_longitude(self, dt_utc, lat, lon, planet_name):
        planet_map = {
            "SUN": "SUN",
            "MOON": "MOON",
            "MERCURY": "MERCURY",
            "VENUS": "VENUS",
            "EARTH": "EARTH",
            "MARS": "MARS",
            "JUPITER": "JUPITER_BARYCENTER",
            "SATURN": "SATURN_BARYCENTER",
            "URANUS": "URANUS_BARYCENTER",
            "NEPTUNE": "NEPTUNE_BARYCENTER",
            "PLUTO": "PLUTO_BARYCENTER",
        }
        planet_key = planet_name.strip().upper()
        skyfield_key = planet_map.get(planet_key)
        if not skyfield_key or skyfield_key not in self._eph:
            raise ValueError(f"Planeta inválido: {planet_name}")

        planet = self._eph[skyfield_key]

        t = self._ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute)
        observer = self._earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
        ecliptic = observer.at(t).observe(planet).ecliptic_latlon()
        return ecliptic[1].degrees


    @staticmethod
    def _sign_from_degree( degree: float) -> str:
        """Mapeia 0-360° para o nome do signo."""
        return PlanetSignCalculator._ZODIAC_SIGNS[int(degree // 30) % 12]
