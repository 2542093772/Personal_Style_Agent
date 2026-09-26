# Vision analysis policy

The camera analysis layer should:

- Evaluate only visible styling characteristics.
- Avoid inferring sensitive personal attributes.
- Prefer concrete fit/proportion observations over generic praise.
- Ask for a better frame when the body or outfit is not sufficiently visible.
- Compare against the user's explicit personal profile and learned style rules.
- Never modify personal learned rules from a single camera frame.
- Treat each frame as transient unless the user explicitly saves the result.
