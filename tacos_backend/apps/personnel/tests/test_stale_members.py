from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.personnel.models import Member, MemberStatus
from apps.personnel.tasks import deactivate_stale_active_members


class StaleActiveMembersTaskTest(TestCase):
    def create_member(
        self,
        user_id: str,
        status: str = MemberStatus.ACTIVE,
        *,
        last_login=None,
        date_joined=None,
    ) -> Member:
        User = get_user_model()
        user = User.objects.create_user(
            user_id=user_id,
            password="password123",
            name=user_id,
        )
        update_fields = {}
        if last_login is not None:
            update_fields["last_login"] = last_login
        if date_joined is not None:
            update_fields["date_joined"] = date_joined
        if update_fields:
            User.objects.filter(pk=user.pk).update(**update_fields)
            user.refresh_from_db()
        return Member.objects.create(user=user, name=user_id, status=status)

    def test_deactivates_only_stale_active_members(self):
        now = timezone.now()
        stale_time = now - timedelta(days=200)
        recent_time = now - timedelta(days=30)

        stale_active = self.create_member("20210001", last_login=stale_time)
        recent_active = self.create_member("20210002", last_login=recent_time)
        never_logged_old = self.create_member(
            "20210003",
            date_joined=stale_time,
        )
        never_logged_recent = self.create_member(
            "20210004",
            date_joined=recent_time,
        )
        alumni = self.create_member(
            "20210005",
            status=MemberStatus.ALUMNI,
            last_login=stale_time,
        )
        inactive = self.create_member(
            "20210006",
            status=MemberStatus.INACTIVE,
            last_login=stale_time,
        )

        result = deactivate_stale_active_members()

        self.assertEqual(result["updated_count"], 2)
        for member in (
            stale_active,
            recent_active,
            never_logged_old,
            never_logged_recent,
            alumni,
            inactive,
        ):
            member.refresh_from_db()

        self.assertEqual(stale_active.status, MemberStatus.INACTIVE)
        self.assertEqual(never_logged_old.status, MemberStatus.INACTIVE)
        self.assertEqual(recent_active.status, MemberStatus.ACTIVE)
        self.assertEqual(never_logged_recent.status, MemberStatus.ACTIVE)
        self.assertEqual(alumni.status, MemberStatus.ALUMNI)
        self.assertEqual(inactive.status, MemberStatus.INACTIVE)
