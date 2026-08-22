from datetime import datetime
from unittest.mock import patch

import pytest
from click import UsageError
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as StreamChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta

from sgpt.handlers.handler import (
    _apply_api_extra_body,
    _parse_api_extra_body,
    filter_thinking_tokens,
)

from .utils import app, cmd_args, runner

# ---------------------------------------------------------------------------
# filter_thinking_tokens — pure function over a string iterable.
# ---------------------------------------------------------------------------


def test_filter_tag_split_across_chunks():
    # "<th" + "ink>" closes the opening tag across chunks, "foo" is inside,
    # "</think>" closes, "bar" is outside. So only "bar" should pass through.
    assert "".join(filter_thinking_tokens(["<th", "ink>foo</think>bar"])) == "bar"


def test_filter_two_blocks_in_one_chunk():
    assert (
        "".join(filter_thinking_tokens(["<think>aaa</think><think>bbb</think>foo"]))
        == "foo"
    )


def test_filter_alt_long_tag():
    assert (
        "".join(filter_thinking_tokens(["<thinking>hidden</thinking>visible"]))
        == "visible"
    )


def test_filter_unclosed_block_discarded():
    assert "".join(filter_thinking_tokens(["<think>foo<think>bar"])) == ""


def test_filter_no_tags_byte_identical():
    stream = ["hello ", "world"]
    assert "".join(filter_thinking_tokens(stream)) == "hello world"


def test_filter_lone_angle_bracket_flushed():
    # `<b` is not a prefix of any tag -> flush "<b" verbatim.
    assert "".join(filter_thinking_tokens(["a<", "b"])) == "a<b"


def test_filter_think_with_close_in_next_chunk():
    assert "".join(filter_thinking_tokens(["<think>aaa</think>", "ok"])) == "ok"


# ---------------------------------------------------------------------------
# _parse_api_extra_body — guards around the raw config string.
# ---------------------------------------------------------------------------


def test_parse_empty_returns_none():
    assert _parse_api_extra_body("") is None


def test_parse_valid_object():
    assert _parse_api_extra_body('{"thinking": {"type": "disabled"}}') == {
        "thinking": {"type": "disabled"}
    }


def test_parse_invalid_json_raises_usage_error():
    with pytest.raises(UsageError) as exc:
        _parse_api_extra_body("{not json")
    assert "API_EXTRA_BODY" in str(exc.value)


def test_parse_non_object_raises_usage_error():
    with pytest.raises(UsageError) as exc:
        _parse_api_extra_body("[1, 2, 3]")
    assert "API_EXTRA_BODY" in str(exc.value)


def test_parse_string_raises_usage_error():
    with pytest.raises(UsageError) as exc:
        _parse_api_extra_body('"hello"')
    assert "API_EXTRA_BODY" in str(exc.value)


# ---------------------------------------------------------------------------
# _apply_api_extra_body — merge rules per backend.
# ---------------------------------------------------------------------------


def test_apply_openai_empty_leaves_kwargs_untouched():
    kwargs: dict = {"timeout": 60}
    _apply_api_extra_body(kwargs, None, False)
    assert kwargs == {"timeout": 60}
    assert "extra_body" not in kwargs


def test_apply_openai_sets_extra_body_key():
    kwargs: dict = {}
    _apply_api_extra_body(kwargs, {"thinking": {"type": "disabled"}}, False)
    assert kwargs == {"extra_body": {"thinking": {"type": "disabled"}}}


def test_apply_litellm_merges_as_kwargs():
    kwargs: dict = {"timeout": 60}
    _apply_api_extra_body(kwargs, {"thinking": {"type": "disabled"}}, True)
    assert kwargs == {"timeout": 60, "thinking": {"type": "disabled"}}


def test_apply_litellm_empty_is_noop():
    kwargs: dict = {"timeout": 60}
    _apply_api_extra_body(kwargs, None, True)
    assert kwargs == {"timeout": 60}


# ---------------------------------------------------------------------------
# End-to-end — streamed deltas pass through the filter.
# ---------------------------------------------------------------------------


def _delta_chunk(content):
    return ChatCompletionChunk(
        id="x",
        model="test-model",
        object="chat.completion.chunk",
        choices=[
            StreamChoice(
                index=0,
                finish_reason=None,
                delta=ChoiceDelta(content=content, role="assistant"),
            )
        ],
        created=int(datetime.now().timestamp()),
    )


def _litellm_stream(content, reasoning):
    """litellm-style object with a dict delta carrying reasoning_content."""
    from types import SimpleNamespace

    delta = {
        "role": "assistant",
        "content": content,
        "reasoning_content": reasoning,
    }
    choice = SimpleNamespace(delta=delta, finish_reason=None, index=0)
    return [SimpleNamespace(choices=[choice])]


@patch("sgpt.handlers.handler.completion")
def test_streaming_filters_think_blocks_openai(completion):
    completion.return_value = [_delta_chunk("<think>hidden</think>public")]
    result = runner.invoke(app, cmd_args(prompt="hi"))
    assert result.exit_code == 0
    assert "public" in result.output
    assert "hidden" not in result.output


@patch("sgpt.handlers.handler.completion")
def test_streaming_filters_split_think_tags(completion):
    completion.return_value = [
        _delta_chunk("<think>secret "),
        _delta_chunk("more</think>answer"),
    ]
    result = runner.invoke(app, cmd_args(prompt="hi"))
    assert result.exit_code == 0
    assert "answer" in result.output
    assert "secret" not in result.output
    assert "more" not in result.output


@patch("sgpt.handlers.handler.use_litellm", True)
@patch("sgpt.handlers.handler.completion")
def test_litellm_reasoning_content_not_yielded(completion):
    completion.return_value = _litellm_stream(
        content="answer", reasoning="thinking out loud"
    )
    result = runner.invoke(app, cmd_args(prompt="hi"))
    assert result.exit_code == 0
    assert "answer" in result.output
    assert "thinking out loud" not in result.output
