"""Entity Resolver: Groups extracted facts by canonical entity_key across documents."""

import json
import hashlib
from typing import List, Dict
from src.models.domain import ExtractedFact, ProjectRegisterEntry, ProjectRegister, SourceCitation


def group_facts_by_entity(facts: List[ExtractedFact]) -> Dict[str, List[ExtractedFact]]:
    """Group extracted facts by entity_key."""
    grouped: Dict[str, List[ExtractedFact]] = {}
    for f in facts:
        key = f.entity_key
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(f)
    return grouped


def resolve_entity_history(facts: List[ExtractedFact]) -> List[ProjectRegisterEntry]:
    """Resolve facts for each entity_key into a clean ProjectRegisterEntry with full audit trail."""
    grouped = group_facts_by_entity(facts)
    entries: List[ProjectRegisterEntry] = []

    for key, fact_list in grouped.items():
        if not fact_list:
            continue

        # Sort facts by timestamp / document date heuristic
        sorted_facts = sorted(fact_list, key=lambda x: x.extracted_at)
        latest_fact = sorted_facts[-1]

        # Determine status
        values = set([f.raw_value for f in fact_list])
        if len(values) == 1 and len(fact_list) > 1:
            status = "CORROBORATED"
        elif len(values) > 1:
            status = "CONTRADICTED"
        else:
            status = "SINGLE_SOURCE"

        history = [
            {
                "doc_name": f.citation.filename,
                "raw_value": f.raw_value,
                "normalized": f.normalized_value,
                "location": f.citation.location,
                "quote": f.citation.exact_quote,
            }
            for f in sorted_facts
        ]

        entries.append(ProjectRegisterEntry(
            entity_key=key,
            title=key.replace(":", " ").replace("_", " ").title(),
            reconciled_value=latest_fact.raw_value,
            unit=latest_fact.unit,
            status=status,
            primary_citation=latest_fact.citation,
            history=history
        ))

    return entries


def reconcile_facts(project_id: str, project_name: str, facts: List[ExtractedFact]) -> ProjectRegister:
    """Reconcile facts and compile ProjectRegister object."""
    entries = resolve_entity_history(facts)
    content_hash = hashlib.sha256(json.dumps([e.model_dump() for e in entries], default=str).encode()).hexdigest()[:12]
    return ProjectRegister(
        project_id=project_id,
        project_name=project_name,
        content_hash=content_hash,
        entries=entries
    )
