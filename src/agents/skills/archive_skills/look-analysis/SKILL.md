---
name: look-analysis
description: Answers queries involving individual looks. Use this when asked for a look breakdown, look visual analysis, or general look questions.
allowed-tools: get_look_analysis
---
# Look Analysis

This skill is for handling any queries that involve individual looks. Pass the query to the get_look_analysis tool, which consists of a three agent workflow:

1. Pass the query into the first agent, which uses the retrieve and get_look_composition tools to retrieve relevant metadata. Its output includes an "Image URLs:" section with the exact CloudFront URLs for the look.
2. Pass the retrieved results (including the Image URLs) and the query to the second agent, which uses get_image_details to perform visual analysis using those exact URLs.
3. Finally, pass the visual and knowledge base information to the final agent to synthesize a final answer.

## Guidelines
Pass the full query to the tool so all relevant context is available across all three steps.
For visual detail questions (closures, hems, construction, jewelry placement), visual analysis takes priority over metadata. If the visual result is inconclusive or images were unavailable, the final answer should state that explicitly rather than filling in from metadata.