# RouteForge

RouteForge is an interactive Streamlit route-analysis application for an MCA/DAA mini project. Its purpose is to demonstrate how a real road network becomes a weighted graph and how different graph-search strategies discover routes with different objectives. It retrieves bounded, real OpenStreetMap driving data through OSMnx and runs independently implemented Dijkstra, A*, and BFS searches over that graph.

## Features

- OpenStreetMap geocoding and bounded road-network retrieval.
- Custom weighted Dijkstra and A* searches plus minimum-hop BFS.
- Consistent route validation and execution metrics.
- Folium map with network context, markers, and selected route.
- Comparison table and Plotly performance charts.
- Reversible simulated edge closures that never mutate the cached original graph.
- Adaptive city/regional downloads: local routes use a midpoint radius and wider routes use a bounded bounding box.
- Selectable search radii: Local (60 km), Regional (150 km), Intercity (300 km), and Extended (500 km).
- GraphML caching prevents repeated downloads for the same endpoints and radius.
- Route-path inspection and CSV export for a college demonstration or report.
- Deterministic offline tests for algorithms, snapping, closures, and benchmarks.

## Architecture

`app.py` contains the Streamlit shell. `algorithms.py` owns graph search. `road_network.py` owns OSMnx access, snapping, and safe graph copies. `benchmarks.py` validates paths and provides comparable runs. `map_utils.py` renders Folium, and `visualization.py` prepares Plotly data.

## Windows setup

```powershell
cd "E:\DAA Mini Project"
py -3.13 -m venv .venv313
.\.venv313\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
python -m streamlit run app.py
```

The existing `.venv` may contain a Python 3.14 installation whose Shapely
native DLL is blocked by Windows Application Control. Use `.venv313` for this
project. You can also double-click `run_routeforge.bat` or run
`.\run_routeforge.ps1`; both launch Streamlit with the verified Python 3.13
environment. RouteForge depends on OSMnx, GeoPandas, and Shapely for real
OpenStreetMap road networks, so these packages must be installed in the same
interpreter that launches Streamlit.

Enter an origin and destination, choose a primary algorithm, and select **Calculate route**. The application geocodes both locations, downloads one network containing both endpoints, snaps them to road nodes, calculates the route, fits the map to the result, and displays the measured analysis. The comparison table contains all algorithms when the race option is enabled. BFS is a minimum-hop demonstration and is not expected to match weighted route distance.

For the best live demonstration, use two recognizable locations in the same city and keep **Local (60 km)** selected. Regional, Intercity, and Extended modes allow wider endpoint separation but can download much larger graphs and require substantially more memory and time. Downloaded GraphML files are stored in the ignored `cache/graphs/` directory and reused for matching endpoint/radius requests.

## Suggested college demonstration

1. Use coordinate inputs if geocoding is ambiguous, for example `12.9716, 77.5946`.
2. Choose a destination within the same city.
3. Run the algorithm race and explain that Dijkstra and A* optimize weighted distance, while BFS minimizes hops.
4. Show the route-analysis cards and ordered path table.
5. Apply a simulated closure and explain how the route or reachability changes.
6. Download the path and comparison CSV files for evidence in the project report.

## Data, attribution, and limits

Road data and map tiles come from OpenStreetMap contributors. Geocoding uses Nominatim through OSMnx. Use a descriptive user agent, keep requests bounded and cached by the hosting environment, and follow the public service policies. The app does not include live traffic or actual closure data.

Internet access is required for geocoding and graph retrieval. Public Streamlit hosting may impose memory, CPU, timeout, and outbound-request limits; a small radius is recommended. Network download time is excluded from algorithm timings. Results vary with graph size and machine performance. No deployment is claimed by this repository.

Project Link: http://localhost:8501