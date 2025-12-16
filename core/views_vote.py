from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from .models import Election, Candidate, Vote, AuditLog
from django.utils import timezone


@login_required
def cast_vote(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    if not (election.start_time <= timezone.now() <= election.end_time):
        return render(request, 'core/vote_closed.html', {'election': election})

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        candidate = get_object_or_404(Candidate, pk=candidate_id, election=election)
        try:
            with transaction.atomic():
                Vote.objects.create(election=election, voter=request.user, candidate=candidate)
        except IntegrityError:
            # already voted
            return render(request, 'core/already_voted.html', {'election': election})

        AuditLog.objects.create(user=request.user, action='vote_cast', details={'election_id': election.id, 'candidate_id': candidate.id}, ip=request.META.get('REMOTE_ADDR'))
        return render(request, 'core/vote_thanks.html', {'election': election, 'candidate': candidate})

    return render(request, 'core/cast_vote.html', {'election': election})
