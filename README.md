# Towards Automated Ontology Generation from Unstructured Text: A Multi-Agent LLM Approach

This repository contains the code and experimental framework for automating the generation of formal Web Ontology Language (OWL) ontologies from unstructured natural language text, specifically focusing on complex domains like life insurance contracts.

Automatically converting dense legal documents into queryable, formal ontologies is a significant challenge. This experiment comparisons the advantages and disadvantages of generating ontologies from LLMs through a single pass direct generation approach against a multi-agent approach.

---

## System Architecture

The pipeline decomposes ontology construction into specialized, artifact-driven roles orchestrated via LangGraph:

1. **Competency Question (CQ) Generator**
   Extracts fine-grained, ODP-driven questions from the source text to serve as functional requirements.

2. **Domain Expert Agent**
   Normalizes domain signals and extracts a precise Semantic Requirements Document (SRD).

3. **Manager Agent**
   Translates the SRD into a build-ready Technical Implementation Plan (TIP), mapping concepts to explicit Ontology Design Patterns (ODPs).

4. **Coder Agent**
   Implements the TIP by incrementally editing a Turtle (`.ttl`) file using file-system tools.

5. **Quality Assurance (QA) Agent & Bug Fixer**
   A three-gate sequence (architectural review, RDF syntax check, OWL consistency check) that enforces quality and loops back to a QA-Coder for precise syntax corrections.

---

## Repository Structure

Based on the provided architecture, the codebase is organized as follows:

* `agents/`: Contains the core LangGraph agents and execution scripts.

  * `cq_generator.py`: Generates structured CQs from input PDFs.
  * `ontology_generator.py`: The direct/baseline single-agent generation script.
  * `multi_agent.py`: The proposed multi-agent generation pipeline.
  * `ontology_fixer.py`: Standalone script to verify and fix syntax/semantics of existing `.ttl` files.
  * `eval.py`: Automated SPARQL-based evaluation framework.
  * `vector_eval.py`: Vector-based Retrieval-Augmented Generation (RAG) evaluation framework.

* `contracts/`: Directory for input unstructured text documents (e.g., PDF contracts).

* `cqs/generated/`: Output directory for the generated JSON Competency Questions.

* `helper/`: Utility scripts (e.g., LLM connections, tool call counting).

* `models/`: Pydantic schemas shared across the agents (e.g. `competency_questions.py` defines the `CompetencyQuestion`/`CQList` structured-output schema used by `cq_generator.py`).

* `ontology/`: Output directory for the generated Turtle (`.ttl`) files.

* `rag_eval/`: Core logic for the semantic retrieval and evaluation nodes.

* `tools/`: LLM-accessible tools for file management (`file_management.py`) and syntax validation (`syntax_checks.py`).

---

## Setup and Prerequisites

1. **Create the conda environment**
   Requires [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda. This creates an environment named `ontology-gen` with Python 3.12 and every dependency the code imports (LangChain/LangGraph, rdflib, owlready2, pymupdf, sentence-transformers, dspy, etc.):

   ```bash
   conda env create -f environment.yml
   conda activate ontology-gen
   ```

   Prefer plain `pip`/`venv` instead? `requirements.txt` has the same pinned versions:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install and start Ollama (local LLM server)**
   The agents connect to a local [Ollama](https://ollama.com/download) server through its OpenAI-compatible API rather than vLLM -- Ollama installs in one step and uses Apple Silicon (Metal) or NVIDIA (CUDA) acceleration automatically, so it works out of the box on a Mac.

   ```bash
   # Install Ollama, then pull a model (pick a size that fits your machine):
   ollama pull qwen2.5:32b-instruct     # ~20GB, needs a beefy machine
   # ollama pull qwen2.5:14b-instruct   # smaller/faster alternative
   ```

   Ollama serves its OpenAI-compatible API at `http://localhost:11434/v1` automatically once installed (start it manually with `ollama serve` if it isn't already running). All LLM connections in this repo go through `helper/connections.py`'s `get_llm()`, so this is the only place the endpoint/model is configured.

3. **Environment Variables**
   Copy `.env.example` to `.env` and set the model tag to match what you pulled:

   ```bash
   cp .env.example .env
   ```

   ```bash
   OLLAMA_MODEL="qwen2.5:32b-instruct"
   ```

---

## Running the Experiments

Follow these steps to execute the pipeline from raw text to evaluated ontology.

### 1. Generate Competency Questions

Extract CQs from the PDF contracts located in the `contracts/` directory.

```bash
python agents/cq_generator.py
```

**Output:** JSON files containing CQs will be saved to `cqs/generated/`.

---

### 2. Generate the Ontology

You can test either the baseline approach or the multi-agent approach.

#### Option A: Multi-Agent Pipeline (Proposed Method)

```bash
python agents/multi_agent.py \
  --contract contracts/sen.pdf \
  --cqs cqs/generated/sen.json \
  --ontology-out ontology/multi_sen.ttl
```

#### Option B: Single-Agent Baseline

> **Note:** Update the `SPECIFIC_CONTRACT_PATH` inside the script before running.

```bash
python agents/ontology_generator.py
```

---

### 3. Evaluate the Ontology

The framework utilizes two distinct methods to score the generated ontologies.

#### SPARQL-Based Functional Evaluation

```bash
python agents/eval.py cqs/generated/sen.json ontology/multi_sen.ttl
```

**Output:** A detailed JSON report is saved to `agents/eval_results/`.

---

#### Vector-Based RAG Evaluation

```bash
python agents/vector_eval.py \
  --ontology-file ontology/multi_sen.ttl \
  --cq-file cqs/generated/sen.json \
  --output-file agents/eval_results/rag_sen.json
```
