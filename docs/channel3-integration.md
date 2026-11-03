# Channel3 integration

The product discovery adapter uses the documented Channel3 Product API search endpoint: POST https://api.trychannel3.com/v1/search. Authentication is sent in the x-api-key header. Requests include a natural-language query, a result limit, optional filters, and an optional page_token. Send a stable authenticated application user ID in x-user-id so Channel3 can attribute offer-link clicks.

The response contains canonical products and retailer offers. A product has its own ID, title, description, brands, images, key features, and structured_attributes. Retailer-specific price and buy URL data live on each offer. Channel3 represents price as an object with amount and currency; the backend validates this nested structure and compares only offers in the requested currency. Availability is InStock or OutOfStock. Search responses may include next_page_token; subsequent requests must repeat the same query and filters and pass that token as page_token.

Channel3 product discovery is not the same as payment settlement. ProcurePilot's PayPal Sandbox workflow is a separate hackathon payment demonstration; it must not be represented as payment to a Channel3 retailer. Confirm current checkout capabilities directly with Channel3 before planning a live retailer checkout flow.

References: https://channel3.ai/docs/guides/make-a-search, https://channel3.ai/docs/guides/response-overview, and https://channel3.ai/docs/sdk/pagination
