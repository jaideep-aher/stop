from whostop.parse import parse_action, parse_completion, strip_echo


def test_leading_words():
    assert parse_action("STOP") == "STOP"
    assert parse_action("  caution, because the lane is busy") == "CAUTION"
    assert parse_action("PROCEED") == "PROCEED"
    assert parse_action("GO") == "PROCEED"
    assert parse_action("PROCEED WITH CAUTION then explain") == "CAUTION"


def test_not_the_leading_word_is_unparsed():
    assert parse_action("The car should STOP") == "UNPARSED"
    assert parse_action("maybe brake") == "UNPARSED"
    assert parse_action("") == "UNPARSED"
    assert parse_action("STOPPING") == "UNPARSED"


def test_markdown_and_punctuation():
    assert parse_action("**STOP**") == "STOP"
    assert parse_action("STOP.") == "STOP"


def test_strip_echo_then_parse():
    prompt = "Answer STOP, PROCEED, or CAUTION."
    raw = prompt + "\nassistant: PROCEED"
    assert strip_echo(raw, prompt) == "PROCEED"
    assert parse_completion(raw, prompt) == "PROCEED"
