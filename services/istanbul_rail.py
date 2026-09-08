"""
Istanbul rayli ag (metro / Marmaray / tramvay / funikuler) rotari.

Veri: OpenStreetMap hat iliskilerinden derlenen data/istanbul_rail.json.gz
(hat -> sirali duraklar + cizgi geometrisi).

Yontem:
- Duraklar isim + mesafe (400 m) bazli istasyon kumelerine birlestirilir (aktarma noktalari).
- Ayni hattin ardisik duraklari arasina kenar eklenir; sure = mesafe / hat hizi.
- Dijkstra ile kapi->kapi rota: yuruyus + rayli ayaklar + aktarma yuruyusleri.
"""

import functools
import gzip
import heapq
import json
import math
import re

LINE_SPEED_KMH = {
    "subway": 33,
    "tram": 18,
    "light_rail": 25,   # Tünel/F2-F3
    "funicular": 15,
    "train": 45,        # Marmaray
}

WALK_SPEED_M_MIN = 75          # ~4.5 km/s
TRANSFER_PENALTY_MIN = 3.5     # peron degistirme/indirme-binme
MAX_ACCESS_WALK_M = 2500       # giris/cikis icin en fazla yurunecek mesafe
TRANSFER_MERGE_M = 400         # farkli isimli istasyonlar arasi aktarma esigi


def _haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _norm_name(name):
    return re.sub(r"\s+", " ", name).strip().lower()


