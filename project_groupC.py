import streamlit as st
import json
import heapq
from PIL import Image
from pyzbar.pyzbar import decode

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Parcel Delivery Tracking System",
    page_icon="📦",
    layout="wide"
)

# --- CSS ---
st.markdown(
    """
    <style>
    .equal-box {
        display: flex;
        align-items: stretch;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- LOAD ORDER DATA ---
@st.cache_data
def load_orders():
    with open("order.json", "r") as f:
        orders = json.load(f)
    return {o["order_id"]: o for o in orders}

ORDERS = load_orders()

# --- QR DECODER ---
def decode_qr(upload):
    try:
        img = Image.open(upload).convert("RGB")
        decoded = decode(img)
        if not decoded:
            return None
        value = decoded[0].data.decode("utf-8").strip()
        try:
            return json.loads(value).get("order_id")
        except:
            return value
    except:
        return None

# --- START NODE ---
START_NODE = "Bentong"

# --- COST GRAPH (RM) ---
COST_GRAPH = {
    "Bentong": {"Raub": 2, "Kuala Krau": 4},
    "Raub": {"Jerantut": 6},
    "Jerantut": {"Maran": 4},
    "Kuala Krau": {"Maran": 3},
    "Maran": {"Kuantan": 3},
    "Kuantan": {}
}

# --- TIME GRAPH ---
TIME_GRAPH = {
    "Bentong": {
        "Raub": 31,
        "Kuala Krau": 71
    },
    "Raub": {
        "Jerantut": 99
    },
    "Jerantut": {
        "Maran": 78
    },
    "Kuala Krau": {
        "Maran": 59
    },
    "Maran": {
        "Kuantan": 68
    },
    "Kuantan": {}
}

# --- DIJKSTRA (MINIMUM COST) ---
def dijkstra(graph, start, goal):
    pq = [(0, start, [])]
    visited = set()

    while pq:
        cost, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        path = path + [node]

        if node == goal:
            return path, cost

        for nxt, w in graph.get(node, {}).items():
            if nxt not in visited:
                heapq.heappush(pq, (cost + w, nxt, path))

    return [], float("inf")

# --- REALISTIC ETA CALCULATION ---
def compute_realistic_eta(path, time_graph):
    total_minutes = 0
    node_times = {path[0]: 0}

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        travel_time = time_graph[u][v]
        total_minutes += travel_time
        node_times[v] = total_minutes

    return total_minutes / 60, node_times  # hours

# --- GRAPHVIZ ---
def to_graphviz(graph, path=None):
    path = path or []
    path_edges = {(path[i], path[i + 1]) for i in range(len(path) - 1)}

    lines = [
        "digraph G {",
        "rankdir=LR;",
        "graph [splines=true, overlap=false];",
        "node [shape=ellipse, style=filled, fillcolor=\"#E3F2FD\"];"
    ]

    for u, nbrs in graph.items():
        for v, w in nbrs.items():
            color = "#D32F2F" if (u, v) in path_edges else "#1E88E5"
            width = 3 if (u, v) in path_edges else 1
            lines.append(
                f"\"{u}\" -> \"{v}\" "
                f"[label=\"RM {w}\", color=\"{color}\", penwidth={width}];"
            )

    lines.append("}")
    return "\n".join(lines)

# --- UI ---
st.title("📦 Parcel Delivery Tracking System")

upload = st.file_uploader("📤 Upload Your QR Code", type=["png", "jpg", "jpeg"])

if upload:
    order_id = decode_qr(upload)

    if not order_id or order_id not in ORDERS:
        st.error("❌ Invalid Order ID")
        st.stop()

    order = ORDERS[order_id]
    st.success("✅ Order verified")
    st.divider()

    st.markdown("### 👤 Customer & Order Details")
    st.info(f"""
    **Order ID:** {order['order_id']}  
    **Customer:** {order['Customer Name']}  
    **Product:** {order['Product ID']}  
    **Quantity:** {order['Quantity']}  
    **City:** {order['City']}  
    **Postal Code:** {order['Postal Code']}
    """)

    destination = order["City"]

    # --- ROUTING ---
    path, total_cost = dijkstra(COST_GRAPH, START_NODE, destination)
    eta_hours, node_times = compute_realistic_eta(path, TIME_GRAPH)

    # --- TITLES ---
    t1, t2 = st.columns([1, 2])
    with t1:
        st.markdown("#### 🗺 Optimized Delivery Route")
    with t2:
        st.markdown("#### 📍 Delivery Route Graph")

    c1, c2 = st.columns([1, 2])

    # --- LEFT PANEL ---
    with c1:
        st.markdown('<div class="equal-box">', unsafe_allow_html=True)
        st.success(
            f"**Start Hub:** {START_NODE}\n\n"
            f"**Destination:** {destination}\n\n"
            f"**Optimized Route:** {' → '.join(path)}\n\n"
            f"**Delivery Cost:** RM {total_cost}\n\n"
            f"**Estimated Delivery Time:** ⏱ {eta_hours:.2f} hours"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RIGHT PANEL ---
    with c2:
        st.markdown('<div class="equal-box">', unsafe_allow_html=True)
        st.graphviz_chart(
            to_graphviz(COST_GRAPH, path),
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
