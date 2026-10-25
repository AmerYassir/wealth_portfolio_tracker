"""Membership endpoints, nested under /portfolios/<id>/members/.

Rules (matching the existing role model):
- List: any member (Owner / Editor / Viewer) can read the roster.
- Invite (POST): Owner only.
- Remove (DELETE): Owner only.
- The Owner cannot remove themselves — that would orphan the portfolio.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .membership_serializers import InviteSerializer, MembershipSerializer
from .models import Membership, Portfolio


class _PortfolioMemberBase(APIView):
    permission_classes = [IsAuthenticated]

    def _portfolio(self, portfolio_pk):
        portfolio = services.get_portfolio_for_user(self.request.user, portfolio_pk)
        if portfolio is None:
            raise PermissionDenied("Not found or access denied.")
        return portfolio

    def _require_owner(self, portfolio):
        role = services.user_role_on_portfolio(self.request.user, portfolio.id)
        if role != "OWNER":
            raise PermissionDenied("Only the owner can manage members.")


class MembershipListCreateView(_PortfolioMemberBase):
    def get(self, request, portfolio_pk):
        portfolio = self._portfolio(portfolio_pk)
        memberships = (
            Membership.objects.filter(portfolio=portfolio)
            .select_related("user")
            .order_by("user__username")
        )
        return Response(MembershipSerializer(memberships, many=True).data)

    def post(self, request, portfolio_pk):
        portfolio = self._portfolio(portfolio_pk)
        self._require_owner(portfolio)

        ser = InviteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        username = ser.validated_data["username"]
        role = ser.validated_data["role"]

        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.get(username=username)

        if Membership.objects.filter(user=target, portfolio=portfolio).exists():
            raise ValidationError({"username": "That user is already a member."})

        membership = Membership.objects.create(
            user=target, portfolio=portfolio, role=role
        )
        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


class MembershipDetailView(_PortfolioMemberBase):
    def delete(self, request, portfolio_pk, pk):
        portfolio = self._portfolio(portfolio_pk)
        self._require_owner(portfolio)

        membership = get_object_or_404(Membership, pk=pk, portfolio=portfolio)
        if membership.user_id == request.user.id:
            raise ValidationError(
                {"detail": "You cannot remove yourself from the portfolio."}
            )
        if membership.role == "OWNER":
            raise ValidationError(
                {"detail": "Cannot remove an owner. Transfer ownership first (not supported yet)."}
            )
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
