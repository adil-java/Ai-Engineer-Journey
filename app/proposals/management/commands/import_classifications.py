"""Bridge pipeline → app: turn data/clean/classifications.jsonl into pending proposals.

    python manage.py import_classifications

Idempotent: the unique constraint (repo, issue, content_hash, prompt_version) means re-running
creates nothing new. Candidates stay empty until the expert finder exists (Phase 3).
"""

import json

from django.core.management.base import BaseCommand
from django.db import transaction

from app.proposals.models import AuditLog, Proposal
from llm.classify import CACHE_PATH
from llm.schemas import ClassificationRecord
from transform.issues import load_issues


class Command(BaseCommand):
    help = "Create pending proposals from classified issues."

    def handle(self, *args, **options):
        if not CACHE_PATH.exists():
            self.stderr.write("No classifications yet. Run: python -m llm.classify")
            return

        titles = {issue["number"]: issue.get("title") or "" for issue in load_issues()}
        created = skipped = bad = 0

        with CACHE_PATH.open(encoding="utf-8") as f:
            for line in f:
                try:
                    record = ClassificationRecord.model_validate_json(line)
                except ValueError:
                    bad += 1
                    continue
                with transaction.atomic():
                    proposal, is_new = Proposal.objects.get_or_create(
                        repo="nestjs/nest",
                        issue_number=record.issue_number,
                        content_hash=record.content_hash,
                        prompt_version=record.prompt_version,
                        defaults={
                            "issue_title": titles.get(record.issue_number, "")[:500],
                            "model": record.model,
                            "classification": record.classification.model_dump(),
                        },
                    )
                    if is_new:
                        AuditLog.objects.create(
                            proposal=proposal, action=AuditLog.Action.CREATED,
                            details={"source": "import_classifications"},
                        )
                created += is_new
                skipped += not is_new

        self.stdout.write(self.style.SUCCESS(f"created {created} | already existed {skipped} | invalid lines {bad}"))
