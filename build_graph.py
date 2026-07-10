#!/usr/bin/env python3
"""Parse the survey CSV into a social-graph document (graph.json).

Each row = one respondent (col 3 "What is your name?") who ticked everyone
they know (col 2). We treat "knows" as an undirected edge. Respondent names
are written in a shorter/different form than the checkbox labels, so we
canonicalise both sides through an alias table before building the graph.
"""
import csv
import json
import re
from collections import defaultdict

SRC = "responses.csv"
OUT = "graph.json"

# Map any raw spelling -> canonical display name.
# Left side is lower-cased & stripped before lookup.
ALIAS = {
    "artem": "Artem",
    "rami": "Mohamed \"Rami\" Gaily",
    "mohamed \"rami\" gaily": "Mohamed \"Rami\" Gaily",
    "art": "Art Kobar",
    "arsenii konstantinov": "Arsenii Kosntantinov",
    "arsenii kosntantinov": "Arsenii Kosntantinov",
    "vaishnav": "vaishnav rane",
    "vaishnav rane": "vaishnav rane",
    "adi": "Aditya",
    "lassi riihelä": "Lassi",
    "maire": "maire salin",
    "aura kouri": "Aura",
    "viia": "Viia Pölönen",
    "elias leinonen": "Elias",
    "vinh": "Vinh Nguyen",
    "nia kellas": "Nia",
    "aishwarya trehan": "aishwarya",
    "petr": "Petr Podlozny",
    "caeden": "Caeden",
    "ivar åkerholm": "Ivar",
}


def canon(raw: str) -> str:
    n = raw.strip()
    key = n.lower()
    if key in ALIAS:
        return ALIAS[key]
    return n


def split_selection(cell: str):
    # names are comma separated, but "Mohamed "Rami" Gaily" contains a comma-free
    # nickname in quotes; the csv module already stripped the outer quoting so we
    # just split on commas.
    return [p.strip() for p in cell.split(",") if p.strip()]


def main():
    # respondent -> set of people they said they know
    knows = defaultdict(set)
    respondents = []

    with open(SRC, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 3:
                continue
            _ts, selections, name = row[0], row[1], row[2]
            me = canon(name)
            respondents.append(me)
            for other in split_selection(selections):
                o = canon(other)
                if o and o != me:
                    knows[me].add(o)

    # Build undirected edge set. mutual = both directions present.
    all_nodes = set()
    for a, outs in knows.items():
        all_nodes.add(a)
        all_nodes.update(outs)

    edge_dir = set()  # (a, b) directed pairs actually reported
    for a, outs in knows.items():
        for b in outs:
            edge_dir.add((a, b))

    edges = {}  # frozenset(a,b) -> {"mutual": bool}
    for (a, b) in edge_dir:
        key = tuple(sorted((a, b)))
        mutual = (b, a) in edge_dir
        if key not in edges:
            edges[key] = mutual
        else:
            edges[key] = edges[key] or mutual

    degree = defaultdict(int)
    for (a, b) in edges:
        degree[a] += 1
        degree[b] += 1

    resp_set = set(respondents)
    nodes = []
    for n in sorted(all_nodes):
        nodes.append({
            "id": n,
            "degree": degree.get(n, 0),
            "responded": n in resp_set,
        })

    edge_list = []
    for (a, b), mutual in sorted(edges.items()):
        edge_list.append({"source": a, "target": b, "mutual": mutual})

    doc = {
        "meta": {
            "source": SRC,
            "node_count": len(nodes),
            "edge_count": len(edge_list),
            "respondent_count": len(resp_set),
            "mutual_edges": sum(1 for e in edge_list if e["mutual"]),
        },
        "nodes": nodes,
        "edges": edge_list,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    # Also emit as a JS assignment so index.html works over file:// (no fetch).
    with open("graph-data.js", "w", encoding="utf-8") as f:
        f.write("window.GRAPH = ")
        json.dump(doc, f, ensure_ascii=False)
        f.write(";\n")

    print(json.dumps(doc["meta"], ensure_ascii=False, indent=2))
    print("\nTop 10 by connections:")
    for n in sorted(nodes, key=lambda x: -x["degree"])[:10]:
        tag = "*" if n["responded"] else " "
        print(f'  {tag} {n["degree"]:3d}  {n["id"]}')
    print("\nNon-respondents (named but never filled the form):")
    non = [n["id"] for n in nodes if not n["responded"]]
    print("  " + ", ".join(non))


if __name__ == "__main__":
    main()
