"""The only code allowed to change a proposal's decision. Admin, views and (later) the
GitHub App all go through here, so the audit log can't be skipped."""

from django.db import transaction
from django.utils import timezone

from .models import AuditLog, Proposal


class DecisionError(Exception):
    pass


@transaction.atomic
def decide(proposal_id: int, user, approve: bool, assignee: str = "") -> Proposal:
    # Row lock: two leads clicking at once can't both decide the same proposal.
    proposal = Proposal.objects.select_for_update().get(pk=proposal_id)
    if proposal.status != Proposal.Status.PENDING:
        raise DecisionError(f"{proposal} was already {proposal.status}")

    if approve:
        assignee = assignee or (proposal.candidates[0]["login"] if proposal.candidates else "")
        if not assignee:
            raise DecisionError(f"{proposal} has no candidates yet; choose an assignee")
        proposal.status = Proposal.Status.APPROVED
        proposal.final_assignee = assignee
    else:
        proposal.status = Proposal.Status.REJECTED

    proposal.decided_by = user
    proposal.decided_at = timezone.now()
    proposal.save(update_fields=["status", "final_assignee", "decided_by", "decided_at"])

    AuditLog.objects.create(
        proposal=proposal,
        action=AuditLog.Action.APPROVED if approve else AuditLog.Action.REJECTED,
        actor=user,
        details={"assignee": proposal.final_assignee},
    )
    # Phase 6: on approve, enqueue the GitHub write (comment + assign) here, after commit.
    return proposal
