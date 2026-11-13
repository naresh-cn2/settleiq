@app.get("/{full_path:path}")
    def serve_spa(full_path: str) -> Response:
        # Explicitly exclude API and health paths from SPA fallback
        clean_path = full_path.lstrip("/")
        if (
            clean_path == ""  # Root path
            or clean_path == "v1"
            or clean_path.startswith("v1/")
            or clean_path == "health"
            or clean_path.startswith("health/")
        ):
            raise HTTPException(status_code=404, detail={"error": "not_found"})

        if clean_path.startswith("assets/"):
            raise HTTPException(status_code=404, detail={"error": "asset_not_found"})

        target_file = STATIC_DIR / clean_path
        if target_file.is_file():
            return FileResponse(str(target_file))

        index_file = STATIC_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file))

        raise HTTPException(status_code=404, detail={"error": "not_found"})