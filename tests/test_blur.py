"""The published blur covers the whole person box, not the retired head strip."""

from PIL import Image
from whostop.data.blur import YUNET_SHA256, head_band_box, person_blur_box, yunet_blur_box
from whostop.data.publish import blur_boxes


def test_yunet_weights_pin_matches_opencv_zoo():
    assert YUNET_SHA256 == "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"


def test_whole_person_box_is_blurred_including_the_face_below_the_head_band():
    """ill2_037 geometry: person y 444–637, head band ends near y 486, face around y 560."""
    person = (400, 444, 560, 637)
    band = head_band_box(person)
    assert band[3] == 444 + 0.22 * (637 - 444)
    assert band[3] < 500
    image = Image.new("RGB", (960, 640), (240, 240, 240))
    for y in range(444, 637):
        for x in range(400, 560):
            image.putpixel((x, y), (180, 40, 40) if (x + y) % 2 == 0 else (20, 20, 200))
    missed = blur_boxes(image, [band])
    assert missed.getpixel((480, 560)) == image.getpixel((480, 560))
    covered = blur_boxes(image, [person_blur_box(person)])
    assert covered.getpixel((480, 560)) != image.getpixel((480, 560))
    # The strip above the face is inside the full box, and so is the chin.
    assert covered.getpixel((480, 450)) != image.getpixel((480, 450))
    assert covered.getpixel((480, 610)) != image.getpixel((480, 610))


def test_yunet_face_is_padded_thirty_percent_on_each_side():
    raw = (100, 500, 40, 80)
    padded = yunet_blur_box(raw)
    assert padded == (100 - 12, 500 - 24, 100 + 52, 500 + 104)
    image = Image.new("RGB", (300, 700), (10, 10, 10))
    # A pixel outside the raw face and inside the 30% pad must change.
    image.putpixel((90, 490), (255, 0, 0))
    image.putpixel((120, 540), (255, 0, 0))
    out = blur_boxes(image, [padded])
    assert out.getpixel((90, 490)) != (255, 0, 0)
    assert out.getpixel((120, 540)) != (255, 0, 0)
