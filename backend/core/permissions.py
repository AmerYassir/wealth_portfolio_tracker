"""DRF permission classes.

`IsPortfolioMember` is the *coarse* gate: the requesting user must be an
authenticated member of the portfolio being acted on. It does NOT enforce
role (Owner/Editor/Viewer). Role checks live in the view layer, where the
operation (read vs write) is visible, and use
`core.services.user_role_on_portfolio` as the single source of truth.

Design note: `has_object_permission` returns False → DRF raises 403 for
authenticated non-members. That is the spec's "not found or access denied"
behavior on the API side — we choose 403 over 404 here because the API is
navigable and the portfolio id is disclosed in the URL. The *agent* tool
layer collapses 403 and 404 into "not found or access denied" for the LLM.
The two layers are consistent in the answer they return; they differ only in
HTTP status, which is fine because no one parses the agent tool's HTTP status.
"""
from rest_framework.permissions import BasePermission

from . import services


class IsPortfolioMember(BasePermission):
    """Object-level check: request.user is a member of the target portfolio.

    Expects the view to expose `get_portfolio_id_from_object(obj)` returning
    the portfolio pk for `obj` (an Asset, a Portfolio, or a Transaction).
    """

    message = "Not found or access denied."

    def has_permission(self, request, view):
        # Authentication is enforced by DRF IsAuthenticated in
        # DEFAULT_PERMISSION_CLASSES. This class only cares about membership,
        # which requires an object.
        return True

    def has_object_permission(self, request, view, obj):
        portfolio_id = self._portfolio_id_from(obj)
        if portfolio_id is None:
            return False
        return services.user_role_on_portfolio(request.user, portfolio_id) is not None

    @staticmethod
    def _portfolio_id_from(obj) -> int | None:
        # Portfolio
        if getattr(obj, "_meta", None) and obj._meta.model_name == "portfolio":
            return obj.pk
        # Asset
        if getattr(obj, "_meta", None) and obj._meta.model_name == "asset":
            return obj.portfolio_id
        # Transaction -> Asset -> Portfolio
        if getattr(obj, "_meta", None) and obj._meta.model_name == "transaction":
            return obj.asset.portfolio_id
        return None
