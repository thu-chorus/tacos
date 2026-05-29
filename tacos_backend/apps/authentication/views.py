from django.contrib.auth.models import update_last_login
from django.db.models import Prefetch
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.utils import envelope_error, envelope_ok
from apps.personnel.models import Member, MemberTitle
from apps.personnel.serializers import MemberSerializer

from .policies import user_is_first_login, user_needs_profile_setup
from .serializers import (
    ChangePasswordSerializer,
    FirstLoginSerializer,
    LoginSerializer,
    UpdateUserSerializer,
    UserSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request: Request) -> JsonResponse:
    serializer = LoginSerializer(data=request.data, context={"request": request})

    # 手动处理验证错误以提供更好的错误响应
    if not serializer.is_valid():
        errors = serializer.errors
        # 检查是否有字段级别的错误
        if "user_id" in errors:
            return JsonResponse(
                envelope_error(
                    400, errors["user_id"][0], {"user_id": errors["user_id"]}
                ),
                status=400,
            )
        elif "password" in errors:
            return JsonResponse(
                envelope_error(
                    400, errors["password"][0], {"password": errors["password"]}
                ),
                status=400,
            )
        elif "non_field_errors" in errors:
            return JsonResponse(
                envelope_error(400, errors["non_field_errors"][0]), status=400
            )
        else:
            # 其他验证错误
            error_messages = []
            for field, field_errors in errors.items():
                if isinstance(field_errors, list):
                    error_messages.extend(field_errors)
                else:
                    error_messages.append(str(field_errors))
            message = (
                "; ".join(error_messages) if error_messages else "登录信息验证失败"
            )
            return JsonResponse(envelope_error(400, message, errors), status=400)

    user = serializer.validated_data["user"]

    # 首次登录和档案补全都在前端强制跳转到 /first-login。
    is_first_login = user_is_first_login(user)
    needs_profile_setup = user_needs_profile_setup(user)

    update_last_login(None, user)

    refresh = RefreshToken.for_user(user)
    data = {
        "token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user": UserSerializer(user).data,
        "is_first_login": is_first_login,
        "needs_profile_setup": needs_profile_setup,
    }
    return JsonResponse(envelope_ok(data), status=200)


