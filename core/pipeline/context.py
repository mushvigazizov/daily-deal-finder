def make_pipeline_context(mode="manual"):
    return {
        "mode": mode,
        "products": [],
        "changed_files": [],
        "artifacts": {},
        "errors": [],
    }
