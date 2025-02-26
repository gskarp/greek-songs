#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 23:17:17 2025

@author: yannis
"""
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

# Set dark mode
st.set_page_config(layout="wide", page_title="Greek Songs Dashboard", initial_sidebar_state="expanded")
st.markdown(""" <style> body { background-color: #121212; color: white; } </style> """, unsafe_allow_html=True)

# Load data
csv_url = "https://raw.githubusercontent.com/gskarp/greek-songs/main/greece-songs2.csv"
df = pd.read_csv(csv_url, sep=";", encoding="utf-8-sig")

# Convert year column to numeric format
df['Year'] = pd.to_numeric(df['Publication_Year'], errors='coerce')
df = df.dropna(subset=['Year'])
df['Year'] = df['Year'].astype(int)

# Sidebar Filters
st.sidebar.title("Network Filters")
decades = sorted(set(df['Year'] // 10 * 10))
decade = st.sidebar.selectbox("Select a Decade", options=decades)
date_range = st.sidebar.slider("Select Year Range", int(df['Year'].min()), int(df['Year'].max()), (int(df['Year'].min()), int(df['Year'].max())))

# Songs per Year (Bottom Graph)
yearly_counts = df.groupby("Year").size().reset_index(name="Number of Songs")
fig = go.Figure()
fig.add_trace(go.Bar(x=yearly_counts["Year"], y=yearly_counts["Number of Songs"], name="Bar", marker_color='orange'))
fig.add_trace(go.Scatter(x=yearly_counts["Year"], y=yearly_counts["Number of Songs"], mode='lines+markers', name="Line", line=dict(color='orange')))
fig.update_layout(title="Number of Songs per Year", xaxis_title="Year", yaxis_title="Number of Songs", hovermode="x")
st.plotly_chart(fig)

# Top 20 People Graph (Top Left)
role_selection = st.selectbox("Select Role", ["Composers", "Lyricists", "Singers", "People"])
role_map = {"Composers": "Composer", "Lyricists": "Lyricist", "Singers": "Singer"}
if role_selection != "People":
    counts = df[role_map[role_selection]].value_counts().head(20)
else:
    df_melted = pd.melt(df, value_vars=['Composer', 'Lyricist', 'Singer'])
    counts = df_melted['value'].value_counts().head(20)
fig_top = px.bar(counts, orientation='h', title=f"Top 20 {role_selection}", labels={"index": role_selection, "value": "Number of Songs"}, color_discrete_sequence=['orange'])
st.plotly_chart(fig_top)

# Word Cloud Placeholder (Commented out for now)
#st.title("Word Clouds")
#col1, col2, col3 = st.columns(3)
#with col1:
#    st.subheader("Album Titles")
#    wordcloud_album = WordCloud(width=800, height=400, background_color='black', colormap='gray').generate(text_album)
#    plt.imshow(wordcloud_album, interpolation='bilinear')
#    plt.axis("off")
#    st.pyplot(plt)
#with col2:
#    st.subheader("Song Titles")
#    wordcloud_songs = WordCloud(width=800, height=400, background_color='black', colormap='gray').generate(text_songs)
#    plt.imshow(wordcloud_songs, interpolation='bilinear')
#    plt.axis("off")
#    st.pyplot(plt)
#with col3:
#    st.subheader("Lyrics")
#    wordcloud_lyrics = WordCloud(width=800, height=400, background_color='black', colormap='gray').generate(text_lyrics)
#    plt.imshow(wordcloud_lyrics, interpolation='bilinear')
#    plt.axis("off")
#    st.pyplot(plt)

# Network Graph (Bottom)
st.title("Collaboration Network")
df_filtered = df[(df['Year'] >= date_range[0]) & (df['Year'] <= date_range[1])]
G = nx.Graph()

for _, row in df_filtered.iterrows():
    people = set(row[[''Composer', 'Lyricist', 'Singer']].dropna())
    for person in people:
        G.add_node(person)
    for p1 in people:
        for p2 in people:
            if p1 != p2:
                if G.has_edge(p1, p2):
                    G[p1][p2]['weight'] += 1
                else:
                    G.add_edge(p1, p2, weight=1)

# Compute modularity classes
partition = community_louvain.best_partition(G)
class_counts = pd.Series(partition).value_counts()
top_classes = class_counts.nlargest(10).index

# Define color map
colors = list(mcolors.TABLEAU_COLORS.values())[:10]
def get_node_color(node):
    class_id = partition[node]
    if class_id in top_classes:
        return colors[top_classes.tolist().index(class_id) % len(colors)]  # Avoid index errors
    return "grey"

# Define node size based on degree
def get_node_size(node):
    return 5 + G.degree(node) * 2  # Base size of 5, scaling with degree

# Create Pyvis network
net = Network(height='1000px', width='100%', notebook=False)
for node in G.nodes():
    net.add_node(node, color=get_node_color(node), size=get_node_size(node))

for edge in G.edges(data=True):
    net.add_edge(edge[0], edge[1], width=edge[2]['weight'])

net.write_html("network.html")
components.html(open("network.html").read(), height=1000)
