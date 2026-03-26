import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import folium_static

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FleetAI Pro", layout="wide")

# ---------------- UI STYLE ----------------
st.markdown("""
<style>

/* Full background image */
[data-testid="stAppViewContainer"] {
    background: url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

/* Dark overlay for readability */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.75);
    z-index: 0;
}

/* Make content appear above overlay */
.block-container {
    position: relative;
    z-index: 1;
    color: white;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.9);
}

/* Cards */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08);
    padding: 15px;
    border-radius: 10px;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 8px;
    border: none;
}

</style>
""", unsafe_allow_html=True)
# ---------------- SESSION ----------------
st.session_state.users = {"admin": "1234"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = ""

# ---------------- AUTH ----------------
def login():
    st.markdown("<h2 style='text-align:center;'>🔐 Login</h2>", unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username in st.session_state.users and st.session_state.users[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("Login successful ✅")
            st.rerun()
        else:
            st.error("Invalid credentials ❌")

def signup():
    st.markdown("<h2 style='text-align:center;'>📝 Sign Up</h2>", unsafe_allow_html=True)

    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")

    if st.button("Create Account"):
        if new_user in st.session_state.users:
            st.error("User already exists ❌")
        elif new_user == "" or new_pass == "":
            st.error("Fields cannot be empty ❌")
        else:
            st.session_state.users[new_user] = new_pass
            st.success("Account created! Go to Login ✅")

def logout():
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ---------------- MENU ----------------
menu = ["Login", "Sign Up"]

if not st.session_state.logged_in:
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "Login":
        login()
    else:
        signup()

    st.stop()

# ---------------- DASHBOARD ----------------
st.markdown("<h1 style='text-align:center; color:#38bdf8;'>🚚 FleetAI Pro Dashboard</h1>", unsafe_allow_html=True)
logout()

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

# ---------------- FUNCTIONS ----------------
def distance(a, b):
    return np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def optimize_route(coords):
    visited = [False]*len(coords)
    route = [0]
    visited[0] = True

    for _ in range(len(coords)-1):
        last = route[-1]
        next_city = None
        min_dist = float('inf')

        for i in range(len(coords)):
            if not visited[i]:
                d = distance(coords[last], coords[i])
                if d < min_dist:
                    min_dist = d
                    next_city = i

        route.append(next_city)
        visited[next_city] = True

    return route

def split_routes(route, num_vehicles):
    chunk_size = len(route) // num_vehicles
    routes = []

    for i in range(num_vehicles):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i != num_vehicles - 1 else len(route)
        routes.append(route[start:end])

    return routes

def create_map(df, routes):
    center = [df['latitude'].mean(), df['longitude'].mean()]
    m = folium.Map(location=center, zoom_start=11)

    colors = ["red", "blue", "green", "purple", "orange"]

    for v, route in enumerate(routes):
        points = []

        for i, idx in enumerate(route):
            lat = df.iloc[idx]['latitude']
            lon = df.iloc[idx]['longitude']
            name = df.iloc[idx]['location']

            icon_color = "green" if i == 0 else colors[v % len(colors)]

            folium.Marker(
                [lat, lon],
                popup=f"Vehicle {v+1}<br>Stop {i}<br>{name}",
                icon=folium.Icon(color=icon_color)
            ).add_to(m)

            points.append((lat, lon))

        folium.PolyLine(points, color=colors[v % len(colors)], weight=4).add_to(m)

    return m

# ---------------- MAIN ----------------
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.strip().str.lower()

    st.subheader("📊 Data Preview")
    st.dataframe(df)

    num_vehicles = st.slider("🚚 Number of Vehicles", 1, 5, 2)

    if st.button("🚀 Optimize Fleet"):

        coords = list(zip(df['latitude'], df['longitude']))
        route = optimize_route(coords)
        routes = split_routes(route, num_vehicles)

        st.subheader("🚚 Vehicle Routes")

        total_distances = []

        for i, r in enumerate(routes):
            st.write(f"### Vehicle {i+1}")
            dist = 0

            for j in range(len(r)-1):
                dist += distance(coords[r[j]], coords[r[j+1]])

            total_distances.append(dist)

            for idx in r:
                st.write(f"➡️ {df.iloc[idx]['location']}")

            st.metric(f"Distance Vehicle {i+1}", f"{dist:.2f}")
            st.write(f"💰 Cost: ₹{dist*10:.2f}")

        # Chart
        fig = px.bar(
            x=[f"V{i+1}" for i in range(len(routes))],
            y=total_distances,
            labels={"x": "Vehicle", "y": "Distance"},
            title="Distance per Vehicle"
        )
        st.plotly_chart(fig)

        # Map
        st.subheader("🗺️ Fleet Map")
        m = create_map(df, routes)
        folium_static(m)

else:
    st.info("Upload a CSV file to start 🚀")