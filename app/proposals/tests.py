"""Run: python manage.py test app.proposals"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from .models import AuditLog, Proposal
from .services import DecisionError, decide


def make_proposal(**overrides):
    fields = dict(
        issue_number=1, content_hash="h", prompt_version="v1", model="m",
        classification={"type": "bug", "area": "core", "priority": "high"},
        candidates=[{"login": "kamil", "score": 0.9}],
    )
    return Proposal.objects.create(**(fields | overrides))


class DecideTests(TestCase):
    def setUp(self):
        self.lead = get_user_model().objects.create_user("lead", password="x-long-password-1")

    def test_approve_uses_top_candidate_and_writes_audit(self):
        p = decide(make_proposal().pk, self.lead, approve=True)
        self.assertEqual((p.status, p.final_assignee, p.decided_by), ("approved", "kamil", self.lead))
        self.assertEqual(AuditLog.objects.get().action, "approved")

    def test_cannot_decide_twice(self):
        p = make_proposal()
        decide(p.pk, self.lead, approve=False)
        with self.assertRaises(DecisionError):
            decide(p.pk, self.lead, approve=True)
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_approve_without_candidates_needs_explicit_assignee(self):
        p = make_proposal(candidates=[])
        with self.assertRaises(DecisionError):
            decide(p.pk, self.lead, approve=True)
        self.assertEqual(decide(p.pk, self.lead, approve=True, assignee="jane").final_assignee, "jane")

    def test_same_input_cannot_create_two_proposals(self):
        make_proposal()
        with self.assertRaises(IntegrityError):
            make_proposal()


class AdminInboxTests(TestCase):
    def test_inbox_and_detail_render_for_staff(self):
        p = make_proposal()
        admin_user = get_user_model().objects.create_superuser("admin", password="x-long-password-1")
        self.client.force_login(admin_user)
        inbox = self.client.get("/admin/proposals/proposal/")
        self.assertContains(inbox, "#1")
        self.assertContains(inbox, "core")
        self.assertEqual(self.client.get(f"/admin/proposals/proposal/{p.pk}/change/").status_code, 200)

    def test_inbox_requires_login(self):
        self.assertEqual(self.client.get("/admin/proposals/proposal/").status_code, 302)


class HealthTests(TestCase):
    def test_health(self):
        self.assertEqual(self.client.get("/health/").json(), {"status": "ok"})
