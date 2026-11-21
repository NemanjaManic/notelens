"""Development retrieval metrics for reviewed alternative evidence bundles."""

import hashlib


def alternative_topic_metrics(passages, topic_sets):
    """Score one complete reference set, never the union of competing sets.

    The passage budget is applied before deduplicating topics. MRR uses the
    first acceptable topic among that unique-topic sequence, matching the
    existing RAG development convention. It does not measure semantic support.
    """
    if not topic_sets:
        return None
    targets = [frozenset(topics) for topics in topic_sets]
    if any(not topics or any(not isinstance(t, str) or not t for t in topics) for topics in targets):
        raise ValueError('Reference topic sets must contain nonempty topic IDs.')
    targets = sorted(set(targets), key=lambda topics: tuple(sorted(topics)))
    unique = list(dict.fromkeys(p['topic_id'] for p in passages[:5]))
    found = set(unique)
    recalls = [len(found & topics) / len(topics) for topics in targets]
    relevant = set().union(*targets)
    first = next((rank for rank, topic in enumerate(unique, 1) if topic in relevant), None)
    return {'recall_at_5': max(recalls),
            'reciprocal_rank_at_5': 1 / first if first else 0.0,
            'all_required_topics_at_5': any(topics <= found for topics in targets),
            'any_reference_set_over_five_topics': any(len(topics) > 5 for topics in targets)}


def evidence_at_five(passages, options, additional_context=()):
    """Require every passage in at least one reviewed evidence option."""
    if not options:
        return None
    if any(not option for option in options):
        raise ValueError('An evidence option cannot be empty.')
    found = {p['passage_id'] for p in passages[:5]}
    context = {ref['passage_id'] for ref in additional_context}
    return context <= found and any({ref['passage_id'] for ref in option} <= found for option in options)


def verify_reference(reference, passages):
    """Verify an exact code-point slice in the pinned passage collection."""
    try:
        passage = passages[reference['passage_id']]
        start, end = reference['passage_start'], reference['passage_end']
        valid = (type(start) is int and type(end) is int and 0 <= start < end <= len(passage['text'])
                 and reference['topic_id'] == passage['topic_id']
                 and reference['topic_start'] == passage['start'] + start
                 and reference['topic_end'] == passage['start'] + end)
        if not valid:
            raise ValueError('Reference coordinates do not match the canonical passage.')
        quote = passage['text'][start:end]
        if hashlib.sha256(quote.encode('utf-8')).hexdigest() != reference['quote_sha256']:
            raise ValueError('Reference quote digest does not match the canonical slice.')
    except (KeyError, TypeError) as exc:
        raise ValueError('Reference identity or coordinates are missing.') from exc
