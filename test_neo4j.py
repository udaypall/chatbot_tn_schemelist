
import os
import ssl

import certifi
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(".env")

uri = os.getenv("NEO4J_URI", "").strip()
username = os.getenv("NEO4J_USERNAME", "").strip()
password = os.getenv("NEO4J_PASSWORD", "")
database = os.getenv("NEO4J_DATABASE", "neo4j").strip()

if not all([uri, username, password]):
    raise SystemExit("Missing Neo4j settings in .env")

# Use the verified Instance01 hostname, but configure TLS explicitly.
host = uri.split("://", 1)[-1].split("/", 1)[0]
direct_uri = f"bolt://{host}"

tls_context = ssl.create_default_context(cafile=certifi.where())

print("Testing Neo4j with certifi TLS verification...")
print("Host:", host)

try:
    with GraphDatabase.driver(
        direct_uri,
        auth=(username, password),
        encrypted=True,
        ssl_context=tls_context,
    ) as driver:
        driver.verify_connectivity()
        print("Driver connectivity verified.")

        with driver.session(database=database) as session:
            record = session.run("RETURN 1 AS test").single()
            print("Connection successful!")
            print("Test result:", record["test"])
            print("Connected database:", database)

except Exception as e:
    print("Connection failed:", type(e).__name__)
    print("Details:", str(e))
