# 07. Master Architectural Dependency Graph
**Status:** [VERIFIED]

```
[Browser Client: index.html]
       │
       ├──(HTTP)──────► [api/router.py]
       └──(WebSocket)─► [api/ws_manager.py]
                                │
                                ▼
                       [agents/graph.py] (StateGraph)
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  [security_gate.py]     [planner.py]           [executor.py]
         │                      │                      │
         ▼                      ▼                      ▼
  [audit_logger.py]      [model_provider.py]    [tools/__init__.py]
  (audit_trail.jsonl)    (Ollama 11434)         (16 Safe Tools)
                                                       │
                 ┌─────────────────────────────────────┼─────────────────────────────────────┐
                 ▼                                     ▼                                     ▼
        [tools/doc_tools.py]                 [tools/calc_tools.py]               [deliverables/*.py]
                 │                                     │                                     │
                 ▼                                     ▼                                     ▼
        [rag/vector_store.py]                 [Python AST Sandbox]                  [validator.py]
        (ChromaDB chroma_db/)                 (Zero eval / Zero RCE)                (OpenXML ZIP Check)
                 │                                                                           │
                 ▼                                                                           ▼
      [nomic-embed-text:latest]                                                    [generated_artifacts/]
```
