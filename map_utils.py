"""Folium map construction kept separate from Streamlit UI code."""

from __future__ import annotations

import folium


def create_map(graph, start=None, destination=None, route=None, zoom_start: int = 13):
    if graph.number_of_nodes():
        lats = [data["y"] for _, data in graph.nodes(data=True) if "y" in data]
        lons = [data["x"] for _, data in graph.nodes(data=True) if "x" in data]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)] if lats else [20.5937, 78.9629]
    else:
        center = [20.5937, 78.9629]
    fmap = folium.Map(location=center, zoom_start=zoom_start, tiles="OpenStreetMap")
    if start:
        folium.Marker(start, tooltip="Start", icon=folium.Icon(color="green")).add_to(fmap)
    if destination:
        folium.Marker(destination, tooltip="Destination", icon=folium.Icon(color="red")).add_to(fmap)
    if route:
        folium.PolyLine(route, color="#00b8d9", weight=6, opacity=0.9, tooltip="Selected route").add_to(fmap)
        fmap.fit_bounds(route, padding=(24, 24))
    elif start and destination:
        fmap.fit_bounds([start, destination], padding=(24, 24))
    return fmap
