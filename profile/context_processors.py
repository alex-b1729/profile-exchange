from profile.models import ConnectionRequest


def connection_requests(request):
    context_data = dict()
    if request.user.is_authenticated:
        context_data['connection_request_count'] = ConnectionRequest.outstanding.filter(
            profile_to__user=request.user,
        ).count()
    return context_data
