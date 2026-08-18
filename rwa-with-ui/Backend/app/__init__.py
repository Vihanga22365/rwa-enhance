"""RWA Model Explainability backend.

Layout
------
app/agents/   the agents (classifier, orchestrator, per-table data agents,
              conclusion writer) plus the pipeline that wires them together
app/tools/    the LangChain tools those agents call
app/prompts/  every prompt string, one module per agent family
app/llm/      OpenAI model configuration and the ChatOpenAI factory
app/data/     Excel loaders: the mock source tables and the decision trees
app/api/      FastAPI routes, request/response schemas, session store
"""

__version__ = "2.0.0"
