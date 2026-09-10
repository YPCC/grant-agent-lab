from src.harness.cases import list_cases, load_case
from src.harness.review import review_text
from src.harness.runner import run_case


def test_list_cases():
    ids = {c["id"] for c in list_cases()}
    assert "weak_aims_vague" in ids
    assert "complete_ora_packet" in ids


def test_weak_aims_graded():
    result = run_case(load_case("weak_aims_vague"))
    assert result["grade"]["passed"], result["grade"]
    assert result["review"]["fatal_or_major"] >= 1
    assert result["checklist"]["can_freeze"] is False
    assert result["package"] is None


def test_good_aims_cleaner_than_weak():
    good = review_text(load_case("good_aims_auditory")["_text"])
    weak = review_text(load_case("weak_aims_vague")["_text"])
    assert good["fatal_or_major"] < weak["fatal_or_major"]
    assert good["gpa_score"] > weak["gpa_score"]


def test_incomplete_package_blocks_office():
    result = run_case(load_case("incomplete_package"), allow_package=True)
    assert result["grade"]["passed"], result["grade"]
    assert result["package"] is None


def test_complete_ora_packet_not_nih():
    result = run_case(load_case("complete_ora_packet"))
    assert result["grade"]["passed"], result["grade"]
    assert result["package"]["tracking_number"].startswith("ORA-")
    assert result["package"]["destination"] == "Office of Research Aid database"
    assert result["package"]["not"] == "NIH_ASSIST"


def test_nih_assist_blocked():
    import pytest

    from src.harness.packaging import create_office_package

    with pytest.raises(PermissionError):
        create_office_package(
            intake={"can_submit_to_office": True},
            destination="NIH_ASSIST",
        )