class RefreshJWTView(TokenRefreshView):
    permission_classes = [AllowAny]

    def finalize_response(self, request, response, *args, **kwargs):  # type: ignore[override]
        if hasattr(response, "data") and isinstance(response.data, dict):
            data = {}
            if "access" in response.data:
                data["token"] = response.data.get("access")
            # 如果启用了 ROTATE_REFRESH_TOKENS，SimpleJWT 会返回新的 refresh token
            if "refresh" in response.data:
                data["refresh"] = response.data.get("refresh")
            if not data:
                data = response.data
            response.data = envelope_ok(data)
        return super().finalize_response(request, response, *args, **kwargs)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request: Request) -> JsonResponse:
    return JsonResponse(envelope_ok(UserSerializer(request.user).data), status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request: Request) -> JsonResponse:
    return JsonResponse(envelope_ok(message="登出成功"), status=200)


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request: Request) -> JsonResponse:
    if request.method == "GET":
        # 返回 user + member 聚合信息
        member = (
            Member.objects.select_related("user", "alumni_profile")
            .prefetch_related(
                Prefetch(
                    "member_titles",
                    queryset=MemberTitle.objects.select_related("title").order_by(
                        "-awarded_at"
                    ),
                    to_attr="prefetched_member_titles",
                )
            )
            .filter(user=request.user)
            .first()
        )
        data = {
            "user": UserSerializer(request.user).data,
            "member": (
                MemberSerializer(member, context={"request": request}).data
                if member
                else {}
            ),
        }
        return JsonResponse(envelope_ok(data), status=200)

    # PUT：允许更新 User.name 与 Member 非敏感字段
    user_data = {}
    if "name" in request.data:
        user_data["name"] = request.data.get("name")

    member = getattr(request.user, "member", None)
    if member is None:
        # 如果没有成员档案，创建一个空白档案（需要最基本字段：与 User 绑定，其他用默认）
        member = Member.objects.create(
            user=request.user,
            name=request.data.get("name", getattr(request.user, "name", "")) or "",
            gender=request.data.get("gender", "男"),
            voice_part=request.data.get("voice_part", "Other"),
            department=request.data.get("department", ""),
            class_name=request.data.get("class_name", ""),
            phone_number=request.data.get("phone_number", "00000000000"),
            email=request.data.get("email", ""),
            dorm=request.data.get("dorm", ""),
            birthday=request.data.get("birthday", "2000-01-01"),
            hometown=request.data.get("hometown", ""),
            ethnicity=request.data.get("ethnicity", ""),
            political_status=request.data.get("political_status", ""),
            political_affiliation=request.data.get("political_affiliation", ""),
            is_specialty=bool(request.data.get("is_specialty", False)),
            is_centralized=bool(request.data.get("is_centralized", False)),
            position=request.data.get("position", ""),
            join_month=request.data.get("join_month", ""),
            graduate_month=request.data.get("graduate_month", ""),
            tier=request.data.get("tier", "二队"),
            portfolio=request.data.get("portfolio", ""),
        )

    # 过滤出可更新的 Member 字段
    member_fields = set(
        MemberSerializer(context={"request": request}).get_fields().keys()
    ) - {"user_id", "created_at", "updated_at"}
    member_data = {k: v for k, v in request.data.items() if k in member_fields}

    # 验证并保存
    if user_data:
        u = UpdateUserSerializer(instance=request.user, data=user_data, partial=True)
        u.is_valid(raise_exception=True)
        u.save()

    if member_data:
        m = MemberSerializer(
            instance=member,
            data=member_data,
            partial=True,
            context={"request": request},
        )
        m.is_valid(raise_exception=True)
        m.save()

    data = {
        "user": UserSerializer(request.user).data,
        "member": (
            MemberSerializer(member, context={"request": request}).data
            if member
            else {}
        ),
    }
    return JsonResponse(envelope_ok(data), status=200)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request: Request) -> JsonResponse:
    serializer = ChangePasswordSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    new_password = serializer.validated_data["new_password"]
    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])
    return JsonResponse(envelope_ok(message="密码修改成功"), status=200)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def first_login_setup(request: Request) -> JsonResponse:
    """首次登录信息完善，包括个人信息和密码修改"""
    serializer = FirstLoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)

    user = request.user
    validated_data = serializer.validated_data

    # 更新用户基本信息
    if "name" in validated_data:
        user.name = validated_data["name"]
        user.save(update_fields=["name"])

    # 修改密码（不需要验证旧密码）
    new_password = validated_data["new_password"]
    user.set_password(new_password)
    user.save(update_fields=["password"])

    # 创建或更新Member信息
    member = getattr(user, "member", None)
    if member is None:
        # 创建Member档案，包含所有字段
        member_data = {
            "user": user,
            "name": validated_data["name"],
            "gender": validated_data["gender"],
            "wechat_id": validated_data["wechat_id"],
            "voice_part": validated_data["voice_part"],
            "tier": validated_data["tier"],
            "department": validated_data["department"],
            "department_other": validated_data.get("department_other", ""),
            "class_name": validated_data["class_name"],
            "phone_number": validated_data["phone_number"],
            "email": validated_data["email"],
            "dorm": validated_data["dorm"],
            "birthday": validated_data["birthday"],
            "hometown": validated_data["hometown"],
            "ethnicity": validated_data["ethnicity"],
            "political_status": validated_data["political_status"],
            "political_affiliation": validated_data["political_affiliation"],
            "is_specialty": validated_data.get("is_specialty", False),
            "is_centralized": validated_data.get("is_centralized", False),
            "position": validated_data.get("position", ""),
            "join_month": validated_data["join_month"],
            "graduate_month": validated_data["graduate_month"],
            "portfolio": validated_data["portfolio"],
        }
        # 如果department是其他且有department_other，需要验证
        if member_data["department"] == "其他" and not member_data["department_other"]:
            return JsonResponse(
                envelope_error(400, '当选择"其他"时，必须填写具体院系'), status=400
            )

        member = Member.objects.create(**member_data)
    else:
        # 更新现有Member信息，包含所有字段
        member_fields = [
            "name",
            "gender",
            "wechat_id",
            "voice_part",
            "tier",
            "department",
            "department_other",
            "class_name",
            "phone_number",
            "email",
            "dorm",
            "birthday",
            "hometown",
            "ethnicity",
            "political_status",
            "political_affiliation",
            "is_specialty",
            "is_centralized",
            "position",
            "join_month",
            "graduate_month",
            "portfolio",
        ]
        for field in member_fields:
            if field in validated_data:
                setattr(member, field, validated_data[field])

        # 验证department和department_other的关系
        if member.department == "其他" and not member.department_other:
            return JsonResponse(
                envelope_error(400, '当选择"其他"时，必须填写具体院系'), status=400
            )

        member.save()

    # 返回更新后的用户信息
    data = {
        "user": UserSerializer(user).data,
        "member": MemberSerializer(member, context={"request": request}).data,
    }
    return JsonResponse(envelope_ok(data, message="信息设置完成"), status=200)
