from django import forms
from .models import Vote, Candidate


class VoteForm(forms.Form):
    candidate_id = forms.IntegerField()
