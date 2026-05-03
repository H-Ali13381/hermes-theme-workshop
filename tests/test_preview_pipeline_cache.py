from workflow.preview_pipeline.cache import (
    append_preview_history,
    clear_pending_preview,
    load_pending_preview,
    load_preview_history,
    save_pending_preview,
)


def test_pending_preview_round_trip(tmp_path):
    html_path = tmp_path / "visualize.html"
    html_path.write_text("<html></html>")
    visual_context = {"reference_image_url": "https://example.com/hero.png", "extracted_palette": {}}

    save_pending_preview(str(tmp_path), "https://example.com/hero.png", html_path, visual_context)
    loaded = load_pending_preview(str(tmp_path))

    assert loaded["image_url"] == "https://example.com/hero.png"
    assert loaded["html_path"] == str(html_path)
    assert loaded["visual_context"] == visual_context


def test_pending_preview_malformed_json_returns_empty(tmp_path):
    (tmp_path / "visualize.pending.json").write_text("not json")
    assert load_pending_preview(str(tmp_path)) == {}


def test_clear_pending_preview_removes_file(tmp_path):
    save_pending_preview(str(tmp_path), "url", tmp_path / "visualize.html", {})
    clear_pending_preview(str(tmp_path))
    assert load_pending_preview(str(tmp_path)) == {}


def test_preview_history_appends_jsonl(tmp_path):
    append_preview_history(str(tmp_path), {"status": "success", "image_url": "url-1"})
    append_preview_history(str(tmp_path), {"status": "error", "error": "boom"})

    history = load_preview_history(str(tmp_path))
    assert history == [
        {"status": "success", "image_url": "url-1"},
        {"status": "error", "error": "boom"},
    ]
