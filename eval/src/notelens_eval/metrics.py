"""One-to-one matching: maximum cardinality, then maximum overlap, stable ties."""


def match(predictions: list[dict], references: list[dict], *, relaxed: bool = False) -> list[tuple[int, int]]:
    # Unit-capacity min-cost flow. Augment until no path: maximum cardinality.
    # Negative overlap costs choose maximum total overlap at that cardinality.
    n, m = len(predictions), len(references)
    sink = 1 + n + m
    graph = [[] for _ in range(sink + 1)]

    def edge(a, b, cost):
        graph[a].append([b, len(graph[b]), 1, cost])
        graph[b].append([a, len(graph[a]) - 1, 0, -cost])
        return graph[a][-1]

    for i in range(n):
        edge(0, 1 + i, 0)
    for j in range(m):
        edge(1 + n + j, sink, 0)
    candidates = []
    for i, p in enumerate(predictions):
        for j, r in enumerate(references):
            if (p["doc_id"], p["type"]) != (r["doc_id"], r["type"]):
                continue
            pa, pb = p["mention"]["start"], p["mention"]["end"]
            ra, rb = r["mention"]["start"], r["mention"]["end"]
            overlap = min(pb, rb) - max(pa, ra)
            if overlap > 0 and (relaxed or (pa, pb) == (ra, rb)):
                candidates.append((i, j, edge(1 + i, 1 + n + j, -overlap)))
    while True:
        distances = [float("inf")] * len(graph)
        distances[0] = 0
        previous = {}
        for _ in range(len(graph) - 1):
            changed = False
            for a, outgoing in enumerate(graph):
                for k, (b, _, capacity, cost) in enumerate(outgoing):
                    if capacity and distances[a] + cost < distances[b]:
                        distances[b] = distances[a] + cost
                        previous[b] = (a, k)
                        changed = True
            if not changed:
                break
        if sink not in previous:
            break
        node = sink
        while node:
            a, k = previous[node]
            forward = graph[a][k]
            forward[2] -= 1
            graph[node][forward[1]][2] += 1
            node = a
    return [(i, j) for i, j, e in candidates if e[2] == 0]


def entity_scores(predictions: list[dict], references: list[dict], *, relaxed: bool = False) -> dict:
    pairs = match(predictions, references, relaxed=relaxed)
    tp, fp, fn = len(pairs), len(predictions) - len(pairs), len(references) - len(pairs)
    result = {"tp": tp, "fp": fp, "fn": fn,
              "precision": tp / (tp + fp) if tp + fp else None,
              "recall": tp / (tp + fn) if tp + fn else None,
              "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}
    for attribute in ("assertion", "temporality", "subject"):
        eligible = [(p, r) for p, r in pairs if references[r].get(attribute) is not None]
        correct = sum(predictions[p].get(attribute) == references[r][attribute] for p, r in eligible)
        result[attribute] = {"correct": correct, "matched_evaluated": len(eligible),
                             "excluded_unresolved": tp - len(eligible),
                             "accuracy": correct / len(eligible) if eligible else None}
    return result


def prediction_mentions(document: dict, items: list[dict]) -> list[dict]:
    """Provisional adapter: infer exact name interval within item evidence.

    Ambiguous names fail instead of picking a repeated occurrence arbitrarily.
    This adapter must be replaced/reviewed if B adopts a mention span field.
    """
    result = []
    for item in items:
        span = item["evidence"][0]
        quote, name = span["quote"], item["name"]
        start = quote.casefold().find(name.casefold())
        # Case folding may change length; require the original substring too.
        if start < 0 or quote[start:start + len(name)].casefold() != name.casefold() or quote.casefold().find(name.casefold(), start + 1) >= 0:
            raise ValueError("Cannot resolve a unique entity mention from evidence.")
        result.append({"doc_id": document["doc_id"], "type": item["type"],
                       "mention": {"start": span["start"] + start, "end": span["start"] + start + len(name)},
                       **{a: item[a] for a in ("assertion", "temporality", "subject")}})
    return result
