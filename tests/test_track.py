import pytest
from spotifydownloader.routers.track import extract_track_id


@pytest.mark.parametrize("input_url,expected", [
    ("https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT", "4cOdK2wGLETKBW3PvgPWqT"),
    ("spotify:track:4cOdK2wGLETKBW3PvgPWqT", "4cOdK2wGLETKBW3PvgPWqT"),
    ("4cOdK2wGLETKBW3PvgPWqT", "4cOdK2wGLETKBW3PvgPWqT"),
    ("https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT?si=123", "4cOdK2wGLETKBW3PvgPWqT"),
    ("", None),
    ("https://open.spotify.com/album/4cOdK2wGLETKBW3PvgPWqT", None),
    ("link_invalido", None),
])
def test_extract_track_id(input_url, expected):
    assert extract_track_id(input_url) == expected