def normalize_network_indicator(ai_client, value):
    """Synthetic anti-pattern: validation/normalization should be challenged as T0."""
    prompt = f"Validate this IP/CIDR, normalize it, and return strict JSON: {value}"
    return ai_client.responses.create(model="frontier-model", input=prompt)
