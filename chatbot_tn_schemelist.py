
import os
import re
import ssl
from urllib.parse import urlparse

import certifi
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


# ==========================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from .env.")

if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    raise ValueError(
        "Neo4j configuration is missing. Check your .env file."
    )


# ==========================================================
# 2. CONNECT TO NEO4J AURA
# ==========================================================

host = urlparse(NEO4J_URI).hostname

if not host:
    raise ValueError("Invalid NEO4J_URI in your .env file.")

driver = GraphDatabase.driver(
    f"bolt://{host}",
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    encrypted=True,
    ssl_context=ssl.create_default_context(
        cafile=certifi.where()
    ),
)


# ==========================================================
# 3. INITIALIZE OPENAI MODEL
# ==========================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY,
)


# ==========================================================
# 4. TEST NEO4J CONNECTION
# ==========================================================

def test_connection():
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run("RETURN 1 AS test").single()

        result = session.run(
            "MATCH (s:Scheme) RETURN count(s) AS total"
        ).single()

        return result["total"]


# ==========================================================
# 5. KEYWORDS AND SYNONYMS
# ==========================================================

STOPWORDS = {
    "find", "show", "list", "display", "which", "what",
    "where", "when", "who", "why", "the", "a", "an",
    "is", "are", "was", "were", "for", "to", "of",
    "in", "on", "and", "or", "do", "does", "did",
    "i", "we", "you", "how", "can", "could", "would",
    "should", "me", "my", "this", "that", "these",
    "those", "please", "tell", "give", "about",
    "related", "with", "scheme", "schemes", "support",
    "supports", "help", "helps", "available", "information",
    "details", "need", "want", "know", "explain"
}

SYNONYMS = {
    "farmer": ["farmer", "farmers", "agriculture"],
    "farmers": ["farmer", "farmers", "agriculture"],
    "agriculture": ["agriculture", "farmer", "farmers"],
    "maize": ["maize", "corn"],
    "corn": ["corn", "maize"],
    "eligible": ["eligible", "eligibility", "qualify"],
    "eligibility": ["eligible", "eligibility", "qualify"],
    "qualify": ["eligible", "eligibility", "qualify"],
    "apply": ["apply", "application", "submit"],
    "application": ["apply", "application", "submit"],
    "subsidy": ["subsidy", "subsidies", "financial assistance"],
    "subsidies": ["subsidy", "subsidies", "financial assistance"],
    "money": ["money", "financial assistance", "grant", "subsidy"],
    "benefit": ["benefit", "benefits", "assistance"],
    "benefits": ["benefit", "benefits", "assistance"],
    "training": ["training", "train"],
    "seed": ["seed", "seeds"],
    "seeds": ["seed", "seeds"],
    "women": ["women", "farm women"],
    "loan": ["loan", "loans", "credit"],
    "loans": ["loan", "loans", "credit"],
}


def prepare_keywords(question):
    words = re.findall(r"[a-zA-Z0-9]+", question.lower())
    keywords = []

    for word in words:
        if word in STOPWORDS or len(word) < 3:
            continue

        alternatives = SYNONYMS.get(word, [word])

        for alternative in alternatives:
            if alternative not in keywords:
                keywords.append(alternative)

    return keywords


# ==========================================================
# 6. SEARCH SCHEMES IN THE KNOWLEDGE GRAPH
# ==========================================================

def search_schemes(question, limit=10):
    keywords = prepare_keywords(question)

    if not keywords:
        return []

    query = """
    MATCH (d:Department)-[:OFFERS]->(s:Scheme)

    WITH d, s,
         toLower(
             coalesce(s.name, '') + ' ' +
             coalesce(s.description, '') + ' ' +
             coalesce(s.beneficiaries, '') + ' ' +
             coalesce(s.types_of_benefits, '') + ' ' +
             coalesce(s.funding_pattern, '') + ' ' +
             coalesce(s.eligibility_criteria, '') + ' ' +
             coalesce(s.how_to_apply, '') + ' ' +
             coalesce(s.income, '') + ' ' +
             coalesce(s.community, '')
         ) AS searchable_text

    WITH d, s, searchable_text,
         [word IN $keywords
          WHERE searchable_text CONTAINS word] AS matches

    WHERE size(matches) > 0

    RETURN
        s.name AS name,
        s.description AS description,
        s.beneficiaries AS beneficiaries,
        s.types_of_benefits AS benefits,
        s.funding_pattern AS funding,
        s.eligibility_criteria AS eligibility,
        s.how_to_apply AS how_to_apply,
        s.url AS url,
        d.name AS department,
        size(matches) AS match_count

    ORDER BY match_count DESC, name
    LIMIT $limit
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(
            query,
            keywords=keywords,
            limit=limit,
        )
        return result.data()


# ==========================================================
# 7. RETRIEVE ALL SCHEMES
# ==========================================================

def get_all_schemes():
    query = """
    MATCH (d:Department)-[:OFFERS]->(s:Scheme)

    RETURN
        s.name AS name,
        s.description AS description,
        s.beneficiaries AS beneficiaries,
        s.types_of_benefits AS benefits,
        s.funding_pattern AS funding,
        s.eligibility_criteria AS eligibility,
        s.how_to_apply AS how_to_apply,
        s.url AS url,
        d.name AS department

    ORDER BY name
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        return session.run(query).data()


