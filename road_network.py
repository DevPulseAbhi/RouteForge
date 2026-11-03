"""Real OpenStreetMap network retrieval and safe route preparation."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from math import asin, cos, hypot, radians, sin, sqrt
from pathlib import Path
import re
from time import sleep
from typing import Any

import networkx as nx

try:
    import osmnx as ox
except Exception as exc:  # Optional for offline algorithm tests.
    ox = None
    _OSMNX_IMPORT_ERROR = exc
else:
    _OSMNX_IMPORT_ERROR = None


DEFAULT_RADIUS_KM = 60
NETWORK_PADDING_METRES = 2500
CACHE_DIRECTORY = Path(__file__).resolve().parent / "cache" / "graphs"


def _great_circle_km(start: tuple[float, float], end: tuple[float, float]) -> float:
    latitude_1, longitude_1 = map(radians, start)
    latitude_2, longitude_2 = map(radians, end)
    delta_latitude = latitude_2 - latitude_1
    delta_longitude = longitude_2 - longitude_1
    value = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude_1) * cos(latitude_2) * sin(delta_longitude / 2) ** 2
    )
    return 6371.0088 * 2 * asin(sqrt(value))


def route_bbox(
    start: tuple[float, float],
    destination: tuple[float, float],
    padding_degrees: float,
) -> tuple[float, float, float, float]:
    """Return an OSMnx bbox as (west, south, east, north)."""
    if padding_degrees <= 0:
        raise ValueError("Network padding must be positive.")
    start_latitude, start_longitude = start
    end_latitude, end_longitude = destination
    north = min(90.0, max(start_latitude, end_latitude) + padding_degrees)
    south = max(-90.0, min(start_latitude, end_latitude) - padding_degrees)
    east = min(180.0, max(start_longitude, end_longitude) + padding_degrees)
    west = max(-180.0, min(start_longitude, end_longitude) - padding_degrees)
    return west, south, east, north


def _configure_osmnx() -> None:
    if ox is not None:
        ox.settings.use_cache = True
        ox.settings.requests_timeout = 90
        ox.settings.http_user_agent = "RouteForge-college-project/1.0"


def radius_to_metres(radius_km: int | float) -> int:
    if radius_km <= 0:
        raise ValueError("Search radius must be positive.")
    return int(round(float(radius_km) * 1000))


def _graph_cache_path(
    start: tuple[float, float],
    destination: tuple[float, float],
    radius_km: int | float,
) -> Path:
    cache_key = "|".join(
        [
            f"{start[0]:.6f}",
            f"{start[1]:.6f}",
            f"{destination[0]:.6f}",
            f"{destination[1]:.6f}",
            str(radius_km),
            "drive",
        ]
    )
    digest = sha256(cache_key.encode("utf-8")).hexdigest()[:20]
    return CACHE_DIRECTORY / f"{digest}.graphml"


def _load_cached_graph(path: Path) -> nx.MultiDiGraph | None:
    if not path.exists():
        return None
    try:
        graph = ox.load_graphml(path)
    except Exception:
        return None
    return graph if graph.number_of_nodes() else None


def _download_with_retries(loader):
    """Retry transient public Overpass failures without unbounded requests."""
    endpoints = [
        "https://overpass-api.de/api",
        "https://overpass.kumi.systems/api",
    ]
    last_error = None
    for attempt in range(3):
        ox.settings.overpass_url = endpoints[attempt % len(endpoints)]
        try:
            return loader()
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                sleep(2**attempt)
    raise RuntimeError(
        "The public OpenStreetMap Overpass service is temporarily busy or unavailable. "
        "Wait a minute and try again with a smaller network padding."
    ) from last_error


def _validate_coordinates(latitude: float, longitude: float) -> None:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Coordinates must use latitude -90..90 and longitude -180..180.")


@lru_cache(maxsize=128)
def geocode(place: str) -> tuple[float, float]:
    if not place or not place.strip():
        raise ValueError("Enter a location or address.")
    coordinate_match = re.fullmatch(
        r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*", place
    )
    if coordinate_match:
        latitude, longitude = map(float, coordinate_match.groups())
        _validate_coordinates(latitude, longitude)
        return latitude, longitude
    if ox is None:
        raise RuntimeError(
            "OSMnx could not be loaded. Install requirements.txt in the project virtual "
            "environment. The underlying error was: "
            f"{_OSMNX_IMPORT_ERROR}"
        ) from _OSMNX_IMPORT_ERROR
    _configure_osmnx()
    try:
        latitude, longitude = ox.geocode(place.strip())
    except Exception as exc:
        raise RuntimeError(f"Could not geocode '{place}'. Check the spelling or try a nearby landmark.") from exc
    return float(latitude), float(longitude)


def geocode_location(place: str) -> dict[str, Any]:
    """Resolve a user input and retain a human-readable name for the UI."""
    latitude, longitude = geocode(place)
    return {
        "query": place.strip(),
        "display_name": place.strip(),
        "latitude": latitude,
        "longitude": longitude,
    }


def retrieve_graph(place: str, dist: int = 2500) -> nx.MultiDiGraph:
    if ox is None:
        raise RuntimeError(
            "OSMnx could not be loaded. Install requirements.txt in the project virtual "
            "environment. The underlying error was: "
            f"{_OSMNX_IMPORT_ERROR}"
        ) from _OSMNX_IMPORT_ERROR
    _configure_osmnx()
    if dist <= 0:
        raise ValueError("Search radius must be positive.")
    try:
        graph = ox.graph_from_point(geocode(place), dist=dist, network_type="drive", simplify=True)
    except Exception as exc:
        raise RuntimeError("OpenStreetMap road data could not be retrieved. Check your internet connection and try again.") from exc
    if graph.number_of_nodes() == 0:
        raise RuntimeError("The selected area contains no usable road network.")
    return graph


def retrieve_graph_for_locations(
    start: tuple[float, float],
    destination: tuple[float, float],
    padding_degrees: float = 0.015,
    radius_km: int | float = DEFAULT_RADIUS_KM,
) -> nx.MultiDiGraph:
    """Download one bounded graph whose network contains both endpoints.

    The selected radius is both the maximum supported endpoint separation and
    the OSMnx search radius in metres. Cached GraphML is reused when available.
    """
    if ox is None:
        raise RuntimeError(
            "OSMnx could not be loaded. Install requirements.txt in the project virtual "
            "environment. The underlying error was: "
            f"{_OSMNX_IMPORT_ERROR}"
        ) from _OSMNX_IMPORT_ERROR
    start_lat, start_lon = start
    end_lat, end_lon = destination
    _validate_coordinates(start_lat, start_lon)
    _validate_coordinates(end_lat, end_lon)
    _configure_osmnx()
    radius_metres = radius_to_metres(radius_km)
    distance_km = _great_circle_km(start, destination)
    if distance_km > float(radius_km):
        raise ValueError(
            f"These locations are about {distance_km:.0f} km apart. "
            f"Choose a larger search radius than {radius_km:g} km."
        )
    cache_path = _graph_cache_path(start, destination, radius_km)
    cached_graph = _load_cached_graph(cache_path)
    if cached_graph is not None:
        return cached_graph
    padding_degrees = max(padding_degrees, NETWORK_PADDING_METRES / 111_000)
    midpoint = ((start_lat + end_lat) / 2, (start_lon + end_lon) / 2)
    try:
        graph = _download_with_retries(
            lambda: ox.graph_from_point(
                midpoint,
                dist=radius_metres,
                network_type="drive",
                simplify=True,
            )
        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("OpenStreetMap road data could not be retrieved for both locations.") from exc
    if graph.number_of_nodes() == 0:
        raise RuntimeError("The selected area contains no usable road network.")
    try:
        CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        ox.save_graphml(graph, filepath=cache_path)
    except Exception:
        # A cache write must never make an otherwise valid route fail.
        pass
    return graph


def nearest_node(graph: nx.Graph, latitude: float, longitude: float):
    if graph.number_of_nodes() == 0:
        raise ValueError("Cannot snap coordinates on an empty graph.")
    if ox is not None:
        try:
            return ox.distance.nearest_nodes(graph, X=longitude, Y=latitude)
        except Exception:
            pass
    candidates = []
    for node, data in graph.nodes(data=True):
        if "x" not in data or "y" not in data:
            continue
        candidates.append((hypot(float(data["x"]) - longitude, float(data["y"]) - latitude), node))
    if not candidates:
        raise ValueError("The graph has no coordinate metadata for snapping.")
    return min(candidates)[1]


def route_coordinates(graph: nx.Graph, path: list) -> list[tuple[float, float]]:
    coordinates = []
    for node in path:
        data = graph.nodes[node]
        if "y" not in data or "x" not in data:
            raise ValueError(f"Node {node!r} has no map coordinates.")
        coordinates.append((float(data["y"]), float(data["x"])))
    return coordinates


def graph_bounds(graph: nx.Graph) -> tuple[float, float, float, float] | None:
    coordinates = [
        (float(data["y"]), float(data["x"]))
        for _, data in graph.nodes(data=True)
        if "x" in data and "y" in data
    ]
    if not coordinates:
        return None
    lats, lons = zip(*coordinates)
    return min(lats), min(lons), max(lats), max(lons)


def closure_copy(graph: nx.Graph, edge: tuple[Any, Any, Any] | tuple[Any, Any]) -> nx.Graph:
    """Return a modified copy, leaving cached/original network data untouched."""
    working = deepcopy(graph)
    if len(edge) == 3 and working.is_multigraph():
        working.remove_edge(edge[0], edge[1], edge[2])
    else:
        working.remove_edge(edge[0], edge[1])
    return working
