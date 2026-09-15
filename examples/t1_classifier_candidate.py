def classify_support_request(ai_client, text):
    """Synthetic example: narrow four-label intent classification."""
    prompt = f"Classify this request as billing, technical, sales, or other: {text}"
    return ai_client.responses.create(model="frontier-model", input=prompt)
