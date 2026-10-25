from django.contrib.auth.models import AnonymousUser
from django.urls import path
from django_ag_ui import AGUIServer
from rest_framework_simplejwt.authentication import JWTAuthentication

from agent.agent_tools import registry, set_current_user


def get_user(request):
    """JWT → User. The ONLY place identity enters the agent."""
    try:
        auth = JWTAuthentication()
        validated = auth.authenticate(request)
        if validated is not None:
            user = validated[0]
            set_current_user(user)
            return user
    except Exception:
        pass
    set_current_user(AnonymousUser())
    return AnonymousUser()


agent = AGUIServer(
    registry,
    get_user=get_user,
    require_authenticated=True,
)

urlpatterns = [
    path("", agent.urls),
]
