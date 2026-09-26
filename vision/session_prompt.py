def build_session_instruction(history):
    if not history:
        return (
            "This is the first frame in the current camera session. "
            "Analyze the outfit as a baseline."
        )

    return (
        "This frame belongs to an ongoing outfit comparison session. "
        "Use the following recent session context only to compare visible styling changes. "
        "Do not assume an item changed unless the current image supports it. "
        "Explain whether the current outfit improves or worsens proportions, color harmony, "
        "visual slimming, and age impression versus the recent baseline. "
        f"Recent context: {history}"
    )
