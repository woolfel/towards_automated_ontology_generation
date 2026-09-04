"""
Pydantic schema for Competency Questions (CQs).

This file was missing from the repo (agents/cq_generator.py imports it but
it didn't exist). Reconstructed from how CompetencyQuestion/CQList are
actually used elsewhere in the codebase, rather than guessed from scratch:

- agents/cq_generator.py builds `CQList.model_json_schema()` into the CQ
  generation prompt, calls `structured_llm.invoke(...)` to get a `CQList`,
  then does `cq_list_object.model_dump()['questions']` and writes that list
  straight to cqs/generated/<contract>.json.
- agents/eval.py, agents/vector_eval.py, and agents/ontology_generator.py
  all read those saved CQ dicts, and every single one of them accesses only
  two keys: cq['competency_question'] and cq['expected_answer'].
- The already-generated files in cqs/generated/ (310 real CQs total, from
  before this module went missing) confirm this: every entry in both files
  has exactly those two keys and nothing else.
- The CQ-generation prompt in cq_generator.py *also* asks the LLM to fill in
  `key_entities` and `odp_hint` (an Ontology Design Pattern hint, e.g.
  "Event Reification", "Participation", "Quantity", "Time Interval",
  "Situation") for each question, even though no downstream code reads
  them and the historical output never contains them. They're included
  below as optional fields so that information isn't silently dropped if a
  model does provide it, without requiring it (and without changing the
  on-disk shape of CQs that don't have it -- see the `exclude_none=True` in
  cq_generator.py's `model_dump()` call).
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Used when the model can't find an answer to a CQ on the page it's looking
# at (common: a page-by-page prompt only sees one page's text, and the
# detail a given CQ asks about may live on a different page). Kept as a
# plain string (rather than making expected_answer Optional) since
# agents/eval.py, agents/vector_eval.py, and agents/ontology_generator.py
# all index into cq['expected_answer'] directly and expect a string.
NO_ANSWER_FOUND = "Not found in this section of the text."


class CompetencyQuestion(BaseModel):
    """A single competency question extracted from one page of a contract."""

    competency_question: str = Field(
        description="The atomic competency question, phrased as a question."
    )
    expected_answer: str = Field(
        description="The precise expected answer, taken verbatim from the source text."
    )
    key_entities: Optional[List[str]] = Field(
        default=None,
        description="Key entities/concepts this competency question revolves around.",
    )
    odp_hint: Optional[str] = Field(
        default=None,
        description=(
            "The Ontology Design Pattern this CQ is meant to drive, e.g. "
            "'Event Reification', 'Participation', 'Quantity', 'Time Interval', "
            "or 'Situation'."
        ),
    )

    @field_validator("expected_answer", mode="before")
    @classmethod
    def _coerce_missing_answer(cls, v):
        """
        Despite expected_answer being marked required in the schema handed to
        the LLM, models sometimes return null for a CQ they can't answer from
        the current page's text (observed in practice: e.g. asking for a
        dollar amount that isn't mentioned on that particular page). Without
        this, a single null answer fails validation for the *entire* page's
        batch of CQs, discarding otherwise-good questions along with it.
        """
        if v is None:
            return NO_ANSWER_FOUND
        return v


class CQList(BaseModel):
    """A page's worth of competency questions, as returned by the LLM."""

    questions: List[CompetencyQuestion] = Field(
        default_factory=list,
        description="The list of competency questions generated for this page.",
    )
