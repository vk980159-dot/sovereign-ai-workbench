# 06. Top Technical Questions & Answers for Judges
**Status:** [VERIFIED]

*(Core technical defenses for SIH judges)*
- **Q: How do you guarantee zero data leakage?**  
  *A: The system binds to localhost sockets (127.0.0.1:8000, 11434). Tests prove zero egress packets. Disconnecting the network cable leaves all models and tools 100% operational.*
- **Q: How do you prevent LLM math hallucination?**  
  *A: The LLM is forbidden from computing math. Math queries are dispatched to an AST parser that evaluates expressions deterministically.*
- **Q: Are deliverables authentic files?**  
  *A: Yes. `python-docx`, `openpyxl`, and `python-pptx` build binary Office OpenXML archives verified by `DeliverableValidator` for magic bytes and XML schemas.*
