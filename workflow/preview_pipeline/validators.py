from __future__ import annotations

REQUIRED_PROMPT_PHRASES = [
    "full linux desktop theme concept preview",
    "entire desktop ui",
    "screenshot-style mockup",
    "themed terminal window",
    "launcher/menu panel",
    "widget menus",
    "edge-to-edge",
    "no cinematic letterbox bars",
]

FORBIDDEN_PROMPT_PHRASES = [
    "no ui chrome",
    "landscape-only",
    "environment only",
    "mood painting only",
]

REQUIRED_VISUAL_CONTEXT_KEYS = [
    "reference_image_url",
    "extracted_palette",
    "style_description",
    "visual_element_plan",
    "validation_checklist",
]


def validate_desktop_prompt_contract(prompt: str) -> list[str]:
    text = (prompt or "").lower()
    errors: list[str] = []
    for phrase in REQUIRED_PROMPT_PHRASES:
        if phrase not in text:
            errors.append(f"missing required prompt phrase: {phrase}")
    for phrase in FORBIDDEN_PROMPT_PHRASES:
        if phrase in text:
            errors.append(f"forbidden prompt phrase present: {phrase}")
    return errors


def validate_visual_context_contract(visual_context: dict) -> list[str]:
    ctx = visual_context if isinstance(visual_context, dict) else {}
    errors: list[str] = []
    for key in REQUIRED_VISUAL_CONTEXT_KEYS:
        if key not in ctx:
            errors.append(f"missing {key}")
    if "visual_element_plan" in ctx and not isinstance(ctx.get("visual_element_plan"), list):
        errors.append("visual_element_plan must be a list")
    if "validation_checklist" in ctx and not isinstance(ctx.get("validation_checklist"), list):
        errors.append("validation_checklist must be a list")
    return errors


def validate_nano_banana_arguments_contract(arguments: dict) -> list[str]:
    args = arguments if isinstance(arguments, dict) else {}
    errors: list[str] = []
    required = {
        "prompt": str,
        "aspect_ratio": str,
        "num_images": int,
        "output_format": str,
        "safety_tolerance": str,
        "limit_generations": bool,
    }
    for key, expected_type in required.items():
        if key not in args:
            errors.append(f"missing {key}")
        elif not isinstance(args[key], expected_type):
            errors.append(f"{key} must be {expected_type.__name__}")
    forbidden = {"guidance_scale", "num_inference_steps", "image_size", "width", "height"}
    for key in sorted(forbidden.intersection(args)):
        errors.append(f"forbidden nano-banana argument: {key}")
    return errors
