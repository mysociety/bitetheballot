def clean_decision(decision, decisions):
    # Some of the decisions are (annoyingly) a different structure
    # to the rest
    if isinstance(decision, basestring):
        decision = decisions[decision]
    # Some decisions are null objects so skip those
    if decision is not None:
        return decision
