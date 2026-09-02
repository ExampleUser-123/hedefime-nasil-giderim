import pandas as pd
from pathlib import Path
from datetime import date


BASE_DIR = Path(__file__).resolve().parent.parent
STOPS_FILE = BASE_DIR / "stops.csv"


def convert_coordinate(value):
    value = str(value)

    cleaned = value.replace(".", "")

    if not cleaned.isdigit():
        return None

    try:
        return float(cleaned[:2] + "." + cleaned[2:])
    except (ValueError, IndexError):
        return None


def load_stops():
    df = pd.read_csv(
        STOPS_FILE,
        sep=";",
        dtype=str
)
    

    df["lat"] = df["stop_lat"].apply(convert_coordinate)
    df["lon"] = df["stop_lon"].apply(convert_coordinate)

    df = df.dropna(subset=["lat", "lon"])

    return df

def normalize_text(text):
    text = str(text).lower()
    text = text.replace("̇", "")

    replacements = {
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

def fix_encoding(value):
    if not isinstance(value, str):
        return value

    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def search_stops(query: str, limit: int = 10):
    df = load_stops()

    query = normalize_text(query.strip())

    if not query:
        return []

    stop_names = df["stop_name"].astype(str).apply(normalize_text)

    matches = df[
        stop_names.str.contains(query, na=False)
    ]

    results = []

    for _, row in matches.head(limit).iterrows():
        results.append({
            "stop_id": str(row["stop_id"]),
            "stop_code": str(row["stop_code"]),
            "stop_name": str(row["stop_name"]),
            "description": str(row["stop_desc"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"])
        })

    return results

from math import radians, sin, cos, sqrt, atan2


def find_nearest_stops(lat: float, lon: float, limit: int = 5):
    df = load_stops()

    lat1 = radians(lat)
    lon1 = radians(lon)

    def distance(row):
        lat2 = radians(row["lat"])
        lon2 = radians(row["lon"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )

        return 6371 * 2 * atan2(sqrt(a), sqrt(1 - a))

    df["distance_km"] = df.apply(distance, axis=1)

    nearest = df.sort_values("distance_km").head(limit)

    results = []

    for _, row in nearest.iterrows():
        results.append({
            "stop_id": str(row["stop_id"]),
            "stop_code": str(row["stop_code"]),
            "stop_name": str(row["stop_name"]),
            "description": str(row["stop_desc"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "distance_km": round(float(row["distance_km"]), 3)
        })

    return results

def get_routes_at_stop(stop_id: str):
    base_dir = Path(__file__).resolve().parent.parent

    stop_times_file = base_dir / "stop_times.csv"
    trips_file = base_dir / "trips.csv"
    routes_file = base_dir / "routes.csv"

    stop_times = pd.read_csv(
        stop_times_file,
        sep=";",
        dtype=str
    )

    trips = pd.read_csv(
        trips_file,
        sep=";",
        dtype=str
    )

    routes = pd.read_csv(
    routes_file,
    sep=";",
    dtype=str
)

    routes["route_long_name"] = routes["route_long_name"].apply(fix_encoding)
    routes["route_long_name"] = (
    routes["route_long_name"]
    .str.replace("KÄ°", "Kİ", regex=False)
    .str.replace("Ã–", "Ö", regex=False)
    .str.replace("Ãœ", "Ü", regex=False)
    .str.replace("Ã‡", "Ç", regex=False)
    .str.replace("Äž", "Ğ", regex=False)
    .str.replace("Åž", "Ş", regex=False)
    .str.replace("Ä°", "İ", regex=False)
    .str.replace("Ä±", "ı", regex=False)
    .str.replace("Ãœ", "Ü", regex=False)
)

    stop_trips = stop_times[
        stop_times["stop_id"] == str(stop_id)
    ]

    if stop_trips.empty:
        return []

    stop_trips = stop_trips[["trip_id"]].drop_duplicates()

    merged = stop_trips.merge(
        trips,
        on="trip_id",
        how="inner"
    )

    merged = merged.merge(
        routes,
        on="route_id",
        how="inner"
    )

    results = (
        merged[
            [
                "route_id",
                "route_short_name",
                "route_long_name",
                "trip_headsign",
                "direction_id"
            ]
        ]
        .drop_duplicates()
    )

    return results.to_dict(orient="records")

def get_stops_at_route(route_id: str, direction_id: str | None = None):
    base_dir = Path(__file__).resolve().parent.parent

    stop_times_file = base_dir / "stop_times.csv"
    stops_file = base_dir / "stops.csv"
    trips_file = base_dir / "trips.csv"

    stop_times = pd.read_csv(
        stop_times_file,
        sep=";",
        dtype=str
    )

    trips = pd.read_csv(
        trips_file,
        sep=";",
        dtype=str
    )

    stops = pd.read_csv(
        stops_file,
        sep=";",
        dtype=str
    )

    trips = trips[
        trips["route_id"] == str(route_id)
    ]

    if direction_id is not None:
        trips = trips[
            trips["direction_id"] == str(direction_id)
        ]

        # Sadece bugün aktif olan servisleri göster
        active_service_ids = []

        for service_id in trips["service_id"].dropna().unique():
            if is_service_active(service_id):
                active_service_ids.append(service_id)

        trips = trips[
            trips["service_id"].isin(active_service_ids)
        ]

    if trips.empty:
        return []

    trip_ids = trips["trip_id"].drop_duplicates()

    stop_times = stop_times[
        stop_times["trip_id"].isin(trip_ids)
    ]

    if stop_times.empty:
        return []

    stop_times = stop_times[
        ["stop_id", "stop_sequence"]
    ].drop_duplicates()

    results = stop_times.merge(
        stops,
        on="stop_id",
        how="inner"
    )

    results["stop_sequence"] = pd.to_numeric(
    results["stop_sequence"],
    errors="coerce"
)

    results = results.sort_values(
        "stop_sequence"
    )

    return results[
        [
            "stop_id",
            "stop_code",
            "stop_name",
            "stop_sequence"
        ]
    ].to_dict(orient="records")

def get_trips_at_route(route_id: str, direction_id: str | None = None):
    base_dir = Path(__file__).resolve().parent.parent

    trips_file = base_dir / "trips.csv"

    trips = pd.read_csv(
        trips_file,
        sep=";",
        dtype=str
    )

    trips = trips[
        trips["route_id"] == str(route_id)
    ]

    if direction_id is not None:
        trips = trips[
            trips["direction_id"] == str(direction_id)
        ]

        # Sadece bugün aktif olan servisleri göster
        active_service_ids = []

    for service_id in trips["service_id"].dropna().unique():
        if is_service_active(service_id):
            active_service_ids.append(service_id)

    trips = trips[
         trips["service_id"].isin(active_service_ids)
    ]

    if trips.empty:
        return []

    return trips[
        [
            "trip_id",
            "service_id",
            "trip_headsign",
            "direction_id"
        ]
    ].drop_duplicates().to_dict(orient="records")

def get_trip_stop_times(trip_id: str):
    base_dir = Path(__file__).resolve().parent.parent

    stop_times_file = base_dir / "stop_times.csv"
    stops_file = base_dir / "stops.csv"

    stop_times = pd.read_csv(
        stop_times_file,
        sep=";",
        dtype=str
    )

    stops = pd.read_csv(
        stops_file,
        sep=";",
        dtype=str
    )

    trip_times = stop_times[
        stop_times["trip_id"] == str(trip_id)
    ]

    if trip_times.empty:
        return []

    trip_times = trip_times.merge(
        stops[
            [
                "stop_id",
                "stop_name"
            ]
        ],
        on="stop_id",
        how="left"
    )

    trip_times["stop_sequence"] = pd.to_numeric(
        trip_times["stop_sequence"],
        errors="coerce"
    )

    trip_times = trip_times.sort_values(
        "stop_sequence"
    )

    trip_times = trip_times.fillna("")

    return trip_times[
        [
            "stop_id",
            "stop_name",
            "stop_sequence",
            "arrival_time",
            "departure_time"
        ]
    ].to_dict(orient="records")

def is_service_active(service_id: str, check_date=None):
    base_dir = Path(__file__).resolve().parent.parent

    calendar_file = base_dir / "calendar.csv"

    calendar = pd.read_csv(
        calendar_file,
        sep=";",
        dtype=str
    )

    service = calendar[
        calendar["service_id"] == str(service_id)
    ]

    if service.empty:
        return False

    service = service.iloc[0]

    if check_date is None:
        check_date = date.today()

    date_number = check_date.strftime("%Y%m%d")

    if date_number < service["start_date"]:
        return False

    if date_number > service["end_date"]:
        return False

    weekday_names = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday"
    ]

    weekday = weekday_names[check_date.weekday()]

    return service[weekday] == "1"

def is_service_active(service_id: str, check_date=None):
    base_dir = Path(__file__).resolve().parent.parent

    calendar_file = base_dir / "calendar.csv"

    calendar = pd.read_csv(
        calendar_file,
        sep=";",
        dtype=str
    )

    service = calendar[
        calendar["service_id"] == str(service_id)
    ]

    if service.empty:
        return False

    service = service.iloc[0]

    if check_date is None:
        check_date = date.today()

    date_number = check_date.strftime("%Y%m%d")

    if date_number < service["start_date"]:
        return False

    if date_number > service["end_date"]:
        return False

    weekday_names = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday"
    ]

    weekday = weekday_names[check_date.weekday()]

    return service[weekday] == "1"

def find_direct_route(start_stop_id: str, end_stop_id: str):
    base_dir = Path(__file__).resolve().parent.parent

    stop_times_file = base_dir / "stop_times.csv"
    trips_file = base_dir / "trips.csv"

    stop_times = pd.read_csv(
        stop_times_file,
        sep=";",
        dtype=str
    )

    trips = pd.read_csv(
        trips_file,
        sep=";",
        dtype=str
    )

    # Başlangıç ve hedef duraklardan geçen seferleri bul
    start_trips = stop_times[
        stop_times["stop_id"] == str(start_stop_id)
    ][["trip_id", "stop_sequence"]]

    end_trips = stop_times[
        stop_times["stop_id"] == str(end_stop_id)
    ][["trip_id", "stop_sequence"]]

    if start_trips.empty or end_trips.empty:
        return []

    # Aynı seferde iki durağın da bulunması gerekiyor
    merged = start_trips.merge(
        end_trips,
        on="trip_id",
        suffixes=("_start", "_end")
    )

    # Hedef durak başlangıçtan sonra gelmeli
    merged["stop_sequence_start"] = pd.to_numeric(
        merged["stop_sequence_start"],
        errors="coerce"
    )

    merged["stop_sequence_end"] = pd.to_numeric(
        merged["stop_sequence_end"],
        errors="coerce"
    )

    merged = merged[
        merged["stop_sequence_end"] >
        merged["stop_sequence_start"]
    ]

    if merged.empty:
        return []

    # Sefer bilgilerini ekle
    merged = merged.merge(
        trips[
            [
                "trip_id",
                "route_id",
                "service_id",
                "trip_headsign",
                "direction_id"
            ]
        ],
        on="trip_id",
        how="left"
    )

    # Sadece bugün çalışan seferleri bırak
    active_service_ids = []

    for service_id in merged["service_id"].dropna().unique():
        if is_service_active(service_id):
            active_service_ids.append(service_id)

    merged = merged[
        merged["service_id"].isin(active_service_ids)
    ]

    if merged.empty:
        return []

    return merged[
        [
            "trip_id",
            "route_id",
            "service_id",
            "trip_headsign",
            "direction_id",
            "stop_sequence_start",
            "stop_sequence_end"
        ]
    ].drop_duplicates().to_dict(orient="records")

def build_trip_graph(trip_id: str):
    stop_times = get_trip_stop_times(trip_id)

    if not stop_times:
        return {}

    graph = {}

    for i in range(len(stop_times) - 1):
        current_stop = stop_times[i]
        next_stop = stop_times[i + 1]

        current_id = current_stop["stop_id"]
        next_id = next_stop["stop_id"]

        if current_id not in graph:
            graph[current_id] = []

        graph[current_id].append({
            "to_stop_id": next_id,
            "type": "transit",
            "from_stop_name": current_stop["stop_name"],
            "to_stop_name": next_stop["stop_name"],
            "stop_sequence_from": current_stop["stop_sequence"],
            "stop_sequence_to": next_stop["stop_sequence"]
        })

    return graph

from collections import deque


def find_path(graph, start_stop_id: str, end_stop_id: str):
    if start_stop_id not in graph:
        return []

    queue = deque([
        (start_stop_id, [start_stop_id])
    ])

    visited = set([start_stop_id])

    while queue:
        current_stop, path = queue.popleft()

        if current_stop == end_stop_id:
            return path

        for connection in graph.get(current_stop, []):
            next_stop = connection["to_stop_id"]

            if next_stop not in visited:
                visited.add(next_stop)

                queue.append(
                    (
                        next_stop,
                        path + [next_stop]
                    )
                )

    return []

def build_full_transit_graph():
    base_dir = Path(__file__).resolve().parent.parent

    stop_times_file = base_dir / "stop_times.csv"
    trips_file = base_dir / "trips.csv"
    stops_file = base_dir / "stops.csv"

    # Dosyaları sadece bir kez oku
    stop_times = pd.read_csv(
        stop_times_file,
        sep=";",
        dtype=str
    )

    trips = pd.read_csv(
        trips_file,
        sep=";",
        dtype=str
    )

    stops = pd.read_csv(
        stops_file,
        sep=";",
        dtype=str
    )

    # Sadece bugün aktif olan servisleri bul
    active_service_ids = []

    for service_id in trips["service_id"].dropna().unique():
        if is_service_active(service_id):
            active_service_ids.append(service_id)

    trips = trips[
        trips["service_id"].isin(active_service_ids)
    ]

    if trips.empty:
        return {}

    # Sadece aktif seferlerin stop zamanlarını al
    stop_times = stop_times[
        stop_times["trip_id"].isin(trips["trip_id"])
    ]

    # Stop bilgilerini ekle
    stop_times = stop_times.merge(
        stops[
            [
                "stop_id",
                "stop_name"
            ]
        ],
        on="stop_id",
        how="left"
    )

    # Sefer bilgilerini ekle
    stop_times = stop_times.merge(
        trips[
            [
                "trip_id",
                "route_id",
                "service_id",
                "trip_headsign",
                "direction_id"
            ]
        ],
        on="trip_id",
        how="left"
    )

    # Stop sırasını sayıya çevir
    stop_times["stop_sequence_num"] = pd.to_numeric(
        stop_times["stop_sequence"],
        errors="coerce"
    )

    stop_times = stop_times.sort_values(
        [
            "trip_id",
            "stop_sequence_num"
        ]
    )

    graph = {}

    # Her sefer için ardışık durakları birbirine bağla
    for trip_id, trip_stops in stop_times.groupby("trip_id"):

        trip_stops = trip_stops.to_dict(orient="records")

        for i in range(len(trip_stops) - 1):

            current = trip_stops[i]
            next_stop = trip_stops[i + 1]

            current_id = current["stop_id"]
            next_id = next_stop["stop_id"]

            if current_id not in graph:
                graph[current_id] = []

            graph[current_id].append({
                "to_stop_id": next_id,
                "type": "transit",
                "route_id": current["route_id"],
                "trip_id": current["trip_id"],
                "service_id": current["service_id"],
                "trip_headsign": current["trip_headsign"],
                "direction_id": current["direction_id"],
                "from_stop_name": current["stop_name"],
                "to_stop_name": next_stop["stop_name"],
                "stop_sequence_from": current["stop_sequence"],
                "stop_sequence_to": next_stop["stop_sequence"]
            })

    transfer_edges = build_transfer_edges()

    for transfer in transfer_edges:
        from_stop = transfer["from_stop_id"]

        if from_stop not in graph:
            graph[from_stop] = []

        graph[from_stop].append({
            "to_stop_id": transfer["to_stop_id"],
            "route_id": None,
            "trip_id": None,
            "service_id": None,
            "trip_headsign": None,
            "direction_id": None,
            "from_stop_name": transfer["from_stop_name"],
            "to_stop_name": transfer["to_stop_name"],
            "stop_sequence_from": None,
            "stop_sequence_to": None,
            "type": "transfer",
            "distance_km": transfer["distance_km"]
        })

    return graph

def find_transit_path(graph, start_stop_id, end_stop_id):
    from collections import deque

    # Durum:
    # (durak_id, mevcut_route_id)
    #
    # Böylece aynı durakta farklı otobüs hatlarını
    # birbirinden ayrı durumlar olarak takip edebiliyoruz.

    queue = deque()

    # Başlangıçta henüz bir otobüs hattında değiliz.
    queue.append((start_stop_id, None))

    visited = {(start_stop_id, None)}
    previous = {}
    edge_info = {}

    target_state = None

    while queue:
        current_stop, current_route_id = queue.popleft()

        if current_stop == end_stop_id:
            target_state = (current_stop, current_route_id)
            break

        for connection in graph.get(current_stop, []):

            next_stop = connection["to_stop_id"]
            edge_type = connection.get("type")

            # 🚌 Otobüs bağlantısı
            if edge_type == "transit":

                route_id = connection.get("route_id")

                # Henüz otobüse binmediysek veya
                # aynı hatta devam ediyorsak geç.
                if current_route_id is None or route_id == current_route_id:
                    next_state = (next_stop, route_id)
                else:
                    # Başka hatta geçmek için önce transfer gerekiyor.
                    continue

            # 🚶 Transfer bağlantısı
            elif edge_type == "transfer":

                # Transfer yaptıktan sonra artık belirli
                # bir otobüs hattında değiliz.
                next_state = (next_stop, None)

            else:
                continue

            if next_state in visited:
                continue

            visited.add(next_state)
            previous[next_state] = (current_stop, current_route_id)
            edge_info[next_state] = connection

            queue.append(next_state)

    if target_state is None:
        return None

    # Yolu geriye doğru oluştur
    path_states = []
    current_state = target_state

    while current_state in previous:
        path_states.append(current_state)
        current_state = previous[current_state]

    path_states.append((start_stop_id, None))
    path_states.reverse()

    # Sonuçları hazırlıyoruz
    stops = [state[0] for state in path_states]

    route = []

    for i in range(1, len(path_states)):
        state = path_states[i]
        connection = edge_info[state]

        route.append({
            "from_stop_id": path_states[i - 1][0],
            "to_stop_id": state[0],
            "from_stop_name": connection["from_stop_name"],
            "to_stop_name": connection["to_stop_name"],
            "route_id": connection.get("route_id"),
            "trip_id": connection.get("trip_id"),
            "trip_headsign": connection.get("trip_headsign"),
            "direction_id": connection.get("direction_id"),
            "type": connection.get("type"),
            "distance_km": connection.get("distance_km")
        })

    return {
        "start_stop_id": start_stop_id,
        "end_stop_id": end_stop_id,
        "stop_count": len(stops),
        "stops": stops,
        "route": route
    }

def build_transfer_edges(max_distance_km=0.5):
    stops = load_stops()

    lat = stops["lat"].to_numpy()
    lon = stops["lon"].to_numpy()
    stop_ids = stops["stop_id"].to_numpy()
    stop_names = stops["stop_name"].to_numpy()

    transfer_edges = []

    max_distance_m = max_distance_km * 1000
    earth_radius_m = 6_371_000

    for i in range(len(stops)):
        lat_diff = lat - lat[i]
        lon_diff = lon - lon[i]

        distance = (
            (lat_diff * 111_000) ** 2
            + (lon_diff * 111_000 * __import__("math").cos(
                __import__("math").radians(lat[i])
            )) ** 2
        ) ** 0.5

        nearby_indexes = (distance <= max_distance_m).nonzero()[0]

        for j in nearby_indexes:
            if i == j:
                continue

            transfer_edges.append({
                "from_stop_id": stop_ids[i],
                "to_stop_id": stop_ids[j],
                "from_stop_name": stop_names[i],
                "to_stop_name": stop_names[j],
                "distance_km": round(float(distance[j]) / 1000, 3),
                "type": "transfer"
            })

    return transfer_edges