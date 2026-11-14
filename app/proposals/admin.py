from django.contrib import admin, messages
from django.utils.html import format_html

from .models import AuditLog, Proposal
from .services import DecisionError, decide


class AuditInline(admin.TabularInline):
    model = AuditLog
    extra = 0
    can_delete = False
    readonly_fields = ["action", "actor", "details", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ["issue_link", "issue_title", "type", "area", "priority", "status", "final_assignee", "created_at"]
    list_filter = ["status", "prompt_version", "model"]
    search_fields = ["issue_title", "issue_number"]
    actions = ["approve_top_candidate", "reject"]
    inlines = [AuditInline]
    # The AI's output and the decision are never edited by hand; decisions go through services.decide().
    readonly_fields = [
        "repo", "issue_number", "issue_title", "content_hash", "prompt_version", "model",
        "classification", "candidates", "status", "final_assignee", "decided_by", "decided_at", "created_at",
    ]

    def has_add_permission(self, request):
        return False  # proposals come from the pipeline, not from humans

    def has_delete_permission(self, request, obj=None):
        return False  # keep history

    @admin.display(description="Issue")
    def issue_link(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener">#{}</a>', obj.issue_url, obj.issue_number)

    @admin.display(description="Type")
    def type(self, obj):
        return obj.classification.get("type")

    @admin.display(description="Area")
    def area(self, obj):
        return obj.classification.get("area")

    @admin.display(description="Priority")
    def priority(self, obj):
        return obj.classification.get("priority")

    def _decide(self, request, queryset, approve: bool):
        done = 0
        for proposal in queryset:
            try:
                decide(proposal.pk, request.user, approve=approve)
                done += 1
            except DecisionError as exc:
                self.message_user(request, str(exc), messages.WARNING)
        if done:
            self.message_user(request, f"{done} proposal(s) {'approved' if approve else 'rejected'}.")

    @admin.action(description="Approve top candidate")
    def approve_top_candidate(self, request, queryset):
        self._decide(request, queryset, approve=True)

    @admin.action(description="Reject")
    def reject(self, request, queryset):
        self._decide(request, queryset, approve=False)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "proposal", "action", "actor"]
    list_filter = ["action"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
