# Tamil Nadu Government Schemes — Knowledge Graph RAG Chatbot

## 1. Project Overview

This project is a question-answering chatbot that helps users explore Tamil Nadu government schemes using a **Knowledge Graph Retrieval-Augmented Generation (KG-RAG)** approach.

The application retrieves relevant scheme information from a Neo4j knowledge graph and uses OpenAI's GPT-4o-mini model to generate answers based on the retrieved information.

The chatbot can help users find information about scheme benefits, beneficiaries, funding patterns, application procedures, and related details available in the collected dataset.

## 2. Objectives

- Collect scheme information from the Tamil Nadu Government scheme-list website.
- Extract and clean scheme details from individual scheme pages.
- Represent departments and schemes as a knowledge graph.
- Store and query the graph using Neo4j Aura.
- Retrieve relevant schemes in response to user questions.
- Generate context-based answers using LangChain and OpenAI.
- Provide source URLs so users can refer to the original scheme pages.

**Source website:** https://www.tn.gov.in/scheme_list.php?dep_id=Mg==

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| LangChain | LLM integration and application workflow |
| OpenAI GPT-4o-mini | Answer generation |
| Neo4j Aura | Cloud-hosted graph database |
| Cypher | Querying graph data |
| NetworkX | Graph construction and GraphML export |
| Requests and BeautifulSoup | Webpage retrieval and HTML parsing |
| python-dotenv | Loading environment variables |
| Certifi | TLS certificate verification |

## 4. Architecture

The application follows a Knowledge Graph RAG workflow.

```text
Tamil Nadu Government Website
              |
              v
      Collect Scheme Data
              |
              v
      Clean Scheme Details
              |
              v
      Build Knowledge Graph
              |
              v
       Neo4j Aura Database
              |
              v
       User's Question
              |
              v
    Keyword-Based Retrieval
              |
              v
    Relevant Scheme Context
              |
              v
    OpenAI GPT-4o-mini
              |
              v
       Answer with Sources
```

### How it works

1. Scheme information is collected from the source website and individual scheme pages.
2. The collected information is cleaned and organized into structured JSON files.
3. Departments and schemes are represented as graph nodes, connected by relationships.
4. The graph is stored in Neo4j Aura.
5. When a user asks a question, the application searches the graph using keywords and configured synonyms.
6. Retrieved scheme details are passed to GPT-4o-mini through LangChain.
7. The model generates an answer based on the retrieved context and includes source URLs where available.

**Note:** This implementation uses keyword-based graph retrieval. It does not use vector embeddings or a vector database.

## 5. Knowledge Graph Design

The current graph contains two node types:

- `Department`
- `Scheme`

The relationship is:

```text
(:Department)-[:OFFERS]->(:Scheme)
```

The current stored graph contains:

- 1 Department node
- 54 Scheme nodes
- 54 `OFFERS` relationships

The scheme records may contain properties such as:

- Scheme name
- Source URL
- Department
- Description
- Beneficiaries
- Types of benefits
- Funding pattern
- Application instructions
- Income and age information
- Community information

The availability of individual properties depends on the source data.

## 6. Project Structure

```text
chatbot_tn_schemelist/
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
│
├── chatbot_tn_schemelist.py
├── prepare_documents.py
├── fetch_scheme_details.py
├── clean_scheme_details.py
├── extract_graph.py
├── store_graph.py
├── test_neo4j.py
├── inspect_scheme_links.py
│
├── tn_schemes.txt
├── agriculture_schemes.json
├── scheme_chunks.json
├── scheme_details.json
├── clean_scheme_details.json
├── graph_data.json
└── tn_schemes.graphml
```

### Important files

| File | Purpose |
|---|---|
| `chatbot_tn_schemelist.py` | Runs the interactive chatbot |
| `prepare_documents.py` | Prepares structured scheme data and text chunks |
| `fetch_scheme_details.py` | Collects details from scheme pages |
| `clean_scheme_details.py` | Cleans and standardizes collected details |
| `extract_graph.py` | Creates graph data and exports GraphML |
| `store_graph.py` | Stores the graph in Neo4j Aura |
| `test_neo4j.py` | Tests the Neo4j connection |
| `inspect_scheme_links.py` | Helps inspect scheme links |
| `tn_schemes.txt` | Initial scheme-list text |
| `clean_scheme_details.json` | Cleaned scheme records |
| `graph_data.json` | Graph nodes and relationships |
| `tn_schemes.graphml` | GraphML export for graph inspection |

