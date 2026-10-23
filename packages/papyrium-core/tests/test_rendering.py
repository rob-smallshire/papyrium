"""JobRendering: bytes through a model into outputs."""

from papyrium.core.rendering import JobRendering
from papyrium.core.testing import ByteDotModel, JsonOutput


def test_pages_reach_every_output_as_they_complete(tmp_path):
    first, second = JsonOutput(name="a", filename="a.json"), JsonOutput(name="b", filename="b.json")
    rendering = JobRendering(ByteDotModel(name="m"), [first, second], tmp_path)
    rendering.feed(b"AB\x0cC")
    assert rendering.page_count == 1
    assert len(first.documents[0]) == len(second.documents[0]) == 1
    filepaths = rendering.finish()
    assert rendering.page_count == 2
    assert sorted(path.name for path in filepaths) == ["a.json", "b.json"]


def test_finish_twice_writes_once(tmp_path):
    rendering = JobRendering(ByteDotModel(name="m"), [JsonOutput(name="j")], tmp_path)
    rendering.feed(b"A")
    assert len(rendering.finish()) == 1
    assert rendering.finish() == []
