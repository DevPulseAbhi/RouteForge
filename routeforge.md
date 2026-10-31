# Project: RouteForge — Interactive Route Optimization & Algorithm Analysis

Act as a senior Python developer and DAA (Design and Analysis of Algorithms) mentor. Build a fully working, interactive route-optimization application suitable for an MCA academic project, live demonstration, algorithm analysis, and eventual public deployment.

## 1. Start by inspecting the project

Inspect the existing folder before creating or modifying files. Preserve useful existing work. If the folder is empty, initialize a clean project.

Use this stack:
- Python
- Streamlit
- Folium and streamlit-folium for the interactive map
- OpenStreetMap for map tiles and road data
- OSMnx for retrieving and preparing a bounded real-world road network
- NetworkX for graph representation, validation, and reference comparisons only
- Plotly for algorithm performance charts

Implement Dijkstra, A*, and BFS ourselves. Do not simply call NetworkX shortest-path functions or an external routing API to generate the algorithm results.

## 2. Main objective

Create a polished application that calculates routes over actual road-network graphs, displays the selected route on an interactive map, and compares the algorithms' behavior.

This must be a working application, not a static mockup. Never fabricate route results, performance numbers, road networks, or live metrics.

## 3. Real map integration

- Display an interactive OpenStreetMap-based map.
- Allow the user to select a supported city or enter a location.
- Support choosing start and destination locations using map interaction and/or address search.
- Geocode addresses using a suitable geocoding service such as Nominatim, respecting its usage policy, rate limits, attribution requirements, and caching guidance.
- Retrieve a bounded road-network graph for the selected area using OSMnx.
- Snap selected coordinates to appropriate graph nodes.
- Show the selected start, destination, calculated route, road network context, and useful route information on the map.
- Display clear loading states and useful errors when geocoding or road-network retrieval fails.
- Handle ambiguous addresses, missing roads, disconnected graphs, invalid coordinates, and unavailable internet connections.
- Limit graph area and download size to prevent excessive memory use and slow requests.
- Cache appropriate results where safe.
- Never silently switch to fake data if real map data cannot be retrieved.

Use road distance as the primary edge cost. If travel-time weighting is implemented, use supported speed/travel-time attributes and label it correctly. Do not claim live traffic awareness unless a genuine traffic data source is integrated.

## 4. Algorithms

Implement each algorithm in a separate, readable module with clear comments and appropriate data structures.

### Dijkstra
- Calculate the shortest weighted path for non-negative edge weights.
- Track execution time, nodes expanded, edges considered, path distance, and path reconstruction.
- Use a priority queue and stale-entry handling.

### A*
- Use a priority queue and a documented heuristic.
- For road-distance optimization, use a geographically valid lower-bound heuristic, such as straight-line distance between coordinates, consistent with the graph's edge-distance units.
- Ensure the heuristic is admissible and consistent for the chosen cost metric.
- Handle unreachable destinations and reconstruct the path correctly.

### BFS
- Use a queue and visited set.
- Explain that BFS finds the fewest-edge path in an unweighted graph, not necessarily the minimum-distance route on a weighted road network.
- Clearly label its result so users do not confuse it with weighted shortest-path results.

## 5. Algorithm Race and correctness

Provide a comparison mode that runs algorithms on the same graph and same start/destination pair.

Show:
- Path found or no path
- Route distance
- Execution time in milliseconds
- Nodes expanded
- Edges considered, where measured consistently
- Path length and number of hops
- Algorithm-specific notes

Separate data retrieval time from algorithm execution time. Do not compare timings unless the measurement methodology is consistent.

Validate each returned path:
- Starts at the selected source
- Ends at the selected destination
- Uses valid graph edges
- Has a cost consistent with the sum of its edge weights

For comparable weighted algorithms, cross-check results against a reference implementation in tests, but keep the actual displayed routes produced by our custom algorithms.

Use appropriate performance charts and explain why algorithms may explore different numbers of nodes.

## 6. Road closures and route changes

Allow a user to block selected graph edges or simulate a road closure.

- Recalculate routes using the modified graph.
- Do not mutate the original cached graph irreversibly.
- Clearly distinguish simulated closures from actual real-world road closures.
- Show when a closure changes the route or makes the destination unreachable.

## 7. UI and experience

Build a professional, responsive Streamlit interface with:
- Project introduction and concise usage instructions
- City/location selection
- Interactive map and start/destination controls
- Algorithm selection and comparison mode
- Route summary and algorithm metrics
- Performance charts
- Road closure simulation
- Clear loading, success, warning, and error states

Use a clean, consistent visual style. Prevent overlapping text, clipped labels, unreadable charts, and unnecessary reruns. Keep map state and selected locations stable during interactions.

## 8. Suggested project structure

Use a simple modular structure:
- app.py
- algorithms.py
- road_network.py
- map_utils.py
- benchmarks.py
- requirements.txt
- README.md
- .gitignore
- tests/

Add other files only when justified. Do not create excessive abstraction.

## 9. Testing and reliability

Add automated tests for:
- Known small weighted graphs with expected shortest-path costs
- A* and Dijkstra agreement on supported non-negative weighted graphs
- BFS behavior on unweighted graphs
- Disconnected graphs and unreachable destinations
- Source equals destination
- Invalid node IDs
- Zero-weight edges where supported
- Route reconstruction and edge validity
- Road closure behavior
- Performance measurement helpers

Keep core algorithm tests independent of external network access. Use small deterministic test graphs for correctness testing; these are test fixtures, not fake production map data.

Handle dependency errors and remote service failures gracefully. Pin compatible dependency versions in requirements.txt after verifying them.

## 10. Security, cost, and deployment

- Never commit secrets, API keys, or personal environment files.
- Respect public map/geocoding service terms and limits.
- Do not scrape excessively or send repeated uncached requests.
- Avoid downloading entire cities or countries without bounds.
- Document deployment resource limitations and external-service dependencies.
- Provide local Windows setup and run instructions.
- Explain that public deployment may have memory, CPU, and execution-time limits; verify the app within those limits rather than assuming it will work unchanged.

## 11. Implementation workflow

Work in small stages.

Stage A: Inspect the project, explain the architecture and identify practical limitations.

Stage B: Implement and test the custom algorithms using deterministic graph tests.

Stage C: Implement bounded real road-network retrieval, geocoding, map interaction, and route rendering.

Stage D: Implement algorithm comparison, performance metrics, and simulated road closures.

Stage E: Run tests, fix issues, verify requirements, and write complete README instructions.

Start with Stage A only. Do not generate the entire application in one uncontrolled response.

At every stage:
- Edit the project files directly.
- Explain which files changed and why.
- Run the tests available in the environment.
- Report exactly what passed and what remains untested.
- Give me only the next action I need to take.

Do not claim success without evidence. Do not remove working functionality or replace real routes with placeholder results.