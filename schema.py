# Input
'''Raw Indian address (free-form text)'''

# Internal LLM output (Parser Agent)
{
  "house_number",
  "street",
  "landmark",
  "village",
  "taluk",
  "city",
  "district",
  "state",
  "pincode"
}


# Output JSON
{
  "normalized_address": "string",
  "latitude": "float",
  "longitude": "float",
  "confidence": "float (0–1)",
  "source": "cache | external",
  "decision": "accepted | retried | flagged"
}


'''Cache: Here Cache is a local SQLite database or any other database'''
'''External: Here External is an external API or any other service like OpenSourceAPI'''
