import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from pyvis.network import Network
import streamlit.components.v1 as components
import community.community_louvain as community_louvain
import matplotlib.colors as mcolors

# Set page configuration
st.set_page_config(layout="wide", page_title="Greek Songs Dashboard", initial_sidebar_state="expanded")

# Apply dark mode styling for entire page and sidebar
st.markdown(
    """
    <style>
        body, .stApp, .css-1d391kg, .stSidebar { background-color: #121212; color: white; }
        .stTextInput, .stSelectbox, .stSlider, .stButton { color: white; }
    </style>
    """,
    unsafe_allow_html=True
)

# Load data
df = pd.read_csv("https://raw.githubusercontent.com/gskarp/greek-songs/main/greece-songs3.csv", encoding="utf-8")
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df = df.dropna(subset=['Year'])

# Sidebar Filters
st.sidebar.header("About")
st.sidebar.write("Greek songs since 1950, including any form of the national name 'Greece.' Actually, there are more ways to refer to the country and its people, but this will be a later addition. Data source: a compilation by Athanasios Katsaounis")

st.sidebar.header("Filters")
year_range = st.sidebar.slider("Select Year Range", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))

# Filter data based on year range
df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

# --- SONGS PER YEAR ---
st.subheader("Songs Per Year")
year_counts = df_filtered["Year"].value_counts().sort_index()
fig = go.Figure()
fig.add_trace(go.Bar(x=year_counts.index, y=year_counts.values, name="Songs", marker_color="orange"))
fig.add_trace(go.Scatter(x=year_counts.index, y=year_counts.values, mode='lines', name='Trend', line=dict(color='orange')))
fig.update_layout(plot_bgcolor='#121212', paper_bgcolor='#121212', font=dict(color='white'))
st.plotly_chart(fig, use_container_width=True)

# --- TOP 20 CHART ---
st.subheader("Top 20 Contributors")
category = st.selectbox("Select Category", ["Composers", "Lyricists", "Singers", "People"])
if category == "People":
    contributors = pd.concat([df_filtered['Composer'], df_filtered['Lyricist'], df_filtered['Singer']]).dropna()
else:
    contributors = df_filtered[category[:-1]]
top_contributors = contributors.value_counts().head(20)
fig = px.bar(top_contributors, x=top_contributors.values, y=top_contributors.index, orientation='h', title=f"Top 20 {category}", color_discrete_sequence=["orange"])
fig.update_layout(plot_bgcolor='#121212', paper_bgcolor='#121212', font=dict(color='white'))
st.plotly_chart(fig, use_container_width=True)

# --- WORD CLOUDS ---
st.subheader("Word Clouds")
fig, axes = plt.subplots(1, 3, figsize=(20, 5))
wordcloud_titles = ["Top 50 Album Title Words", "Top 50 Song Title Words", "Top 50 Lyrics Words"]
columns = ["cleanAlbum", "cleanSong", "cleanLyrics"]
for i, col in enumerate(columns):
    text = " ".join(df_filtered[col].dropna())
    wordcloud = WordCloud(background_color="white", colormap="Greys", max_words=50).generate(text)
    axes[i].imshow(wordcloud, interpolation="bilinear")
    axes[i].axis("off")
    axes[i].set_title(wordcloud_titles[i], fontsize=14, color='black')
st.pyplot(fig)

# --- NETWORK VISUALIZATION ---
st.subheader("Network Visualization")
G = nx.Graph()
for _, row in df_filtered.iterrows():
    G.add_edge(str(row["Composer"]), str(row["Lyricist"]), weight=1)
    G.add_edge(str(row["Lyricist"]), str(row["Singer"]), weight=1)
    G.add_edge(str(row["Singer"]), str(row["Composer"]), weight=1)

partition = community_louvain.best_partition(G)
nx.set_node_attributes(G, partition, 'modularity_class')
nx.set_node_attributes(G, dict(G.degree(weight='weight')), 'weighted_degree')

net = Network(height='500px', width='100%', bgcolor='white', font_color='black')
for node in G.nodes():
    net.add_node(str(node), size=G.nodes[node]['weighted_degree'] * 2, color=mcolors.CSS4_COLORS[list(mcolors.CSS4_COLORS.keys())[partition[node] % len(mcolors.CSS4_COLORS)]])
for edge in G.edges():
    net.add_edge(str(edge[0]), str(edge[1]), width=G[edge[0]][edge[1]]['weight'] / 2)

net.save_graph("network.html")
components.html(open("network.html").read(), height=500)
