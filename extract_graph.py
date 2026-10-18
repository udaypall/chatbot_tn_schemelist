
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "clean_scheme_details.json"
OUTPUT_FILE = BASE_DIR / "graph_data.json"
GRAPHML_FILE = BASE_DIR / "tn_schemes.graphml"

DEPARTMENT_NAME = "Agriculture - Farmers Welfare Department"


def load_schemes():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE.name}. "
            "Run clean_scheme_details.py first."
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    schemes = data.get("schemes", [])

    if not isinstance(schemes, list):
        raise ValueError("'schemes' must be a list.")

    return schemes


def build_graph_data(schemes):
    nodes = [
        {
            "id": "department_1",
            "label": "Department",
            "name": DEPARTMENT_NAME,
        }
    ]

    relationships = []
    seen_names = set()
    scheme_number = 0

    for scheme in schemes:
        name = str(scheme.get("name", "")).strip()

        if not name:
            print("Skipping a record with an empty scheme name.")
            continue

        normalized_name = name.casefold()

        if normalized_name in seen_names:
            print(f"Skipping duplicate scheme: {name}")
            continue

        seen_names.add(normalized_name)
        scheme_number += 1

        properties = {
            "id": f"scheme_{scheme_number}",
            "label": "Scheme",
            "name": name,
            "department": scheme.get("department", ""),
            "url": scheme.get("url", ""),
            "sponsored_by": scheme.get("sponsored_by", ""),
            "funding_pattern": scheme.get("funding_pattern", ""),
            "beneficiaries": scheme.get("beneficiaries", ""),
            "types_of_benefits": scheme.get("types_of_benefits", ""),
            "income": scheme.get("income", ""),
            "age_from": scheme.get("age_from", ""),
            "age_to": scheme.get("age_to", ""),
            "community": scheme.get("community", ""),
            "eligibility_criteria": scheme.get(
                "eligibility_criteria", ""
            ),
            "how_to_apply": scheme.get("how_to_apply", ""),
            "description": scheme.get("description", ""),
            "status": scheme.get("status", ""),
        }

        nodes.append(properties)

        relationships.append(
            {
                "source": "department_1",
                "target": properties["id"],
                "type": "OFFERS",
            }
        )

    return nodes, relationships


def save_graph_data(nodes, relationships):
    output = {
        "department": DEPARTMENT_NAME,
        "node_count": len(nodes),
        "scheme_count": len(nodes) - 1,
        "relationship_count": len(relationships),
        "nodes": nodes,
        "relationships": relationships,
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)


def save_graphml(nodes, relationships):
    try:
        import networkx as nx
    except ImportError as error:
        raise RuntimeError(
            "NetworkX is required. Install it with: pip install networkx"
        ) from error

    graph = nx.DiGraph()

    for node in nodes:
        node_id = node["id"]
        attributes = {
            key: value
            for key, value in node.items()
            if key != "id"
        }
        graph.add_node(node_id, **attributes)

    for relationship in relationships:
        graph.add_edge(
            relationship["source"],
            relationship["target"],
            type=relationship["type"],
        )

    nx.write_graphml(graph, GRAPHML_FILE)


def main():
    print("=" * 60)
    print("Tamil Nadu Scheme Knowledge Graph Builder")
    print("=" * 60)

    schemes = load_schemes()
    nodes, relationships = build_graph_data(schemes)

    save_graph_data(nodes, relationships)
    save_graphml(nodes, relationships)

    print(f"\nInput scheme records: {len(schemes)}")
    print(f"Unique schemes:      {len(nodes) - 1}")
    print(f"Total nodes:         {len(nodes)}")
    print(f"Relationships:       {len(relationships)}")
    print(f"JSON output:         {OUTPUT_FILE.name}")
    print(f"GraphML output:      {GRAPHML_FILE.name}")

    # Show one example so you can verify the new properties.
    for node in nodes:
        if node.get("label") == "Scheme":
            print("\nSample scheme properties:")
            print(json.dumps(node, ensure_ascii=False, indent=2))
            break

    print("\nGraph extraction completed.")
    print("Neo4j has NOT been changed by this script.")


if __name__ == "__main__":
    main()
