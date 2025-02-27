import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
#from wordcloud import WordCloud
import matplotlib.pyplot as plt
from pyvis.network import Network
import streamlit.components.v1 as components
import community.community_louvain as community_louvain
import matplotlib.colors as mcolors

# Set page configuration
st.set_page_config(layout="wide", page_title="Greek Songs Dashboard", initial_sidebar_state="expanded")

# Apply dark mode styling
st.markdown("""
    <style>
        body { background-color: #121212; color: white; }
    </style>
""", unsafe_allow_html=True)

# Load data from GitHub
df = pd.read_csv("https://raw.githubusercontent.com/gskarp/greek-songs/main/greece-songs2.csv", encoding="utf-8")

# Ensure 'Year' is numeric
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df = df.dropna(subset=['Year'])

# Sidebar Filters
st.sidebar.header("Filters")
year_range = st.sidebar.slider("Select Year Range", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
df_filtered = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]

# Visualization: Yearly Song Count
st.header("Songs Released Per Year")
year_counts = df_filtered["Year"].value_counts().sort_index()
fig = px.bar(x=year_counts.index, y=year_counts.values, labels={'x': 'Year', 'y': 'Number of Songs'}, title="Songs Per Year")
st.plotly_chart(fig)

# Network Graph (if Singer collaborations exist)
st.header("Singer Collaboration Network")
G = nx.Graph()
for _, row in df_filtered.iterrows():
    singers = str(row["Singer"]).split(" & ")
    for i in range(len(singers)):
        for j in range(i + 1, len(singers)):
            G.add_edge(singers[i], singers[j])

nt = Network(height="500px", width="100%", bgcolor="#121212", font_color="white")
nt.from_nx(G)
nt.save_graph("network.html")
components.html(open("network.html", "r", encoding="utf-8").read(), height=520)

st.success("Dashboard Loaded Successfully!")
