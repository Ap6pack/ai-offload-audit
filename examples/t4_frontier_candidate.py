def design_migration_strategy(ai_client, context):
    """Synthetic example: novel architecture/planning may justify frontier reasoning."""
    prompt = f"Design an architecture and migration strategy across ambiguous, conflicting constraints: {context}"
    return ai_client.responses.create(model="frontier-model", input=prompt)
