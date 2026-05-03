from workflow.preview_pipeline.providers import build_nano_banana_arguments
from workflow.preview_pipeline.validators import (
    validate_desktop_prompt_contract,
    validate_nano_banana_arguments_contract,
    validate_visual_context_contract,
)


def test_nano_banana_arguments_use_required_schema():
    args = build_nano_banana_arguments("desktop prompt", aspect_ratio="16:9")

    assert args == {
        "prompt": "desktop prompt",
        "aspect_ratio": "16:9",
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "6",
        "limit_generations": True,
    }

    forbidden = {"guidance_scale", "num_inference_steps", "image_size", "width", "height"}
    assert forbidden.isdisjoint(args)
    assert validate_nano_banana_arguments_contract(args) == []


def test_nano_banana_argument_contract_rejects_flux_controls():
    errors = validate_nano_banana_arguments_contract({
        "prompt": "desktop",
        "aspect_ratio": "16:9",
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "6",
        "limit_generations": True,
        "guidance_scale": 3.5,
    })
    assert "forbidden nano-banana argument: guidance_scale" in errors


def test_prompt_contract_rejects_wallpaper_only_prompt():
    errors = validate_desktop_prompt_contract("cinematic landscape, no UI chrome")
    assert any("entire desktop UI" in e or "forbidden" in e for e in errors)


def test_prompt_contract_accepts_full_desktop_prompt():
    prompt = "full Linux desktop theme concept preview, entire desktop UI, screenshot-style mockup, themed terminal window, launcher/menu panel, widget menus, edge-to-edge, no cinematic letterbox bars"
    assert validate_desktop_prompt_contract(prompt) == []


def test_visual_context_contract_requires_reference_and_elements():
    errors = validate_visual_context_contract({"style_description": "dark"})
    assert "missing reference_image_url" in errors
    assert "missing visual_element_plan" in errors


def test_visual_context_contract_accepts_minimal_valid_context():
    ctx = {
        "reference_image_url": "https://example.com/image.png",
        "extracted_palette": {"background": "#000000", "foreground": "#ffffff"},
        "style_description": "dark RPG menu",
        "ui_recommendations": "thin borders, terminal, launcher",
        "visual_element_plan": [{"id": "terminal", "implementation_tool": "terminal:kitty"}],
        "validation_checklist": ["terminal visible"],
    }
    assert validate_visual_context_contract(ctx) == []