@functools.lru_cache(maxsize=1)
def _build_network():
    raw = json.loads(gzip.open("data/istanbul_rail.json.gz").read().decode("utf-8"))

    # 1) Istasyon kumeleri: ayni isim YAKIN koordinatta -> ayni kume.
    # Ayni isim ama uzak (T1 Göztepe vs Marmaray Göztepe) -> ayri kumeler.
    groups = []            # [{"name", "lat", "lon", "count"}]
    by_name = {}           # norm_isim -> [kume, ...]
    line_stop_clusters = []   # hat -> [kume_obj, ...] (durdugu kumeler)

    def _cluster_for(stop):
        name = _norm_name(stop["name"])
        for c in by_name.get(name, []):
            if _haversine_m(c["lat"], c["lon"], stop["lat"], stop["lon"]) <= 300:
                n = c["count"]
                c["lat"] = (c["lat"] * n + stop["lat"]) / (n + 1)
                c["lon"] = (c["lon"] * n + stop["lon"]) / (n + 1)
                c["count"] += 1
                return c
        c = {"name": stop["name"], "lat": stop["lat"], "lon": stop["lon"], "count": 1}
        by_name.setdefault(name, []).append(c)
        groups.append(c)
        return c

    for line in raw:
        line_stop_clusters.append([_cluster_for(stop) for stop in line["stops"]])

    # 2) Yakin istasyonlari birlestir (Ayrilikcesme M4 <-> Marmaray aktarmasi vb.)
    n = len(groups)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        ci = groups[i]
        for j in range(i + 1, n):
            cj = groups[j]
            if _haversine_m(ci["lat"], ci["lon"], cj["lat"], cj["lon"]) <= TRANSFER_MERGE_M:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri

    root_idx = {}
    cluster_list = []
    for i in range(n):
        r = find(i)
        if r not in root_idx:
            root_idx[r] = len(cluster_list)
            cluster_list.append({"name": groups[r]["name"], "lat": groups[r]["lat"],
                                 "lon": groups[r]["lon"], "members": [groups[r]["name"]]})
        else:
            cluster_list[root_idx[r]]["members"].append(groups[i]["name"])
        groups[i]["cid"] = root_idx[r]

    # 3) Kenarlar: hattin ardısık duraklari
    edges = {}   # cluster_idx -> [(cluster_idx, time_min, line_idx)]
    for li, line in enumerate(raw):
        speed = LINE_SPEED_KMH.get(line.get("route") or "subway", 30)

        for c1, c2 in zip(line_stop_clusters[li], line_stop_clusters[li][1:]):
            a, b = c1["cid"], c2["cid"]
            if a == b:
                continue

            dist = _haversine_m(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
            time_min = dist / (speed * 1000 / 60)

            edges.setdefault(a, []).append((b, time_min, li))
            edges.setdefault(b, []).append((a, time_min, li))

    return {
        "lines": raw,
        "clusters": cluster_list,
        "edges": edges,
    }


def _line_leg_type(line):
    route = line.get("route") or "subway"

    if route == "train":
        return "marmaray"
    if route == "tram":
        return "tram"
    if route == "funicular":
        return "funicular"

    return "metro"


def _nearest_clusters(lat, lon, max_walk_m=MAX_ACCESS_WALK_M, limit=3):
    net = _build_network()

    scored = []
    for idx, c in enumerate(net["clusters"]):
        d = _haversine_m(lat, lon, c["lat"], c["lon"])
        if d <= max_walk_m:
            scored.append((d, idx))

    scored.sort()
    return scored[:limit]


def find_rail_route(start_lat, start_lon, end_lat, end_lon, max_routes=3, max_walk=None):
    """Kapi->kapi rayli ag rotasi; IETT leg semasina uyumlu doner."""

    access_walk_m = max_walk if max_walk is not None else MAX_ACCESS_WALK_M

    net = _build_network()

    starts = _nearest_clusters(start_lat, start_lon, max_walk_m=access_walk_m)
    ends = _nearest_clusters(end_lat, end_lon, max_walk_m=access_walk_m)

    if not starts or not ends:
        return {
            "status": "no_route",
            "routes": [],
            "error": "Yakinda rayli sistem istasyonu bulunamadi.",
            "source": "Metro İstanbul",
        }

    # Dijkstra, durum = (istasyon, hattaki son line_idx): aktarma cezasi sayilir.
    INF = float("inf")
    dist = {}
    prev = {}
    heap = []

    for walk_m, idx in starts:
        t = walk_m / WALK_SPEED_M_MIN
        state = (idx, None)
        if t < dist.get(state, INF):
            dist[state] = t
            prev[state] = (None, None, walk_m)   # (onceki_durum, edge_line, giris_yuruyus_m)
            heapq.heappush(heap, (t, state))

    end_set = {idx for _, idx in ends}
    settled = {}

    while heap:
        t, state = heapq.heappop(heap)
        if state in settled:
            continue
        settled[state] = t
        idx, cur_line = state

        if end_set.issubset({u for (u, _) in settled}):
            break

        for nb, tmin, li in net["edges"].get(idx, []):
            penalty = 0.0 if cur_line is None or cur_line == li else TRANSFER_PENALTY_MIN
            nt = t + tmin + penalty
            nstate = (nb, li)
            if nt < dist.get(nstate, INF):
                dist[nstate] = nt
                prev[nstate] = (state, li, 0)
                heapq.heappush(heap, (nt, nstate))

    end_walks = {idx: walk for walk, idx in ends}   # cluster_idx -> cikis yuruyus m

    results = []
    for end_idx, walk_out in end_walks.items():
        best_state = min(
            (st for st in settled if st[0] == end_idx),
            key=lambda st: settled[st],
            default=None,
        )
        if best_state is None:
            continue

        total_min = settled[best_state] + walk_out / WALK_SPEED_M_MIN

        # Zinciri geri sar: durum zincirini istasyon zincirine cevir
        chain = []   # [(cluster_idx, line_idx_or_None)]; baslangicta giris yuruyusu
        cur = best_state
        while cur is not None:
            p, li, entry_m = prev[cur]
            chain.append((cur[0], li))
            if p is None:
                chain[-1] = (cur[0], li, entry_m)
                break
            cur = p
        chain.reverse()

        results.append({
            "total_min": total_min,
            "walk_out_m": walk_out,
            "chain": chain,
        })

    results.sort(key=lambda r: r["total_min"])

    routes = []
    for cand in results[:max_routes]:
        legs = []
        chain = cand["chain"]

        # Giristeki yuruyus
        entry = chain[0][2] if len(chain[0]) > 2 else 0
        if entry > 60:
            first = net["clusters"][chain[0][0]]
            legs.append({
                "type": "walking",
                "line": None,
                "name": "Yürüme",
                "route_id": "rail-walk-in",
                "distance_m": round(entry),
                "departure_time": None,
                "arrival_time": None,
                "from_stop": None,
                "to_stop": first["name"],
                "stops": [],
                "alternate_lines": [],
                "coords": [[start_lat, start_lon], [first["lat"], first["lon"]]],
            })

        # Rayli ayaklari hattara gore grupla (binis istasyonu = onceki dugum)
        # Ayni ref (orn. B1 iki ayrı OSM relation) tek ayak sayilir.
        def _ref(li):
            return net["lines"][li].get("ref") or net["lines"][li].get("name") or str(li)

        rail_groups = []   # [(line_idx, [cluster_idx, ...])]
        prev_node = chain[0][0]
        for c, li in chain[1:]:
            if li is None:
                prev_node = c
                continue
            if rail_groups and _ref(rail_groups[-1][0]) == _ref(li):
                rail_groups[-1][1].append(c)
            else:
                rail_groups.append((li, [prev_node, c]))
            prev_node = c

        for line_idx, clusters_seq in rail_groups:
            line = net["lines"][line_idx]
            stations = [net["clusters"][c]["name"] for c in clusters_seq]

            coords = [[net["clusters"][c]["lat"], net["clusters"][c]["lon"]] for c in clusters_seq]
            if line.get("path"):
                coords = line["path"]

            leg_dist = sum(
                _haversine_m(net["clusters"][a]["lat"], net["clusters"][a]["lon"],
                             net["clusters"][b]["lat"], net["clusters"][b]["lon"])
                for a, b in zip(clusters_seq, clusters_seq[1:])
            )

            legs.append({
                "type": _line_leg_type(line),
                "line": line["ref"],
                "name": line["name"],
                "route_id": f"rail-{line_idx}",
                "distance_m": round(leg_dist),
                "departure_time": None,
                "arrival_time": None,
                "from_stop": stations[0],
                "to_stop": stations[-1],
                "stops": stations,
                "alternate_lines": [],
                "coords": coords,
            })

        # Cikistaki yuruyus
        if cand["walk_out_m"] > 60:
            last = net["clusters"][chain[-1][0]]
            legs.append({
                "type": "walking",
                "line": None,
                "name": "Yürüme",
                "route_id": "rail-walk-out",
                "distance_m": round(cand["walk_out_m"]),
                "departure_time": None,
                "arrival_time": None,
                "from_stop": last["name"],
                "to_stop": None,
                "stops": [],
                "alternate_lines": [],
                "coords": [[last["lat"], last["lon"]], [end_lat, end_lon]],
            })

        walk_total = sum(l["distance_m"] for l in legs if l["type"] == "walking")

        routes.append({
            "fee": None,
            "walking_distance_m": round(walk_total),
            "calories_burned": None,
            "co2_emission": None,
            "departure_time": None,
            "arrival_time": None,
            "duration_minutes": round(cand["total_min"]),
            "legs": legs,
        })

    if not routes:
        return {
            "status": "no_route",
            "routes": [],
            "error": "Bu guzergah icin rayli ag uzerinde baglanti bulunamadi.",
            "source": "Metro İstanbul",
        }

    return {
        "status": "success",
        "routes": routes,
        "source": "Metro İstanbul",
    }
