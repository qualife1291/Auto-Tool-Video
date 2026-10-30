import pytest
from PIL import Image

from auto_tool_video.render import ScenePainter, caption_pages, emphasis_spans, font, wrap


def test_vietnamese_words_are_not_split_in_normal_captions():
    text = "Nước trên áo dần đi vào không khí."
    face = font(48)
    lines = wrap(text, face, 400)
    assert " ".join(lines) == text
    assert all(face.getlength(line) <= 400 for line in lines)
    assert all(word in text.split() for line in lines for word in line.split())


def test_unbroken_input_is_bounded_without_losing_characters():
    text = "https://" + "á" * 100
    face = font(48)
    lines = wrap(text, face, 180)
    assert "".join(lines) == text
    assert all(face.getlength(line) <= 180 for line in lines)


def test_two_line_caption_avoids_a_single_orphan_question_word():
    text = "Áo ướt khô rồi. Nước đã đi đâu nhỉ?"
    page = caption_pages(text, font(48), 770)[0]
    lines = page.splitlines()
    assert " ".join(lines) == text
    assert len(lines) == 2 and len(lines[-1].split()) >= 3


@pytest.mark.parametrize("bold", [False, True])
@pytest.mark.parametrize(
    "text",
    [
        "Nước lỏng chuyển thành hơi nước. Quá trình này gọi là bay hơi.",
        "Hơi nước thường vô hình. Những chấm xanh chỉ là hình minh họa.",
        "Nước không biến mất: nó chuyển vào không khí. Bạn thử quan sát chiếc khăn ướt nhé!",
    ],
)
def test_long_narration_has_balanced_pages_without_an_orphan_last_word(text, bold):
    for width in (770, 1400):
        face = font(48, bold)
        pages = caption_pages(text, face, width)
        assert " ".join(page.replace("\n", " ") for page in pages) == text
        assert all(len(page.split()) >= 3 for page in pages)
        assert all(len(page.splitlines()) <= 2 for page in pages)
        assert all(face.getlength(line) <= width for page in pages for line in page.splitlines())


def test_review_sentences_fit_a_single_two_line_caption_page():
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    spec = spec_from_file_location(
        "review_video", Path(__file__).resolve().parents[2] / "scripts/create_review_video.py"
    )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    for _, text, _ in module.SPEECH:
        for bold in (False, True):
            pages = caption_pages(text, font(48, bold), 770)
            assert len(pages) == 1, text
            assert len(pages[0].splitlines()) <= 2


@pytest.mark.parametrize(
    "lines,phrase,expected",
    [
        (["Nước Bay", "Hơi rồi."], "bay hơi", [(5, 8), (0, 3)]),
        (["Nước .* <img>"], ".* <img>", [(5, 13)]),
        (["Nước bay hơi."], ".*", [None]),
        (["Nước bay hơi."], "", [None]),
        (["Nước bay hơi."], "khói", [None]),
    ],
)
def test_emphasis_is_literal_preserves_unicode_and_crosses_line_breaks(lines, phrase, expected):
    assert emphasis_spans(lines, phrase) == expected


@pytest.mark.parametrize("size", [(1080, 1920), (1920, 1080), (360, 640), (640, 360)])
@pytest.mark.parametrize("style", ["card", "contrast", "accent"])
def test_caption_styles_stay_in_safe_box_and_highlight_in_both_aspects(tmp_path, size, style):
    path = tmp_path / "image.png"
    Image.new("RGB", (800, 700), "#FFF8EB").save(path)
    scene = {
        "title": "Bay hơi",
        "narration": "Nước bay hơi.",
        "duration": 4,
        "style": "motion",
        "caption_style": style,
        "caption_emphasis": "bay hơi",
    }
    painter = ScenePainter(path, scene, *size, True)
    try:
        frame = painter.base.copy()
        painter.draw_caption(frame, 0.5)
        import numpy as np

        pixels = np.asarray(frame)
        changed = np.any(pixels != np.asarray(painter.base), axis=2)
        ys, xs = np.where(changed)
        x, y, w, h = [round(v * painter.scale) for v in painter.caption_box]
        assert xs.min() >= x and xs.max() <= x + w + max(1, round(5 * painter.scale))
        assert ys.min() >= y and ys.max() <= y + h + max(1, round(5 * painter.scale))
        if style == "contrast":
            assert tuple(pixels[y + h // 2, x + 5]) == (23, 61, 51)
        if style == "accent":
            # Yellow must appear around the actual phrase, away from the left accent bar.
            text_region = pixels[y : y + h, x + round(30 * painter.scale) : x + w]
            assert ((text_region == (244, 190, 83)).all(axis=2)).sum() > 10
    finally:
        painter.close()
