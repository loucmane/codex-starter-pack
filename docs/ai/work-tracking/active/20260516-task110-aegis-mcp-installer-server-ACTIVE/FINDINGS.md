# Findings

- 2026-05-16 — Task 110 kickoff plan contained generic wizard-flow language from the scaffold template. Corrected the plan to the Aegis MCP server scope before implementation so future sessions do not follow the wrong handler target.
- 2026-05-16 — FastMCP/Pydantic renders `Literal["generic"]` as a JSON Schema `const`, not an `enum`, and `json_response=True` returns both text content and structured payload from `call_tool`. The tests now assert these actual protocol shapes.