## 7. Prerequisites

Before running the application, install or configure:

- Python
- Visual Studio Code
- A Neo4j Aura database
- An OpenAI API key
- Git, if you want to publish the project to GitHub

## 8. Installation

### Step 1: Open the project folder

Open the project folder in VS Code and open its terminal.

### Step 2: Create a virtual environment

```cmd
python -m venv venv
```

### Step 3: Activate the virtual environment

```cmd
venv\Scripts\activate
```

### Step 4: Install dependencies

```cmd
python -m pip install -r requirements.txt
```

## 9. Environment Configuration

Create a `.env` file in the project root.

Add your own credentials using the following template:

```dotenv
OPENAI_API_KEY=your_openai_api_key
NEO4J_URI=neo4j+s://your_database_uri
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

Replace the placeholder values with your actual credentials.

**Security:** Never commit `.env` to GitHub. Ensure that `.env` is listed in `.gitignore`. Never place real API keys or database passwords in this README or in publicly shared screenshots.

## 10. Running the Application

### Step 1: Verify the Neo4j connection

```cmd
python test_neo4j.py
```

Confirm that the database connection succeeds.

### Step 2: Run the chatbot

```cmd
python chatbot_tn_schemelist.py
```

The application connects to Neo4j Aura, retrieves scheme information relevant to the question, and generates an answer using GPT-4o-mini.

### Example questions

```text
Find schemes related to maize.

What benefits are available under the schemes?

How can I apply for a scheme?

Show me all available schemes.

Which schemes mention financial assistance?
```

Answers depend on the information available in the collected records and the retrieval results.

## 11. Rebuilding the Knowledge Graph

If you need to rebuild the graph from the collected data, the scripts can be run in the following order:

```cmd
python prepare_documents.py
python fetch_scheme_details.py
python clean_scheme_details.py
python extract_graph.py
python store_graph.py
```

Then run the chatbot:

```cmd
python chatbot_tn_schemelist.py
```

Run these steps only when you intend to refresh the dataset. The graph-storage script clears and rebuilds the graph, so use it only with the dedicated assignment database and ensure you have a backup if needed.

## 12. Current Limitations and Data Quality

- The collected dataset contains 54 unique scheme records, while the website listing or expected count was observed as 53. This discrepancy requires verification.
- Although the source page was accessed with an Agriculture – Farmers Welfare Department filter, some collected scheme records appear to relate to MSME or industrial schemes. Department classification should be validated against the original source pages.
- The cleaned `eligibility_criteria` field is empty for the current 54 records. Some eligibility information may appear within scheme descriptions, but it is not consistently available as a separate field.
- Application instructions are available for 52 of the 54 cleaned records.
- Keyword and synonym matching can miss relevant schemes when the user's wording differs from the stored data.
- The LLM can only provide reliable answers to the extent that relevant information is retrieved and present in the source records.
- Scheme information may change. Users should verify important details on the official source website before applying.

## 13. Future Improvements

- Improve scheme classification and validate department metadata.
- Extract eligibility criteria into a dedicated, structured field.
- Improve retrieval with additional synonyms, entity matching, or hybrid retrieval.
- Add more graph relationships, such as scheme-to-beneficiary and scheme-to-benefit relationships.
- Add automated data refresh and validation.
- Build a web interface for easier interaction.
- Add tests for retrieval accuracy and answer grounding.

## 14. Conclusion

This project demonstrates how a Knowledge Graph RAG chatbot can combine structured graph data, Neo4j, LangChain, and an LLM to answer questions about government schemes.

It separates information retrieval from answer generation, supports source-linked responses, and provides a foundation for building more reliable domain-specific assistants.

---

**Project:** Tamil Nadu Government Schemes — Knowledge Graph RAG Chatbot  
**Database:** Neo4j Aura  
**LLM:** OpenAI GPT-4o-mini  
**Retrieval approach:** Keyword-based Knowledge Graph retrieval
