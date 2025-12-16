from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Election, Candidate, Vote, AuditLog


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('USOVS', {'fields': ('firebase_uid', 'phone_number', 'is_verified_student', 'is_election_admin')}),
    )


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'is_active')
    actions = ['export_results_csv']

    def export_results_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from .models import Vote

        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="election_results.csv"'
        writer = csv.writer(response)
        writer.writerow(['election_id', 'election_title', 'candidate_id', 'candidate_name', 'vote_count'])

        for election in queryset:
            for candidate in election.candidates.all():
                vote_count = Vote.objects.filter(election=election, candidate=candidate).count()
                writer.writerow([election.id, election.title, candidate.id, candidate.name, vote_count])

        return response
    export_results_csv.short_description = 'Export selected election results as CSV'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'election')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('election', 'voter', 'candidate', 'timestamp')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'user', 'ip')
