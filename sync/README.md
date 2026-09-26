# GitHub profile sync

The camera collector writes every sample locally to `personal/visual_profile.json`.

GitHub sync is intentionally debounced so the repository does not receive one commit per camera sample.

Default behavior:
- local save: every successful sample
- GitHub sync check: after samples
- actual push: at most once every 300 seconds when the profile changed
- synced data: structured profile JSON only
- raw camera frames: never synced

Environment variables:

```text
PROFILE_GITHUB_SYNC=true
PROFILE_GITHUB_SYNC_INTERVAL=300
```

The local machine must already be able to run `git push origin HEAD:main` without an interactive login prompt.
