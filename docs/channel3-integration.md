# Channel3 integration

The product discovery adapter uses the documented Channel3 Product API search endpoint: POST https://api.trychannel3.com/v1/search. Authentication is sent in the x-api-key header. The request contains a natural-language query and optional filters/limit. The adapter supports an optional x-user-id attribution header when a stable authenticated application user ID is available.

The response is validated against the Channel3 product/offer schema. Product identity and descriptive fields belong to the product record; price, currency, availability, and retailer buy links belong to individual offers. Do not infer a product-level price where offers are missing.

Channel3 checkout is not assumed to be available. The current developer overview labels its checkout API as coming soon. PayPal Sandbox is a separate payment demonstration and must not be represented as a payment to the Channel3 retailer.

References: https://channel3.ai/docs/guides/make-a-search and https://channel3.ai/docs/guides/response-overview
