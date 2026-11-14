"""Mission 1 · Task 1.3: the shape every classification must have.

The same model is (1) sent to Gemini as the response schema and (2) used to validate what
comes back. Enums (Literal) stop the model from inventing new categories.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

IssueType = Literal["bug", "feature", "docs", "question"]
Priority = Literal["low", "medium", "high", "critical"]

# Top-level packages in nestjs/nest (packages/*), plus buckets for everything else.
CodeArea = Literal[
    "common", "core", "microservices", "platform-express", "platform-fastify",
    "platform-socket.io", "platform-ws", "testing", "websockets",
    "build-tooling", "documentation", "other",
]

MAX_SKILLS = 5


class IssueClassification(BaseModel):
    type: IssueType
    area: CodeArea
    priority: Priority
    skills: list[str] = Field(description=f"1-{MAX_SKILLS} short technical skills needed, e.g. 'rxjs', 'typescript decorators'")
    reasoning: str = Field(description="One sentence explaining the classification")

    @field_validator("skills")
    @classmethod
    def check_skills(cls, skills: list[str]) -> list[str]:
        cleaned = [s.strip().lower() for s in skills if s.strip()]
        if not 1 <= len(cleaned) <= MAX_SKILLS:
            raise ValueError(f"expected 1-{MAX_SKILLS} skills, got {len(cleaned)}")
        return cleaned


class ClassificationRecord(BaseModel):
    """One line in data/clean/classifications.jsonl: the result plus everything needed to audit it."""
    issue_number: int
    content_hash: str
    prompt_version: str
    model: str
    classification: IssueClassification
    input_tokens: int
    output_tokens: int
    cost_usd: float
    created_at: str
