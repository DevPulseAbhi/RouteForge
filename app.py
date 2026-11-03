"""RouteForge Streamlit application."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from benchmarks import compare_algorithms, path_rows
from config import CITY_OPTIONS, DEFAULT_RADIUS_LABEL, NETWORK_PADDING_METRES, RADIUS_OPTIONS_KM
from map_utils import create_map
from road_network import (
    closure_copy,
    geocode_location,
    graph_bounds,
    nearest_node,
    retrieve_graph_for_locations,
    route_coordinates,
)
from visualization import comparison_chart, results_frame


@st.cache_resource(show_spinner=False)
def load_route_graph(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
    padding_degrees: float,
    radius_km: int,
):
    return retrieve_graph_for_locations(
        (origin_latitude, origin_longitude),
        (destination_latitude, destination_longitude),
        padding_degrees,
        radius_km,
    )


st.set_page_config(page_title="RouteForge", page_icon="🗺️", layout="wide")
st.title("RouteForge")
st.caption("Interactive route optimization and algorithm analysis on real OpenStreetMap road networks.")
st.markdown(
    "**Project purpose:** RouteForge demonstrates how graph algorithms solve a real routing problem. "
    "It converts OpenStreetMap roads into a weighted graph, runs custom Dijkstra, A*, and BFS searches, "
    "then compares their distance, exploration, and execution metrics."
)

with st.sidebar:
    st.header("Route setup")
    city = st.selectbox("Location suggestion", CITY_OPTIONS)
    st.caption("Larger study areas may take longer and use more memory.")
    start_text = st.text_input(
        "Origin",
        value=st.session_state.get("start_text", ""),
        placeholder="Address or 'latitude, longitude'",
    )
    destination_text = st.text_input(
        "Destination",
        value=st.session_state.get("destination_text", ""),
        placeholder="Address or 'latitude, longitude'",
    )
    algorithm_name = st.selectbox("Primary algorithm", ["Dijkstra", "A*", "BFS"])
    radius_label = st.selectbox(
        "Road-network search radius",
        list(RADIUS_OPTIONS_KM),
        index=list(RADIUS_OPTIONS_KM).index(DEFAULT_RADIUS_LABEL),
        help="The selected value is passed to OSMnx as metres. Larger areas may require more time and memory.",
    )
    radius_km = RADIUS_OPTIONS_KM[radius_label]
    if radius_km >= 150:
        st.warning(
            f"{radius_label} may download a large road network and take longer. "
            "Use Local for normal demonstrations."
        )
    compare = st.checkbox("Run algorithm race", value=True)
    calculate = st.button("Calculate route", type="primary", use_container_width=True)

if calculate:
    origin_query = start_text.strip() or city
    destination_query = destination_text.strip()
    if not destination_query:
        st.error("Enter a destination before calculating a route.")
        st.stop()
    with st.spinner("Resolving locations and downloading one bounded road network..."):
        try:
            origin = geocode_location(origin_query)
            destination = geocode_location(destination_query)
            padding_degrees = NETWORK_PADDING_METRES / 111_000
            graph = load_route_graph(
                origin["latitude"],
                origin["longitude"],
                destination["latitude"],
                destination["longitude"],
                padding_degrees,
                radius_km,
            )
            source = nearest_node(graph, origin["latitude"], origin["longitude"])
            target = nearest_node(graph, destination["latitude"], destination["longitude"])
            working = graph
            st.session_state.closed_edge = None
            all_results = compare_algorithms(working, source, target) if compare else []
            if not all_results:
                from algorithms import astar, bfs, dijkstra

                runner = {"Dijkstra": dijkstra, "A*": astar, "BFS": bfs}[algorithm_name]
                all_results = [runner(working, source, target)]
            selected = next((item for item in all_results if item.algorithm == algorithm_name), all_results[0])
            st.session_state.update(
                graph=graph,
                working_graph=working,
                origin=origin,
                destination=destination,
                source=source,
                target=target,
                results=all_results,
                selected_result=selected,
                start_text=start_text,
                destination_text=destination_text,
                place=f"{origin['display_name']} → {destination['display_name']}",
                radius_label=radius_label,
                radius_km=radius_km,
                selected_algorithm=algorithm_name,
                compare=compare,
            )
            st.success("Route calculation completed.")
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))

graph = st.session_state.get("graph")
results = st.session_state.get("results")
origin = st.session_state.get("origin")
destination = st.session_state.get("destination")
selected = st.session_state.get("selected_result")

if graph is None or not results or not origin or not destination:
    st.info("Enter an origin and destination, then calculate a route using real OpenStreetMap data.")
    st.markdown("### Workflow\n1. Enter two locations. 2. Choose an algorithm. 3. Calculate the route. 4. Inspect the map, metrics, comparison, and path export.")
    st.stop()

working = st.session_state.get("working_graph", graph)
route = route_coordinates(working, selected.path) if selected and selected.found else None
st.caption(
    f"Network: {graph.number_of_nodes():,} nodes · {graph.number_of_edges():,} edges · "
    f"Search radius: {st.session_state.get('radius_label', DEFAULT_RADIUS_LABEL)}"
)

map_col, info_col = st.columns([2.2, 1])
with map_col:
    st_folium(
        create_map(
            working,
            (origin["latitude"], origin["longitude"]),
            (destination["latitude"], destination["longitude"]),
            route,
        ),
        height=600,
        use_container_width=True,
    )
with info_col:
    st.subheader("Route analysis")
    st.write(f"**Origin:** {origin['display_name']}")
    st.write(f"**Destination:** {destination['display_name']}")
    st.write(f"**Resolved origin:** `{origin['latitude']:.6f}, {origin['longitude']:.6f}`")
    st.write(f"**Resolved destination:** `{destination['latitude']:.6f}, {destination['longitude']:.6f}`")
    st.write(f"**Snapped nodes:** `{selected.source}` → `{selected.target}`")
    if selected.found:
        st.success(selected.message or "A valid route was found.")
        st.metric("Route distance", f"{selected.cost:,.1f} m")
        st.metric("Path hops", selected.hops)
        st.metric("Execution time", f"{selected.execution_time_ms:.3f} ms")
    else:
        st.error(selected.message or "No route was found.")
    st.write(f"**Nodes explored:** {selected.explored_nodes:,}")
    st.write(f"**Edges considered:** {selected.edges_considered:,}")
    st.write(f"**Path nodes:** {len(selected.path):,}")

if len(results) > 1:
    st.subheader("Algorithm race")
    comparison = results_frame(results)
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(comparison_chart(results, "Time (ms)"), use_container_width=True)
    with chart_col2:
        st.plotly_chart(comparison_chart(results, "Nodes explored"), use_container_width=True)
    st.info("Dijkstra and A* optimize weighted distance. BFS minimizes hops and may return a longer physical route. Timings exclude geocoding, downloads, and rendering.")

if selected.found:
    rows = path_rows(working, selected.path)
    path_frame = pd.DataFrame(rows)
    st.subheader("Path inspection")
    st.caption("The table contains the ordered final path, not every node explored during search.")
    st.dataframe(path_frame, use_container_width=True, hide_index=True, height=280)
    csv_col, report_col = st.columns(2)
    csv_col.download_button("Download path CSV", path_frame.to_csv(index=False), "route_path.csv", "text/csv")
    report_col.download_button("Download comparison CSV", results_frame(results).to_csv(index=False), "algorithm_comparison.csv", "text/csv")

with st.expander("Network explorer"):
    bounds = graph_bounds(graph)
    st.write(f"**Graph nodes:** {graph.number_of_nodes():,}")
    st.write(f"**Graph edges:** {graph.number_of_edges():,}")
    st.write(f"**Origin node:** `{selected.source}` · **Destination node:** `{selected.target}`")
    st.write(f"**Bounds (south, west, north, east):** `{bounds}`")
    st.write(f"**Path exists:** {'Yes' if selected.found else 'No'}")

with st.expander("Simulated road closure"):
    st.warning("Simulation only. This does not represent a real-world closure or live traffic.")
    edges = list(graph.edges(keys=True)) if graph.is_multigraph() else list(graph.edges())
    labels = [f"{edge[0]} → {edge[1]}" for edge in edges]
    selected_label = st.selectbox("Select an edge", ["None"] + labels)
    closure_col, reset_col = st.columns(2)
    if closure_col.button("Apply closure"):
        closed_edge = None if selected_label == "None" else edges[labels.index(selected_label)]
        st.session_state.closed_edge = closed_edge
        working_after_closure = graph if closed_edge is None else closure_copy(graph, closed_edge)
        source = st.session_state.source
        target = st.session_state.target
        from algorithms import astar, bfs, dijkstra

        runners = {"Dijkstra": dijkstra, "A*": astar, "BFS": bfs}
        if st.session_state.get("compare", True):
            updated_results = compare_algorithms(working_after_closure, source, target)
        else:
            updated_results = [runners[st.session_state.get("selected_algorithm", "Dijkstra")](
                working_after_closure, source, target
            )]
        st.session_state.working_graph = working_after_closure
        st.session_state.results = updated_results
        selected_algorithm = st.session_state.get("selected_algorithm", "Dijkstra")
        st.session_state.selected_result = next(
            (item for item in updated_results if item.algorithm == selected_algorithm),
            updated_results[0],
        )
        st.rerun()
    if reset_col.button("Reset closure"):
        st.session_state.closed_edge = None
        st.session_state.working_graph = graph
        st.session_state.results = compare_algorithms(graph, st.session_state.source, st.session_state.target)
        selected_algorithm = st.session_state.get("selected_algorithm", "Dijkstra")
        st.session_state.selected_result = next(
            (item for item in st.session_state.results if item.algorithm == selected_algorithm),
            st.session_state.results[0],
        )
        st.rerun()
