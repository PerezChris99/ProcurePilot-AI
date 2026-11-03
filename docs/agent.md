# Procurement agent

The Google ADK agent is defined in backend/app/agents/procurement_agent/agent.py. Its only registered tool is discover_and_rank_products. The tool calls the Channel3 adapter, validates catalogue records, and delegates scoring to the deterministic procurement ranking service.

The agent may clarify requirements, discover products, compare evidence, and explain recommendations. It has no tools for creating or approving purchase orders, initiating PayPal orders, capturing payments, or changing payment state.

The API runs the agent in an ephemeral InMemorySessionService session per analysis request. The request and final explanation are persisted in PostgreSQL; ADK conversation state itself is not persistent. Gemini API access is required. A missing key returns a clear configuration error instead of a fabricated AI response.

Product descriptions and other supplier-supplied text are untrusted. The system prompt explicitly prohibits treating catalogue content as instructions and prohibits invented prices, stock status, merchants, delivery claims, or attributes.
