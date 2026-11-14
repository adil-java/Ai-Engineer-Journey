from django.conf import settings
from django.db import models


class Proposal(models.Model):
    """What WhoFix suggests for one issue. Nothing reaches GitHub until a human decides."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    repo = models.CharField(max_length=200, default="nestjs/nest")
    issue_number = models.PositiveIntegerField()
    issue_title = models.CharField(max_length=500, blank=True)

    # Provenance: exactly which input + prompt + model produced this.
    content_hash = models.CharField(max_length=64)
    prompt_version = models.CharField(max_length=20)
    model = models.CharField(max_length=100)

    classification = models.JSONField()  # IssueClassification as a dict
    # Phase 3 fills this: [{"login": "...", "score": 0.8, "evidence_prs": [123, 456]}, ...]
    candidates = models.JSONField(default=list, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    final_assignee = models.CharField(max_length=100, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Importing the same classification twice must not create a second proposal.
            models.UniqueConstraint(
                fields=["repo", "issue_number", "content_hash", "prompt_version"],
                name="uniq_proposal_per_input",
            ),
        ]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.repo}#{self.issue_number}"

    @property
    def issue_url(self) -> str:
        return f"https://github.com/{self.repo}/issues/{self.issue_number}"


class AuditLog(models.Model):
    """Append-only record of every action on a proposal (who, what, when)."""

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    proposal = models.ForeignKey(Proposal, on_delete=models.PROTECT, related_name="audit")
    action = models.CharField(max_length=10, choices=Action.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )  # null = the system (importer)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.proposal} {self.action}"
