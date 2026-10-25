import pytest

from app.services.evaluation_service import list_datasets, load_dataset


@pytest.mark.parametrize("name", list_datasets())
def test_dataset_is_valid(name):
    cases = load_dataset(name)
    assert cases, f"{name} is empty"
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids)), f"{name} has duplicate ids"
    for c in cases:
        # Every case must be checkable by at least one evaluator.
        assert c.expected_output or c.expected_tools is not None or c.rubric, c.id


def test_tool_agent_dataset_is_listed():
    assert "tool_agent_eval.jsonl" in list_datasets()
