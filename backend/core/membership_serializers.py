"""Membership serializers. Separate file from core/serializers.py because
membership is a distinct domain (access control) and mixing it in makes the
permission surface harder to audit."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Membership

User = get_user_model()


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "user_id", "username", "role")
        read_only_fields = ("id", "user_id", "username")


class InviteSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=["EDITOR", "VIEWER"])

    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("No user with that username.")
        return value
