# stuhi-graph

A "who-knows-whom" social graph. Each person selected everyone they know; the
result is an interactive, Neo4j-Bloom-style network you can explore in the
browser.

**Live (current static version):** https://stuhi-graph-439502948711.europe-north1.run.app

![graph](graph.png)

---

## 🚧 Task for the next developer

Right now this is a **static site**: a pre-baked graph (`graph.json` /
`graph-data.js`) rendered by a single `index.html`. Anyone with the URL sees
everything, and the data can only change by re-running a Python script.

**Turn it into a proper app: TypeScript + PostgreSQL, with accounts and a
questionnaire.** Concretely:

1. **Auth is mandatory to see the graph.** No anonymous access. A visitor must
   create an account (email + password + name) or log in before the network is
   shown. Hash passwords (bcrypt/argon2), use sessions or JWT — your call, but
   keep it standard.

2. **On first arrival, after signup, the user fills the questionnaire** — the
   same "select everyone you know" step the original Google Form asked. This is
   **required before they can view the graph**: sign up → answer who-you-know →
   then the network unlocks. Their answers become edges in the live graph.

3. **The graph is served from the database, not a static JSON file.** New
   signups and new questionnaire submissions must show up in the graph. Model
   people, accounts, and the directed "knows" relationships in Postgres; derive
   nodes/edges (with the `mutual` and `degree` logic below) from those tables.

4. **Seed the database from the existing responses.** ✅ **Yes — the
   questionnaire results are already in this repo.** Do *not* start from an
   empty DB. Load them:
   - [`responses.csv`](responses.csv) — the raw form export, one row per
     respondent (41 rows): `Timestamp, Select everyone you know, What is your name?`.
   - [`build_graph.py`](build_graph.py) — reference logic for parsing that CSV,
     including the **alias table** (`ALIAS`) that merges short names ("Adi",
     "Art", "Rami", "Vinh") into canonical identities. Port this name-resolution
     into your seed/migration so the seeded graph matches today's.
   - These seeded people exist as nodes but have **no login yet** — treat them
     like the current "hollow" non-respondents until a real account claims that
     name.

5. **Reuse the exact existing design.** Keep the look of [`index.html`](index.html)
   pixel-for-pixel — the dark radial background, the blue monochrome links
   (`#6d86c8` / mutual `#9fbcff`), node sizing by degree, hover-to-isolate,
   the frosted control panel, the D3 force layout and its cooling behaviour.
   The login and questionnaire screens should feel like they belong to the same
   product (same fonts, colors, panel styling). Don't redesign — port.

**Deliverable:** a PR against `main` with the TypeScript + Postgres app, DB
schema + migrations, a seed step that loads `responses.csv`, auth, the gated
questionnaire flow, and the restyled-but-identical graph viewer. Include how to
run it locally (env vars, `DATABASE_URL`, migrate + seed commands) in this
README.

### Suggested shape (not prescriptive)
- **Backend:** TypeScript (Node) — Express/Fastify/Nest, plus a typed DB layer
  (Prisma / Drizzle / Kysely). Endpoints roughly: `POST /auth/signup`,
  `POST /auth/login`, `GET /me`, `POST /questionnaire`, `GET /graph` (auth-gated).
- **DB:** `users` (email unique, password_hash, name), `people` (canonical
  identity, may exist without a user), `knows` (from_person, to_person),
  derive edges + `mutual` + `degree` in a query or view.
- **Frontend:** keep it thin and reuse the D3 viewer from `index.html`; gate it
  behind auth + a completed questionnaire.

---

## What's here today (the static version to migrate from)

| File | What it is |
| --- | --- |
| `responses.csv` | ✅ Raw form export — **the questionnaire results to seed from.** |
| `build_graph.py` | Parses the CSV into a graph, resolving name aliases. Emits `graph.json` + `graph-data.js`. Port this logic into the seed. |
| `graph.json` | The graph document: nodes (with degree) + edges (with mutual flag). |
| `graph-data.js` | Same data as `window.GRAPH`, so the viewer works over `file://`. |
| `index.html` | Interactive force-directed viewer (D3) — **the design to reuse.** |
| `plot_graph.py` | Renders a static `graph.png` (matplotlib spring layout). |

## The graph model (keep this behaviour)

- **57 people**, **627 links**, **335 mutual** ("we both named each other"),
  from **41 respondents**.
- An edge means at least one of the two people said they know the other;
  `mutual` = both directions reported.
- **Node size = number of connections (degree).** Solid nodes filled the form;
  hollow rings were named by others but never responded.
- Name resolution is the fiddly part: people signed with short names while the
  checkboxes used full names. `build_graph.py`'s `ALIAS` table is the source of
  truth for merging identities — carry it over.

## Run the current static version

```bash
# rebuild the graph after editing responses.csv
python3 build_graph.py

# (optional) re-render the static PNG
python3 plot_graph.py

# view the interactive version
python3 -m http.server 8117
# then open http://localhost:8117
```

## Deploy (current, Cloud Run)

The viewer is a static site served by nginx (`Dockerfile` + `nginx.conf`),
built with Cloud Build and hosted on Cloud Run.

```bash
IMAGE="europe-north1-docker.pkg.dev/cleveland-464404-m0/web/stuhi-graph:latest"

# build + push the container
gcloud builds submit --tag "$IMAGE"

# deploy (public)
gcloud run deploy stuhi-graph \
  --image="$IMAGE" --region=europe-north1 \
  --allow-unauthenticated --port=8080
```

> Once the app has accounts + a database, this static/public deploy needs to
> change: the graph must sit behind auth, and Cloud Run will need a Postgres
> instance (Cloud SQL) and secrets for `DATABASE_URL` + the session secret.

## Viewer controls (behaviour to preserve)

- **Hover** a node to isolate its circle of friends.
- **Drag** nodes to rearrange; **scroll** to zoom; **drag** the background to pan.
- Sliders tune the physics (charge, link distance, link strength).
- The layout cools down and holds still — it does not jitter forever.