# ==========================================================
# 8. FORMAT RETRIEVED SCHEME DETAILS
# ==========================================================

def format_context(records):
    context_parts = []

    for index, scheme in enumerate(records, start=1):
        details = f"""
Scheme {index}
Name: {scheme.get('name') or 'Not available'}
Department: {scheme.get('department') or 'Not available'}
Description: {scheme.get('description') or 'Not available'}
Beneficiaries: {scheme.get('beneficiaries') or 'Not available'}
Benefits: {scheme.get('benefits') or 'Not available'}
Funding: {scheme.get('funding') or 'Not available'}
Eligibility: {scheme.get('eligibility') or 'Not available'}
How to apply: {scheme.get('how_to_apply') or 'Not available'}
Source: {scheme.get('url') or 'Not available'}
"""
        context_parts.append(details.strip())

    return "\n\n".join(context_parts)


# ==========================================================
# 9. DETECT REQUESTS TO LIST ALL SCHEMES
# ==========================================================

def wants_all_schemes(question):
    normalized = re.sub(
        r"[^a-z0-9 ]",
        " ",
        question.lower()
    )
    normalized = " ".join(normalized.split())

    phrases = [
        "show all schemes",
        "list all schemes",
        "display all schemes",
        "all schemes",
        "show every scheme",
        "list every scheme",
        "how many schemes",
        "total number of schemes",
    ]

    return any(phrase in normalized for phrase in phrases)


# ==========================================================
# 10. GENERATE ANSWERS USING OPENAI
# ==========================================================

def answer_question(question):

    if wants_all_schemes(question):
        records = get_all_schemes()

        if not records:
            return "No schemes were found in Neo4j."

        output = [f"Total schemes found: {len(records)}"]

        for index, scheme in enumerate(records, start=1):
            output.append(
                f"\n{index}. {scheme.get('name') or 'Unnamed scheme'}"
                f"\n   Department: "
                f"{scheme.get('department') or 'Not available'}"
                f"\n   Description: "
                f"{scheme.get('description') or 'Not available'}"
                f"\n   Source: {scheme.get('url') or 'Not available'}"
            )

        return "\n".join(output)

    records = search_schemes(question, limit=10)

    if not records:
        return (
            "I couldn't find matching schemes in the stored details.\n"
            "Try a scheme name or topic such as maize, farmers, "
            "seeds, subsidy, or training."
        )

    context = format_context(records)

    system_prompt = """
You are a helpful Tamil Nadu government schemes assistant.

Answer using ONLY the information in the supplied Knowledge Graph
context.

Rules:
1. Do not invent scheme details, amounts, or eligibility rules.
2. If a detail is missing, clearly say it is not available.
3. For application questions, use the supplied How to apply field.
4. For eligibility questions, use the available description and
   eligibility field. Distinguish explicit details from missing data.
5. Include the scheme name in your answer.
6. Include the source URL when available.
7. If multiple schemes match, summarize the most relevant ones.
8. Do not assume every record belongs to Agriculture merely because
   its stored department label says so.
9. Explain uncertainty rather than making unsupported claims.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"""
User question:
{question}

Retrieved Knowledge Graph context:
{context}

Answer clearly using only the supplied context.
"""
        ),
    ]

    response = llm.invoke(messages)
    return response.content


# ==========================================================
# 11. MAIN CHAT LOOP
# ==========================================================

def main():
    try:
        total_schemes = test_connection()

        print("\n" + "=" * 60)
        print("  TAMIL NADU SCHEME KNOWLEDGE GRAPH CHATBOT")
        print("=" * 60)
        print(f"Neo4j schemes available: {total_schemes}")
        print("Retrieval: Neo4j Knowledge Graph")
        print("Answer generation: OpenAI GPT-4o-mini")
        print("Vector database: Not used")
        print("\nAsk a question about the stored schemes.")
        print("Type 'exit' to stop.")
        print("-" * 60)

        while True:
            question = input("\nYou: ").strip()

            if question.lower() in {"exit", "quit", "bye"}:
                print("Chatbot: Goodbye!")
                break

            if not question:
                print("Chatbot: Please enter a question.")
                continue

            try:
                answer = answer_question(question)
                print(f"\nChatbot:\n{answer}")

            except Exception as error:
                print(f"\nError while answering: {error}")

    except Exception as error:
        print(f"\nCould not connect to Neo4j: {error}")
        print("Check your .env settings and Neo4j database status.")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
