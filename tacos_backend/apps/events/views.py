from __future__ import annotations

import logging
import os
from io import BytesIO
from typing import Any

from django.db.models import Prefetch, Q
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.utils.encoding import smart_str

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.utils import envelope_error
from apps.common.viewsets import EnvelopeModelViewSet
from apps.personnel.models import Member, MemberStatus
from apps.personnel.sorting import sort_members
from apps.sheet_music.models import Sheet
from apps.sheet_music.serializers import SheetSerializer
from apps.sheet_music.sorting import sort_sheets

from .models import (
    Assignment,
    AssignmentAttachment,
    AssignmentSubmission,
    AssignmentSubmissionAttachment,
    CheckinType,
    Event,
    EventAnnouncementImage,
    EventCheckinRecord,
    EventCheckinSession,
    EventVisibility,
)
from .permissions import IsAdminOrEventAdmin
from .serializers import (
    AssignmentAttachmentSerializer,
    AssignmentSerializer,
    AssignmentSubmissionAttachmentSerializer,
    AssignmentSubmissionSerializer,
    EventBasicSerializer,
    EventCheckinRecordSerializer,
    EventCheckinSessionSerializer,
    EventSerializer,
    MemberBriefSerializer,
)


class EventViewSet(EnvelopeModelViewSet):
    queryset = (
        Event.objects.prefetch_related(
            Prefetch(
                "admins",
                queryset=Member.objects.only("id"),
                to_attr="prefetched_admins",
            ),
            Prefetch(
                "participants",
                queryset=Member.objects.only("id"),
                to_attr="prefetched_participants",
            ),
            "announcement_images",
        )
        .all()
        .order_by("-start_date", "-created_at")
    )
    serializer_class = EventSerializer
    permission_classes = [IsAdminOrEventAdmin]
    lookup_field = "public_id"
    filterset_fields = {
        "visibility": ["exact"],
        "visible_to_alumni": ["exact"],
        "start_date": ["exact", "lte", "gte"],
        "end_date": ["exact", "lte", "gte"],
    }
    search_fields = ["name"]

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()

        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        only_participated = str(
            self.request.query_params.get("only_participated", "")
        ).lower() in {"1", "true", "yes", "on"}

        if is_site_admin:
            if only_participated:
                member = getattr(user, "member", None)
                if member:
                    return qs.filter(participants=member).distinct()
                return qs.none()
            return qs

        member = getattr(user, "member", None)
        if member:
            member_status = getattr(member, "status", MemberStatus.ACTIVE)
            if member_status == MemberStatus.ALUMNI:
                base_qs = qs.filter(
                    Q(visible_to_alumni=True)
                    | Q(participants=member)
                    | Q(admins=member)
                ).distinct()
            elif member_status == MemberStatus.INACTIVE:
                base_qs = qs.none()
            else:
                member_tier = getattr(member, "tier", "")
                tier_q = Q()
                if member_tier == "一队":
                    tier_q |= Q(visibility=EventVisibility.FIRST)
                elif member_tier == "二队":
                    tier_q |= Q(visibility=EventVisibility.SECOND)

                base_qs = qs.filter(
                    Q(visibility=EventVisibility.ALL)
                    | tier_q
                    | Q(participants=member)
                    | Q(admins=member)
                ).distinct()
        else:
            base_qs = qs.filter(visibility=EventVisibility.ALL)

        if only_participated:
            if member:
                return base_qs.filter(participants=member).distinct()
            return base_qs.none()

        return base_qs

    def get_serializer_class(self):  # type: ignore[override]
        if getattr(self, "action", None) in {"list", "retrieve"}:
            return EventBasicSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer: EventSerializer) -> None:  # type: ignore[override]
        serializer.save()

    # =====================
    # =====================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="announcement/images",
    )
    def upload_announcement_image(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        is_event_admin = (
            getattr(user, "member", None)
            and event.admins.filter(pk=user.member.id).exists()
        )
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        if not (is_event_admin or is_site_admin):
            return Response(envelope_error(403, "无权限上传公告图片", {}), status=403)
        file = request.FILES.get("image") or request.FILES.get("file")
        if not file:
            return Response(envelope_error(422, "需要提供图片文件", {}), status=422)
        content_type = getattr(file, "content_type", "") or ""
        allowed_types = {"image/jpeg", "image/png", "image/gif"}
        if content_type not in allowed_types:
            return Response(
                envelope_error(422, "仅支持 JPG/PNG/GIF 图片", {}), status=422
            )
        max_size = 5 * 1024 * 1024  # 5MB
        if getattr(file, "size", 0) > max_size:
            return Response(envelope_error(422, "图片大小不能超过5MB", {}), status=422)
        img = EventAnnouncementImage.objects.create(event=event, image=file)
        data = {
            "id": img.id,
            "image": (
                request.build_absolute_uri(img.image.url)
                if hasattr(request, "build_absolute_uri")
                else getattr(img.image, "url", "")
            ),
            "created_at": img.created_at,
        }
        return Response(data, status=201)

    @action(
        detail=True,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path=r"announcement/images/(?P<image_id>[^/.]+)",
    )
    def delete_announcement_image(
        self, request, public_id=None, image_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        is_event_admin = (
            getattr(user, "member", None)
            and event.admins.filter(pk=user.member.id).exists()
        )
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        if not (is_event_admin or is_site_admin):
            return Response(envelope_error(403, "无权限删除公告图片", {}), status=403)
        if not image_id:
            return Response(envelope_error(422, "需要提供图片ID", {}), status=422)
        try:
            img = event.announcement_images.get(pk=int(image_id))
        except Exception:
            return Response(envelope_error(404, "公告图片不存在", {}), status=404)
        img.delete()
        return Response(status=204)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="join",
    )
    def join(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        member = getattr(user, "member", None)
        if not member:
            return Response(
                envelope_error(422, "仅队员可以报名参加活动", {}), status=422
            )
        if event.participants.filter(pk=member.id).exists():
            return Response({"joined": True})
        if event.admins.filter(pk=member.id).exists():
            event.participants.add(member)
            return Response({"joined": True})
        if getattr(member, "status", MemberStatus.ACTIVE) == MemberStatus.ALUMNI:
            if event.visible_to_alumni:
                event.participants.add(member)
                return Response({"joined": True})
            return Response(
                envelope_error(403, "仅校友可见活动允许校友报名", {}),
                status=403,
            )
        if event.visibility == EventVisibility.ALL:
            pass
        elif event.visibility == EventVisibility.FIRST:
            if getattr(member, "tier", "") != "一队":
                return Response(
                    envelope_error(403, "仅一队成员可报名该活动", {}), status=403
                )
        elif event.visibility == EventVisibility.SECOND:
            if getattr(member, "tier", "") != "二队":
                return Response(
                    envelope_error(403, "仅二队成员可报名该活动", {}), status=403
                )
        else:  # 部分可见
            return Response(
                envelope_error(403, "该活动仅由管理员添加参与人员", {}), status=403
            )
        event.participants.add(member)
        return Response({"joined": True})

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/sessions",
    )
    def checkin_sessions(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        member = getattr(user, "member", None)
        is_event_member = bool(
            member
            and (
                event.participants.filter(pk=member.id).exists()
                or event.admins.filter(pk=member.id).exists()
            )
        )
        if not (is_site_admin or is_event_member):
            return Response(envelope_error(403, "无权限查看签到列表", {}), status=403)
        sessions = list(event.checkin_sessions.all().order_by("-started_at", "-id"))
        data = EventCheckinSessionSerializer(sessions, many=True).data
        return Response({"results": data, "count": len(sessions)})

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/status",
    )
    def checkin_status(self, request, public_id=None):
        event: Event = self.get_object()
        session = event.checkin_sessions.filter(is_active=True).first()
        data = None
        has_checked_in = False
        if session:
            data = EventCheckinSessionSerializer(session).data
            member = getattr(request.user, "member", None)
            if member:
                has_checked_in = EventCheckinRecord.objects.filter(
                    session=session, member=member
                ).exists()
        return Response(
            {
                "active": bool(session),
                "session": data,
                "has_checked_in": has_checked_in,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/start",
    )
    def checkin_start(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限发起签到", {}), status=403)
        payload = request.data.copy()
        payload["event"] = event.id
        serializer = EventCheckinSessionSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        # 创建实例，但默认不激活；另提供单独开始接口
        session = serializer.save(created_by=user, is_active=False)
        # 如果前端希望立即开始（immediate=true），则将其置为active
        immediate = str(request.query_params.get("immediate", "")).lower() in {
            "1",
            "true",
            "yes",
        }
        if immediate and not event.checkin_sessions.filter(is_active=True).exists():
            session.is_active = True
            session.started_at = timezone.now()
            session.save(update_fields=["is_active", "started_at"])
        return Response(EventCheckinSessionSerializer(session).data, status=201)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/stop",
    )
    def checkin_stop(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限结束签到", {}), status=403)
        # 支持按 session_id 结束，否则结束当前进行中的
        session_id = request.data.get("session_id")
        session = None
        if session_id:
            try:
                session = event.checkin_sessions.get(pk=session_id)
            except EventCheckinSession.DoesNotExist:
                session = None
        if session is None:
            session = event.checkin_sessions.filter(is_active=True).first()
        if not session:
            return Response(envelope_error(404, "当前无进行中的签到", {}), status=404)
        session.is_active = False
        session.ended_at = timezone.now()
        session.save(update_fields=["is_active", "ended_at"])
        return Response({"stopped": True})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/begin",
    )
    def checkin_begin(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限开始签到", {}), status=403)
        session_id = request.data.get("session_id")
        if not session_id:
            return Response(envelope_error(422, "需要提供签到实例ID", {}), status=422)
        try:
            session = event.checkin_sessions.get(pk=session_id)
        except EventCheckinSession.DoesNotExist:
            return Response(envelope_error(404, "签到实例不存在", {}), status=404)
        if (
            event.checkin_sessions.filter(is_active=True)
            .exclude(pk=session.id)
            .exists()
        ):
            return Response(envelope_error(409, "已有其他进行中的签到", {}), status=409)
        session.is_active = True
        session.started_at = timezone.now()
        session.save(update_fields=["is_active", "started_at"])
        return Response({"started": True})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/submit",
    )
    def checkin_submit(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        member = getattr(user, "member", None)
        # 只有活动参与者（participants）可以签到，活动管理员（admins）如果不在participants中则不能签到
        if not member or not event.participants.filter(pk=member.id).exists():
            return Response(envelope_error(403, "仅活动成员可签到", {}), status=403)
        session = event.checkin_sessions.filter(is_active=True).first()
        if not session:
            return Response(envelope_error(404, "当前无进行中的签到", {}), status=404)
        if session.type == CheckinType.PASSWORD:
            from django.contrib.auth.hashers import check_password

            raw = str(request.data.get("password", ""))
            if not raw or not check_password(raw, session.password_hash):
                return Response(envelope_error(422, "签到密码错误", {}), status=422)
        elif session.type == CheckinType.LOCATION:
            try:
                lat = float(request.data.get("lat"))
                lng = float(request.data.get("lng"))
            except Exception:
                return Response(envelope_error(422, "需要提供定位坐标", {}), status=422)
            if session.location_lat is None or session.location_lng is None:
                return Response(
                    envelope_error(500, "签到未正确配置地点", {}), status=500
                )
            from math import asin, cos, radians, sin, sqrt

            def haversine(lat1, lng1, lat2, lng2):
                R = 6371000.0
                dlat = radians(lat2 - lat1)
                dlng = radians(lng2 - lng1)
                a = (
                    sin(dlat / 2) ** 2
                    + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
                )
                c = 2 * asin(sqrt(a))
                return R * c

            distance = haversine(
                float(session.location_lat), float(session.location_lng), lat, lng
            )
            if distance > float(session.radius_m or 500):
                return Response(
                    envelope_error(403, "不在签到范围内", {"distance": distance}),
                    status=403,
                )
        record, created = EventCheckinRecord.objects.get_or_create(
            session=session,
            member=member,
            defaults={"lat": request.data.get("lat"), "lng": request.data.get("lng")},
        )
        if not created:
            # 重复签到：返回200状态码并标记duplicate
            return Response(
                {
                    "code": 200,
                    "message": "您已签到过，无需重复签到",
                    "data": {"checked": True, "duplicate": True},
                }
            )
        return Response(EventCheckinRecordSerializer(record).data, status=201)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/records",
    )
    def checkin_records(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        member = getattr(user, "member", None)
        is_event_admin = member and event.admins.filter(pk=member.id).exists()
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        session_id = request.query_params.get("session_id")
        mine_only = str(request.query_params.get("mine", "")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if mine_only:
            if not member:
                return Response(
                    envelope_error(403, "仅队员可查看签到记录", {}), status=403
                )
            qs = EventCheckinRecord.objects.filter(
                session__event=event, member=member
            ).select_related("member__user", "session")
        elif not (is_event_admin or is_site_admin):
            if member and (
                event.participants.filter(pk=member.id).exists()
                or event.admins.filter(pk=member.id).exists()
            ):
                qs = EventCheckinRecord.objects.filter(
                    session__event=event, member=member
                ).select_related("member__user", "session")
            else:
                return Response(
                    envelope_error(403, "无权限查看签到记录", {}), status=403
                )
        else:
            qs = EventCheckinRecord.objects.filter(session__event=event).select_related(
                "member__user", "session"
            )
        if session_id:
            qs = qs.filter(session_id=session_id)
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        items = qs.order_by("-checked_at")[start:end]
        data = EventCheckinRecordSerializer(items, many=True).data
        return Response({"count": total, "results": data})

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="checkin/summary",
    )
    def checkin_summary(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        is_event_admin = (
            getattr(user, "member", None)
            and event.admins.filter(pk=user.member.id).exists()
        )
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        if not (is_event_admin or is_site_admin):
            return Response(envelope_error(403, "无权限查看签到统计", {}), status=403)
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(envelope_error(422, "需要提供签到实例ID", {}), status=422)
        try:
            session = event.checkin_sessions.get(pk=session_id)
        except EventCheckinSession.DoesNotExist:
            return Response(envelope_error(404, "签到实例不存在", {}), status=404)
        records_by_member_id = {
            int(record.member_id): record
            for record in EventCheckinRecord.objects.filter(
                session=session
            ).select_related("member__user")
        }
        member_map = {
            int(member.id): member
            for member in Member.objects.filter(
                Q(events=event) | Q(managed_events=event)
            )
            .select_related("user")
            .distinct()
        }
        members = sort_members(member_map.values())
        checked_members = []
        not_checked_members = []
        results = []
        for member in members:
            record = records_by_member_id.get(int(member.id))
            if record:
                checked_members.append(member)
            else:
                not_checked_members.append(member)
            results.append(
                {
                    "id": getattr(record, "id", None),
                    "session": int(session.id),
                    "member": int(member.id),
                    "member_public_id": getattr(member, "public_id", ""),
                    "member_name": getattr(member, "name", ""),
                    "member_user_id": getattr(
                        getattr(member, "user", None), "user_id", ""
                    ),
                    "voice_part": getattr(member, "voice_part", ""),
                    "tier": getattr(member, "tier", ""),
                    "checked_at": getattr(record, "checked_at", None),
                    "lat": getattr(record, "lat", None),
                    "lng": getattr(record, "lng", None),
                }
            )
        return Response(
            {
                "checked": MemberBriefSerializer(checked_members, many=True).data,
                "not_checked": MemberBriefSerializer(
                    not_checked_members, many=True
                ).data,
                "results": results,
                "count": len(results),
            }
        )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path=r"checkin/sessions/(?P<session_id>[^/.]+)/detail",
    )
    def get_checkin_session_detail(
        self, request, public_id=None, session_id: str | None = None
    ):
        """获取指定签到场次详情。"""
        event: Event = self.get_object()
        user = request.user
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        member = getattr(user, "member", None)
        is_event_member = bool(
            member
            and (
                event.participants.filter(pk=member.id).exists()
                or event.admins.filter(pk=member.id).exists()
            )
        )
        if not (is_site_admin or is_event_member):
            return Response(envelope_error(403, "无权限查看签到详情", {}), status=403)
        try:
            session = event.checkin_sessions.get(id=int(session_id))
        except (ValueError, EventCheckinSession.DoesNotExist):
            return Response(envelope_error(404, "签到场次不存在", {}), status=404)
        data = EventCheckinSessionSerializer(session).data
        return Response(data)

    @action(
        detail=True,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path=r"checkin/sessions/(?P<session_id>[^/.]+)",
    )
    def delete_checkin_session(
        self, request, public_id=None, session_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        is_event_admin = (
            getattr(user, "member", None)
            and event.admins.filter(pk=user.member.id).exists()
        )
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        if not (is_event_admin or is_site_admin):
            return Response(envelope_error(403, "无权限删除签到实例", {}), status=403)
        if not session_id:
            return Response(envelope_error(422, "需要提供签到实例ID", {}), status=422)
        try:
            session = event.checkin_sessions.get(pk=int(session_id))
        except Exception:
            return Response(envelope_error(404, "签到实例不存在", {}), status=404)
        session.delete()
        return Response(status=204)

    # =====================
    # =====================

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="assignments",
    )
    def list_assignments(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        member = getattr(user, "member", None)
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                member
                and (
                    event.participants.filter(pk=member.id).exists()
                    or event.admins.filter(pk=member.id).exists()
                )
            )
        ):
            return Response(envelope_error(403, "无权限查看作业", {}), status=403)
        qs = event.assignments.all().order_by("-created_at")
        results = AssignmentSerializer(qs, many=True, context={"request": request}).data
        submitted_map: dict[str, bool] = {}
        if member:
            submitted_public_ids = set(
                AssignmentSubmission.objects.filter(
                    assignment__event=event, member=member
                ).values_list("assignment__public_id", flat=True)
            )
            submitted_map = {str(pid): True for pid in submitted_public_ids}
        for item in results:
            try:
                pid = str(item.get("id") or "")
                item["my_submitted"] = bool(submitted_map.get(pid, False))
            except Exception:
                item["my_submitted"] = False
        if member:
            my_comments = {
                str(a_pid): c
                for a_pid, c in AssignmentSubmission.objects.filter(
                    assignment__event=event, member=member
                ).values_list("assignment__public_id", "graded_comment")
            }
            my_graded = {
                str(a_pid): (c.strip() != "" or (s or "").strip() != "")
                for a_pid, s, c in AssignmentSubmission.objects.filter(
                    assignment__event=event, member=member
                ).values_list("assignment__public_id", "graded_score", "graded_comment")
            }
            for item in results:
                try:
                    pid = str(item.get("id") or "")
                    item["my_graded_comment"] = my_comments.get(pid, "")
                    item["my_graded"] = bool(my_graded.get(pid, False))
                except Exception:
                    item["my_graded_comment"] = ""
                    item["my_graded"] = False
        return Response({"results": results, "count": qs.count()})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="assignments/create",
    )
    def create_assignment(self, request, public_id=None):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限创建作业", {}), status=403)
        payload = request.data.copy()
        payload["event"] = event.id
        serializer = AssignmentSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save(created_by=user)
        return Response(AssignmentSerializer(assignment).data, status=201)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)",
    )
    def assignment_detail(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        member = getattr(user, "member", None)
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                member
                and (
                    event.participants.filter(pk=member.id).exists()
                    or event.admins.filter(pk=member.id).exists()
                )
            )
        ):
            return Response(envelope_error(403, "无权限查看作业详情", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        data = AssignmentSerializer(assignment, context={"request": request}).data
        if member:
            data["my_submitted"] = AssignmentSubmission.objects.filter(
                assignment=assignment, member=member
            ).exists()
        else:
            data["my_submitted"] = False
        return Response(data)

    @action(
        detail=True,
        methods=["put", "patch"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/edit",
    )
    def update_assignment(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限编辑作业", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        payload = request.data.copy()
        if "event" not in payload:
            payload["event"] = event.id
        serializer = AssignmentSerializer(assignment, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/delete",
    )
    def delete_assignment(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限删除作业", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        assignment.delete()
        return Response(status=204)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/attachments",
    )
    def upload_assignment_attachment(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限上传作业附件", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        files = list(request.FILES.getlist("files") or [])
        single = request.FILES.get("file")
        if single:
            files.append(single)
        if not files:
            return Response(envelope_error(422, "需要提供文件", {}), status=422)
        replace_flag = str(request.data.get("replace", "")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if replace_flag:
            assignment.attachments.all().delete()
        created = [
            AssignmentAttachment.objects.create(assignment=assignment, file=f)
            for f in files
        ]
        data = AssignmentAttachmentSerializer(
            created, many=True, context={"request": request}
        ).data
        return Response({"results": data, "count": len(created)}, status=201)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/submit",
    )
    def submit_assignment(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        member = getattr(user, "member", None)
        if not member or (
            not event.participants.filter(pk=member.id).exists()
            and not event.admins.filter(pk=member.id).exists()
        ):
            return Response(envelope_error(403, "仅活动成员可提交作业", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        if assignment.is_past_deadline or assignment.is_closed:
            return Response(envelope_error(403, "作业已截止，无法提交", {}), status=403)
        text = str(request.data.get("text", "")).strip()
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment, member=member, defaults={"text": text}
        )
        if not created:
            submission.text = text
            submission.submitted_at = timezone.now()
            submission.save(update_fields=["text", "submitted_at"])
        files = request.FILES.getlist("files") or []
        replace_flag = str(request.data.get("replace", "")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not created and replace_flag:
            submission.attachments.all().delete()
        created_attachments = []
        for f in files:
            att = AssignmentSubmissionAttachment.objects.create(
                submission=submission, file=f
            )
            created_attachments.append(att)
        data = AssignmentSubmissionSerializer(
            submission, context={"request": request}
        ).data
        return Response(data, status=201 if created else 200)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/submissions",
    )
    def list_submissions(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        is_event_admin = (
            getattr(user, "member", None)
            and event.admins.filter(pk=user.member.id).exists()
        )
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        if not (is_event_admin or is_site_admin):
            member = getattr(user, "member", None)
            if not member:
                return Response(envelope_error(403, "无权限查看提交", {}), status=403)
            qs = AssignmentSubmission.objects.filter(
                assignment=assignment, member=member
            )
        else:
            include_all = str(request.query_params.get("include_all", "")).lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            only_submitted = str(
                request.query_params.get("only_submitted", "")
            ).lower() in {"1", "true", "yes", "on"}

            name = request.query_params.get("name")
            user_id = request.query_params.get("user_id")
            voice_part = request.query_params.get("voice_part")

            if include_all:
                members_qs = (
                    Member.objects.filter(Q(events=event) | Q(managed_events=event))
                    .select_related("user")
                    .distinct()
                )
                if name:
                    members_qs = members_qs.filter(name__icontains=name)
                if user_id:
                    members_qs = members_qs.filter(user__user_id__icontains=user_id)
                if voice_part:
                    members_qs = members_qs.filter(voice_part=voice_part)

                subs_qs = AssignmentSubmission.objects.filter(
                    assignment=assignment, member__in=members_qs
                )
                subs_map = {int(s.member_id): s for s in subs_qs}

                if only_submitted:
                    members_qs = members_qs.filter(id__in=list(subs_map.keys()))

                page = int(request.query_params.get("page", 1))
                page_size = int(request.query_params.get("page_size", 20))
                start = (page - 1) * page_size
                end = start + page_size
                ordered_members = sort_members(members_qs)
                total = len(ordered_members)
                paged_members = ordered_members[start:end]

                results: list[dict] = []
                serializer_context = {"request": request}
                for m in paged_members:
                    sub = subs_map.get(int(m.id))
                    if sub is not None:
                        results.append(
                            AssignmentSubmissionSerializer(
                                sub, context=serializer_context
                            ).data
                        )
                    else:
                        results.append(
                            {
                                "id": None,
                                "assignment": int(assignment.id),
                                "member": int(m.id),
                                "member_name": getattr(m, "name", ""),
                                "member_user_id": getattr(
                                    getattr(m, "user", None), "user_id", ""
                                ),
                                "voice_part": getattr(m, "voice_part", ""),
                                "tier": getattr(m, "tier", ""),
                                "text": "",
                                "submitted_at": None,
                                "graded_score": None,
                                "graded_comment": "",
                                "graded_by": None,
                                "graded_by_name": "",
                                "graded_by_user_id": "",
                                "graded_at": None,
                                "attachments": [],
                            }
                        )
                return Response({"count": total, "results": results})
            else:
                qs = AssignmentSubmission.objects.filter(assignment=assignment)
                if name:
                    qs = qs.filter(member__name__icontains=name)
                if user_id:
                    qs = qs.filter(member__user__user_id__icontains=user_id)
                if voice_part:
                    qs = qs.filter(member__voice_part=voice_part)
                page = int(request.query_params.get("page", 1))
                page_size = int(request.query_params.get("page_size", 20))
                start = (page - 1) * page_size
                end = start + page_size
                total = qs.count()
                items = qs.order_by("-submitted_at")[start:end]
                data = AssignmentSubmissionSerializer(
                    items, many=True, context={"request": request}
                ).data
                return Response({"count": total, "results": data})

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        items = qs.order_by("-submitted_at")[start:end]
        data = AssignmentSubmissionSerializer(
            items, many=True, context={"request": request}
        ).data
        return Response({"count": total, "results": data})

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/my-submission",
    )
    def my_submission(self, request, public_id=None, assignment_id: str | None = None):
        event: Event = self.get_object()
        user = request.user
        member = getattr(user, "member", None)
        if not member:
            return Response(envelope_error(403, "仅队员可查看提交", {}), status=403)
        if not (
            event.participants.filter(pk=member.id).exists()
            or event.admins.filter(pk=member.id).exists()
        ):
            return Response(envelope_error(403, "无权限查看提交", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment, member=member
        ).first()
        data = (
            AssignmentSubmissionSerializer(
                submission, context={"request": request}
            ).data
            if submission
            else None
        )
        return Response({"submission": data})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/grade",
    )
    def grade_submission(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        event: Event = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限批改作业", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response(envelope_error(422, "需要提供提交ID", {}), status=422)
        try:
            submission = assignment.submissions.get(pk=int(submission_id))
        except Exception:
            return Response(envelope_error(404, "提交不存在", {}), status=404)
        score = request.data.get("graded_score")
        comment = request.data.get("graded_comment", "")
        submission.graded_by = user
        submission.graded_comment = str(comment)
        submission.graded_score = "" if score is None else str(score)
        submission.graded_at = timezone.now()
        submission.save(
            update_fields=["graded_by", "graded_comment", "graded_score", "graded_at"]
        )
        return Response(
            AssignmentSubmissionSerializer(
                submission, context={"request": request}
            ).data
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/submissions/export",
    )
    def export_submissions(
        self, request, public_id=None, assignment_id: str | None = None
    ):
        """
        Initiate async export of assignment submissions as XLSX.
        Returns task_id for polling status.
        """
        event: Event = self.get_object()
        user = request.user

        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限导出作业成绩", {}), status=403)
        try:
            assignment = event.assignments.get(public_id=str(assignment_id))
        except Exception:
            return Response(envelope_error(404, "作业不存在", {}), status=404)

        filter_params = {
            "name": request.data.get("name") or request.query_params.get("name"),
            "user_id": request.data.get("user_id")
            or request.query_params.get("user_id"),
            "voice_part": request.data.get("voice_part")
            or request.query_params.get("voice_part"),
            "only_submitted": str(
                request.data.get("only_submitted")
                or request.query_params.get("only_submitted", "")
            ).lower()
            in {"1", "true", "yes", "on"},
        }

        import uuid

        from .models import AssignmentExportTask
        from .tasks import generate_assignment_export_task

        task_id = str(uuid.uuid4())
        task = AssignmentExportTask.objects.create(
            task_id=task_id,
            assignment=assignment,
            user=user,
            filter_params=filter_params,
            status="PENDING",
        )

        generate_assignment_export_task.delay(
            task_id=task_id,
            assignment_id=assignment.id,
            filter_params=filter_params,
        )

        from .serializers import AssignmentExportTaskSerializer

        serializer = AssignmentExportTaskSerializer(task)
        return Response(
            {"task_id": task_id, **serializer.data},
            status=202,
        )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path=r"assignments/(?P<assignment_id>a[0-9a-z]+)/export-task/(?P<task_id>[^/.]+)",
    )
    def export_task(
        self, request, public_id=None, assignment_id: str | None = None, task_id=None
    ):
        """
        Get export task status or download result if completed.
        Returns JSON for pending/processing/failed status, file for completed.
        """
        from .models import AssignmentExportTask
        from .serializers import AssignmentExportTaskSerializer

        event: Event = self.get_object()
        user = request.user

        if not (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            or (
                getattr(user, "member", None)
                and event.admins.filter(pk=user.member.id).exists()
            )
        ):
            return Response(envelope_error(403, "无权限查看导出任务", {}), status=403)

        try:
            task = AssignmentExportTask.objects.get(task_id=task_id, user=user)
        except AssignmentExportTask.DoesNotExist:
            return Response(envelope_error(404, "导出任务不存在", {}), status=404)

        if task.expires_at < timezone.now():
            return Response(
                envelope_error(410, "导出任务已过期，请重新发起导出", {}), status=410
            )

        if task.status == "COMPLETED" and task.result_file:
            try:
                response = FileResponse(
                    task.result_file.open("rb"),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                filename = os.path.basename(task.result_file.name)
                response["Content-Disposition"] = (
                    f'attachment; filename="{smart_str(filename)}"'
                )
                return response
            except Exception as e:
                return Response(
                    envelope_error(500, f"导出文件读取失败{task_id}: {e}", {}),
                    status=500,
                )

        serializer = AssignmentExportTaskSerializer(task)
        return Response(serializer.data, status=200)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="sheets",
    )
    def list_sheets(self, request, public_id=None):
        """列出显式关联该活动且当前用户可访问的乐谱。

        - 管理员可查看关联该活动的全部乐谱
        - 成员仅可查看对自己可见的乐谱
        - 匿名用户由 IsAuthenticated 拦截
        """
        event: Event = self.get_object()
        user = request.user
        qs = Sheet.objects.filter(visible_events=event).distinct()
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        if not is_site_admin:
            member = getattr(user, "member", None)
            if member:
                member_status = getattr(member, "status", MemberStatus.ACTIVE)
                if member_status == MemberStatus.ALUMNI:
                    if event.visible_to_alumni:
                        qs = qs.filter(
                            Q(visible_to_alumni=True)
                            | Q(visible_members=member)
                            | Q(visible_events__visible_to_alumni=True)
                        ).distinct()
                    else:
                        qs = qs.filter(
                            Q(visible_to_alumni=True) | Q(visible_members=member)
                        ).distinct()
                elif member_status == MemberStatus.INACTIVE:
                    qs = qs.none()
                else:
                    qs = qs.filter(
                        Q(visible_to_all=True) | Q(visible_members=member)
                    ).distinct()
            else:
                qs = qs.filter(visible_to_all=True)
        title = request.query_params.get("title")
        composer = request.query_params.get("composer")
        if title:
            qs = qs.filter(title__icontains=title)
        if composer:
            qs = qs.filter(composer__icontains=composer)
        items = sort_sheets(qs)
        total = len(items)
        if "page" in request.query_params or "page_size" in request.query_params:
            page = max(int(request.query_params.get("page", 1)), 1)
            page_size = max(int(request.query_params.get("page_size", 20)), 1)
            start = (page - 1) * page_size
            items = items[start : start + page_size]
        data = SheetSerializer(items, many=True, context={"request": request}).data
        return Response({"results": data, "count": total})

    # =====================
    # =====================
    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="admin-detail",
    )
    def admin_detail(self, request, public_id=None):
        """为站点管理员或活动管理员返回可编辑的完整活动数据。"""
        event: Event = self.get_object()
        user = request.user
        is_event_admin = (
            getattr(user, "member", None)
            and event.admins.filter(pk=user.member.id).exists()
        )
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in ("Admin", "SuperAdmin")
        if not (is_event_admin or is_site_admin):
            return Response(envelope_error(403, "无权限查看详细信息", {}), status=403)
        serializer = EventSerializer(event, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="admins",
    )
    def list_admins(self, request, public_id=None):
        """列出活动管理员，支持分页和筛选。"""
        from .serializers import MemberBriefSerializer

        event: Event = self.get_object()
        user = request.user
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in (
            "Admin",
            "SuperAdmin",
        )
        member = getattr(user, "member", None)
        is_event_member = bool(
            member
            and (
                event.participants.filter(pk=member.id).exists()
                or event.admins.filter(pk=member.id).exists()
            )
        )
        if not (is_site_admin or is_event_member):
            return Response(envelope_error(403, "无权限查看管理员列表", {}), status=403)
        qs = event.admins.select_related("user").all()
        name = request.query_params.get("name")
        user_id = request.query_params.get("user_id")
        voice_part = request.query_params.get("voice_part")
        if name:
            qs = qs.filter(name__icontains=name)
        if user_id:
            qs = qs.filter(user__user_id__icontains=user_id)
        if voice_part:
            qs = qs.filter(voice_part=voice_part)
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start = (page - 1) * page_size
        end = start + page_size
        ordered_items = sort_members(qs)
        total = len(ordered_items)
        items = ordered_items[start:end]
        data = MemberBriefSerializer(
            items, many=True, context={"request": request}
        ).data
        return Response({"count": total, "results": data})

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="members",
    )
    def list_members(self, request, public_id=None):
        """列出活动参与成员，支持分页和筛选。"""
        from .serializers import MemberBriefSerializer

        event: Event = self.get_object()
        user = request.user
        is_site_admin = getattr(user, "is_staff", False) or getattr(
            user, "role", ""
        ) in (
            "Admin",
            "SuperAdmin",
        )
        member = getattr(user, "member", None)
        is_event_member = bool(
            member
            and (
                event.participants.filter(pk=member.id).exists()
                or event.admins.filter(pk=member.id).exists()
            )
        )
        if not (is_site_admin or is_event_member):
            return Response(envelope_error(403, "无权限查看成员列表", {}), status=403)
        qs = event.participants.select_related("user").all()
        name = request.query_params.get("name")
        user_id = request.query_params.get("user_id")
        voice_part = request.query_params.get("voice_part")
        if name:
            qs = qs.filter(name__icontains=name)
        if user_id:
            qs = qs.filter(user__user_id__icontains=user_id)
        if voice_part:
            qs = qs.filter(voice_part=voice_part)
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start = (page - 1) * page_size
        end = start + page_size
        ordered_items = sort_members(qs)
        total = len(ordered_items)
        items = ordered_items[start:end]
        data = MemberBriefSerializer(
            items, many=True, context={"request": request}
        ).data
        return Response({"count": total, "results": data})
