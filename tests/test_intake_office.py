from src.shared.intake import apply_overrides, fill_intake
from src.shared.packaging import create_office_package


SAMPLE = (
    "Mechanism: R01 FOA PA-25-301. Principal investigator Jane Doe. "
    "The central hypothesis is that X causes Y. Specific Aim 1. "
    "Budget justification: 2.4 person-months. Data management and sharing plan attached. "
    "No vertebrate animals. Human subjects not applicable. Modular budget."
)


def test_intake_agent_fills_and_blocks_on_human_only():
    form = fill_intake(SAMPLE, "Doe_R01_Aims.docx")
    ids = {i["id"]: i for i in form["items"]}
    assert ids["BUDGET_ELEMENT"]["value"] == "yes"
    assert ids["BUDGET_ELEMENT"]["source"] == "agent"
    assert ids["PI_CERTIFY"]["value"] == "unknown"
    assert ids["PI_CERTIFY"]["complete"] is False
    assert form["can_submit_to_office"] is False


def test_human_override_unlocks_office_submit():
    form = fill_intake(SAMPLE, "Doe_R01_Aims.docx")
    overrides = {r["id"]: "yes" for r in form["items"] if not r["complete"]}
    # remaining unknown formatting/institutional
    for r in form["items"]:
        if r["value"] == "unknown":
            overrides[r["id"]] = "yes"
    form2 = apply_overrides(form, overrides)
    assert form2["can_submit_to_office"] is True
    assert form2["items"][-1]["source"] == "human"


def test_packaging_returns_tracking_not_nih():
    form = fill_intake(SAMPLE, "Doe_R01_Aims.docx")
    overrides = {r["id"]: "yes" for r in form["items"] if r["value"] == "unknown" or not r["complete"]}
    form = apply_overrides(form, overrides)
    snap = create_office_package(
        filename="Doe_R01_Aims.docx",
        intake=form,
        findings=[],
        text_excerpt=SAMPLE,
        submitted_by="PI",
    )
    assert snap["tracking_number"].startswith("ORA-")
    assert snap["destination"] == "Office of Research Aid database"
    assert snap["not"] == "NIH_ASSIST"
    assert "MANIFEST.json" in snap["files"]
    assert "intake-form.json" in snap["files"]


def test_incomplete_intake_cannot_package():
    form = fill_intake("short draft", "x.docx")
    try:
        create_office_package(intake=form)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "incomplete" in str(e).lower()
