#!/usr/bin/env python3
"""Render graph.json as a minimalist PNG: one colour, black background.

- spring_layout = the simulation engine (edges = springs, nodes repel).
- stronger repulsion (larger k) spreads the layout out.
- circles sized by # connections; small labels beside them.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

DOC = "graph.json"
OUT = "graph.png"

INK = "#eaeaea"
BG = "#000000"

with open(DOC, encoding="utf-8") as f:
    doc = json.load(f)

G = nx.Graph()
for n in doc["nodes"]:
    G.add_node(n["id"])
for e in doc["edges"]:
    G.add_edge(e["source"], e["target"])

deg = dict(G.degree())
maxdeg = max(deg.values()) or 1

# --- force simulation: stronger repulsion via a larger k --------------------
pos = nx.spring_layout(G, k=6.0 / (len(G) ** 0.5), iterations=600, seed=7)

fig, ax = plt.subplots(figsize=(24, 18), dpi=110)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# faint single-colour edges
nx.draw_networkx_edges(G, pos, ax=ax, edge_color=INK, width=0.4, alpha=0.10)

# circles sized by connection count
node_sizes = [40 + 1600 * (deg[n] / maxdeg) ** 1.15 for n in G.nodes()]
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                       node_color=INK, linewidths=0, edgecolors=BG)

# small labels sitting just below each circle
for n in G.nodes():
    fs = 5 + 4 * (deg[n] / maxdeg)
    off = 0.012 + 0.022 * (deg[n] / maxdeg)
    ax.text(pos[n][0], pos[n][1] - off, n, fontsize=fs, ha="center", va="top",
            color=INK, zorder=5)

ax.axis("off")
ax.margins(0.06)
plt.savefig(OUT, facecolor=BG, bbox_inches="tight", pad_inches=0.4)
print(f"wrote {OUT}  ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
