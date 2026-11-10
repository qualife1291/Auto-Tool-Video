"""Scene-grounded composition cues for local ComfyUI image candidates.

Model instructions are not evidence that an image meets these standards.
Keep the original authored image prompt verbatim at the front.
"""

from __future__ import annotations

from typing import Any

NEGATIVE = (
    "text, watermark, logo, unreadable labels, clutter, inconsistent character, "
    "generic isolated icon, flat vector clip art, low-detail pictogram, "
    "mostly blank background, plain empty border, cropped subject, "
    "blurry outlines, low-detail textures, duplicate main objects, random color shifts"
)


def build_image_prompt(project: dict[str, Any], scene: dict[str, Any]) -> tuple[str, str]:
    """Target this scene, not one repeated icon for an entire video.

    Use only an authored middle beat for a representative still; generated
    placeholder beats are not approved visual instructions. A human must still
    inspect the actual image before applying it to a video.
    """
    aspect = project["aspect"]
    if aspect == "portrait":
        framing = (
            "Portrait 9:16: full-bleed illustrated environment from top to bottom, "
            "large focal subject clearly visible on a phone, including its whole silhouette; "
            "extend believable ground, furniture or scenery behind the lower caption safe area. "
            "Leave readable contrast for a separately typeset caption, not an empty lower fifth."
        )
    elif aspect == "landscape":
        framing = (
            "Landscape 16:9: full-bleed wide environment with a large clear focal subject, "
            "supporting foreground and background, balanced horizontal framing and "
            "clear caption safe area without clipping the main object."
        )
    else:
        raise ValueError("Unsupported image aspect")

    brief = project.get("brief") or {}
    pieces = [scene["image_prompt"]]
    if (description := scene.get("visual_description", "")).strip():
        pieces.append("Concrete depicted event: " + description)
    if (narration := scene.get("narration", "")).strip():
        pieces.append("This scene must visually explain the narration: " + narration)

    beats = scene.get("second_by_second") or []
    if scene.get("beat_plan_status") == "authored" and beats:
        beat = beats[len(beats) // 2]
        if isinstance(beat, dict):
            state = beat.get("visual_state", "")
            action = beat.get("action", "")
            if isinstance(state, str) and state.strip():
                pieces.append("Representative visible state: " + state)
            if isinstance(action, str) and action.strip():
                pieces.append("Visible action to depict: " + action)
            camera = beat.get("camera", "")
            continuity = beat.get("continuity", "")
            if isinstance(camera, str) and camera.strip():
                pieces.append("Representative shot framing: " + camera)
            if isinstance(continuity, str) and continuity.strip():
                pieces.append("Continuity anchors: " + continuity)
            pieces.append(
                "depict only the representative moment, not several contradictory "
                "wet/dry stages at the same time; later stages belong in animation."
            )

    pieces.extend(
        [
            framing,
            (
                "Establish a coherent color palette consistent with the story and "
                "subject materials; keep lighting direction, object proportions and "
                "character identity stable between neighboring scenes. "
                "Detailed scene-specific objects and correct physical relationships; "
                "visible material grain, fabric weave or surface texture as appropriate, "
                "precise edges, natural lighting and cast shadows, foreground/midground/"
                "background depth. No repeated generic icon across different actions. "
                "No text, letters, logo or watermark inside the picture."
            ),
        ]
    )
    for key in ("style_bible", "character_bible"):
        if (value := brief.get(key, "")).strip():
            pieces.append(value)
    return "\n".join(pieces), NEGATIVE
