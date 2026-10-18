
import json
import os
import ssl
from pathlib import Path
from urllib.parse import urlparse

import certifi
from dotenv import load_dotenv
from neo4j import GraphDatabase

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

INPUT_FILE = BASE_DIR / "graph_data.json"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def load_graph_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "graph_data.json not found. Run extract_graph.py first."
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    nodes = data.get("nodes", [])
    relationships = data.get("relationships", [])

    departments = [
        node for node in nodes
        if node.get("label") == "Department"
    ]
    schemes = [
        node for node in nodes
        if node.get("label") == "Scheme"
    ]

    if len(departments) != 1:
        raise ValueError("Expected exactly one Department node.")

    if len(schemes) != 54:
        raise ValueError(
            f"Expected 54 schemes, found {len(schemes)}."
        )

    if len(relationships) != 54:
        raise ValueError(
            f"Expected 54 relationships, found {len(relationships)}."
        )

    if any(not scheme.get("name") for scheme in schemes):
        raise ValueError("A scheme is missing its name.")

    return departments[0], schemes


def main():
    if not all([NEO4J_URI, NEO4J_PASSWORD]):
        raise ValueError(
            "Check NEO4J_URI and NEO4J_PASSWORD in your .env file."
        )

    host = urlparse(NEO4J_URI).hostname

    if not host:
        raise ValueError("Invalid NEO4J_URI in .env.")

    department, schemes = load_graph_data()

    driver = GraphDatabase.driver(
        f"bolt://{host}",
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        encrypted=True,
        ssl_context=ssl.create_default_context(
            cafile=certifi.where()
        ),
    )

    try:
        driver.verify_connectivity()

        with driver.session(database=NEO4J_DATABASE) as session:
            session.run("RETURN 1 AS test").single()

            # Step 1: Create constraints separately from data writes.
            session.run("""
                CREATE CONSTRAINT department_name_unique IF NOT EXISTS
                FOR (d:Department)
                REQUIRE d.name IS UNIQUE
            """).consume()

            session.run("""
                CREATE CONSTRAINT scheme_name_unique IF NOT EXISTS
                FOR (s:Scheme)
                REQUIRE s.name IS UNIQUE
            """).consume()

            # Step 2: Replace the graph in one data transaction.
            def replace_graph(tx):
                tx.run("MATCH (n) DETACH DELETE n").consume()

                tx.run("""
                    CREATE (d:Department {
                        id: $id,
                        name: $name
                    })
                """, id=department["id"],
                     name=department["name"]).consume()

                for scheme in schemes:
                    properties = {
                        key: value
                        for key, value in scheme.items()
                        if key not in {"id", "label"}
                    }

                    tx.run("""
                        CREATE (s:Scheme)
                        SET s = $properties
                    """, properties=properties).consume()

                tx.run("""
                    MATCH (d:Department)
                    MATCH (s:Scheme)
                    WHERE s.department = d.name
                    CREATE (d)-[:OFFERS]->(s)
                """).consume()

            session.execute_write(replace_graph)

            # Step 3: Verify the stored graph.
            result = session.run("""
                MATCH (d:Department)
                OPTIONAL MATCH (d)-[r:OFFERS]->(s:Scheme)
                RETURN count(DISTINCT d) AS departments,
                       count(DISTINCT s) AS schemes,
                       count(r) AS relationships
            """).single()

            print("\nNeo4j graph updated successfully.")
            print(f"Departments:   {result['departments']}")
            print(f"Schemes:       {result['schemes']}")
            print(f"Relationships: {result['relationships']}")

            sample = session.run("""
                MATCH (s:Scheme)
                RETURN s.name AS name,
                       s.beneficiaries AS beneficiaries,
                       s.description AS description
                ORDER BY s.name
                LIMIT 1
            """).single()

            if sample:
                print("\nSample stored scheme:")
                print(f"Name: {sample['name']}")
                print(f"Beneficiaries: {sample['beneficiaries']}")
                print(f"Description: {sample['description']}")

    finally:
        driver.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nERROR: {error}")
        print("Check the input data and Neo4j connection.")
