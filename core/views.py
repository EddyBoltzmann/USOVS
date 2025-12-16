import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .models import User, AuditLog

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import datetime

logger = logging.getLogger(__name__)

# Initialize Firebase app once
if settings.FIREBASE_CREDENTIALS_JSON:
    try:
        # Support passing either a JSON string or a path to a JSON file
        raw = settings.FIREBASE_CREDENTIALS_JSON
        try:
            cred_json = json.loads(raw)
            cred = credentials.Certificate(cred_json)
        except Exception:
            # treat as file path
            cred = credentials.Certificate(raw)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.exception("Failed to initialize Firebase: %s", e)


def index(request):
    return render(request, 'core/index.html')


def login_page(request):
    firebase_config = {
        'apiKey': settings.FIREBASE_API_KEY,
        'authDomain': settings.FIREBASE_AUTH_DOMAIN,
    }
    return render(request, 'core/login.html', {'firebase_config': firebase_config})


@csrf_exempt
@require_POST
def firebase_verify(request):
    data = json.loads(request.body.decode('utf-8'))
    id_token = data.get('id_token')
    if not id_token:
        return HttpResponseBadRequest('Missing id_token')

    ip = request.META.get('REMOTE_ADDR')

    # Simple per-IP attempt limiting (DB-backed) - count attempts in window
    from .firebase_models import VerificationAttempt, FirebaseTokenUse
    now = timezone.now()
    window_start = now - timezone.timedelta(seconds=settings.FIREBASE_VERIFICATION_WINDOW_SECONDS)
    recent_ip_attempts = VerificationAttempt.objects.filter(ip=ip, timestamp__gte=window_start).count()
    if recent_ip_attempts >= settings.FIREBASE_VERIFICATION_MAX_ATTEMPTS_PER_IP:
        VerificationAttempt.objects.create(ip=ip, success=False, reason='rate_limited')
        return JsonResponse({'error': 'rate_limited'}, status=429)

    # We compute token hash now (do not store token plaintext)
    import hashlib
    token_hash = hashlib.sha256(id_token.encode('utf-8')).hexdigest()

    # Verify token with Firebase
    try:
        decoded = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        logger.exception('Invalid Firebase token: %s', e)
        VerificationAttempt.objects.create(ip=ip, success=False, reason='invalid_token')
        return JsonResponse({'error': 'invalid_token'}, status=400)

    uid = decoded.get('uid')
    email = decoded.get('email')
    phone = decoded.get('phone_number')

    # Enforce strict token age
    import datetime as _dt
    iat = decoded.get('iat')
    if iat:
        issued_dt = _dt.datetime.fromtimestamp(int(iat), tz=_dt.timezone.utc)
        age = (now - issued_dt).total_seconds()
        if age > settings.FIREBASE_TOKEN_MAX_AGE_SECONDS:
            VerificationAttempt.objects.create(uid=uid, ip=ip, success=False, reason='token_too_old')
            AuditLog.objects.create(action='firebase_verify_blocked_old_token', ip=ip, details={'uid': uid, 'age_seconds': age})
            return JsonResponse({'error': 'token_too_old'}, status=400)

    # Atomic check-and-mark for token reuse prevention
    try:
        with transaction.atomic():
            token_use, created = FirebaseTokenUse.objects.select_for_update().get_or_create(
                token_hash=token_hash,
                defaults={'uid': uid, 'issued_at': (datetime.datetime.fromtimestamp(int(iat), tz=datetime.timezone.utc) if iat else None), 'expires_at': (datetime.datetime.fromtimestamp(int(decoded.get('exp')), tz=datetime.timezone.utc) if decoded.get('exp') else None), 'ip': ip, 'details': {'email': email, 'phone': phone}}
            )

            if not created and token_use.used_at:
                # Token was already used — replay detected
                VerificationAttempt.objects.create(user=None, uid=uid, ip=ip, success=False, reason='token_reuse')
                AuditLog.objects.create(action='firebase_token_reuse', ip=ip, details={'uid': uid})
                return JsonResponse({'error': 'token_reuse'}, status=403)

            # Mark token as used now
            token_use.used_at = now
            token_use.user = None
            token_use.save()
    except Exception as e:
        logger.exception('Token verification error: %s', e)
        VerificationAttempt.objects.create(uid=uid, ip=ip, success=False, reason='internal_error')
        return JsonResponse({'error': 'internal_error'}, status=500)

    # Link or create local user
    user = None
    try:
        user = User.objects.get(firebase_uid=uid)
    except User.DoesNotExist:
        # Create or link by email if exists
        username = email or phone or uid
        if email:
            user, created = User.objects.get_or_create(email=email, defaults={'username': username})
            if created:
                user.set_password(get_random_string(50))
        else:
            user = User.objects.create_user(username=username, password=get_random_string(50))
        user.firebase_uid = uid
        user.is_verified_student = True
        if phone:
            user.phone_number = phone
        user.save()

    # Associate token_use with user
    token_use.user = user
    token_use.save()

    # Record successful verification
    VerificationAttempt.objects.create(user=user, uid=uid, ip=ip, success=True, reason='ok')
    AuditLog.objects.create(user=user, action='firebase_verify', ip=ip, details={'uid': uid, 'email': email, 'phone': phone})

    # Log user in
    login(request, user)

    return JsonResponse({'status': 'ok'})


@csrf_exempt
@require_POST
def log_otp_sent(request):
    # Endpoint for clients to notify the server that an OTP was issued (optional)
    data = json.loads(request.body.decode('utf-8'))
    method = data.get('method')  # 'sms' or 'email'
    address = data.get('address')
    uid = data.get('uid')
    ip = request.META.get('REMOTE_ADDR')

    from .firebase_models import OTPSendLog
    OTPSendLog.objects.create(method=method or 'unknown', address=address or '', uid=uid or '', ip=ip, details={})
    AuditLog.objects.create(action='firebase_otp_issued', ip=ip, details={'method': method, 'address': address, 'uid': uid})

    return JsonResponse({'status': 'logged'})


def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'core/profile.html')


@login_required
def admin_export_csv(request, election_id):
    # Admin-only endpoint protected by Django session authentication
    if not (request.user.is_election_admin or request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden('forbidden')

    import csv
    from .models import Election, Vote, AuditLog

    try:
        election = Election.objects.get(pk=election_id)
    except Election.DoesNotExist:
        return HttpResponse(status=404)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="election_{election_id}_results.csv"'
    writer = csv.writer(response)
    writer.writerow(['election_id', 'election_title', 'candidate_id', 'candidate_name', 'vote_count'])

    for candidate in election.candidates.all():
        vote_count = Vote.objects.filter(election=election, candidate=candidate).count()
        writer.writerow([election.id, election.title, candidate.id, candidate.name, vote_count])

    # Audit log the export
    AuditLog.objects.create(user=request.user, action='export_results', ip=request.META.get('REMOTE_ADDR'), details={'election_id': election.id})

    return response
