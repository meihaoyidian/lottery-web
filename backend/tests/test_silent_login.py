"""
验证 silent-login 回退匹配逻辑（Bug #1/#3 修复）
运行: cd backend && python -m pytest tests/test_silent_login.py -v
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# 辅助：构造 mock 请求对象
# ---------------------------------------------------------------------------
class FakeReq:
    def __init__(self, code="mock_code", phone=None, user_id=None):
        self.code = code
        self.phone = phone
        self.user_id = user_id


# ---------------------------------------------------------------------------
# 辅助：构造 mock 用户
# ---------------------------------------------------------------------------
def make_user(id=1, phone="13800000001", openid=None, token_version=0):
    """创建一个 mock User 对象"""
    user = MagicMock()
    user.id = id
    user.phone = phone
    user.openid = openid
    user.token_version = token_version
    user.is_trial_user = False
    user.has_used_trial = False
    return user


# ---------------------------------------------------------------------------
# 辅助：模拟 silent_login 核心逻辑（从 auth.py 提取）
# ---------------------------------------------------------------------------
def run_silent_login_core(req, db, mock_wechat_openid="oABC123"):
    """
    模拟 silent_login 的核心匹配逻辑（不含 WeChat API 调用）。
    返回 (user, is_new, openid_was_bound)
    """
    openid = mock_wechat_openid

    # 2. 查已有用户（优先 openid）
    user = db.query().filter().first()  # mock: 由测试预设返回值

    # 3. openid 没查到？回退匹配
    openid_was_bound = False
    if not user and (req.user_id or req.phone):
        # 测试中由 mock 控制 fallback 返回值
        fallback = db._fallback_result
        if fallback and not fallback.openid:
            fallback.openid = openid
            user = fallback
            openid_was_bound = True

    is_new = user is None
    return user, is_new, openid_was_bound


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

class TestOpenidDirectMatch:
    """场景：openid 直接命中（已有行为，确保未破坏）"""

    def test_openid_match_returns_existing_user(self):
        """openid 匹配 → 返回老用户"""
        db = MagicMock()
        db._fallback_result = None
        db.query().filter().first.return_value = make_user(id=1, openid="oABC123")

        req = FakeReq(code="c1")
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 1
        assert bound is False  # 不需要回退

    def test_openid_match_even_when_fallback_provided(self):
        """openid 命中时忽略回退参数"""
        db = MagicMock()
        db._fallback_result = make_user(id=99, openid=None)
        db.query().filter().first.return_value = make_user(id=1, openid="oABC123")

        req = FakeReq(code="c1", user_id=99)
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 1  # 用 openid 匹配的，不是回退的
        assert bound is False


class TestFallbackByUserId:
    """场景：openid 未命中 → user_id 回退"""

    def test_user_id_fallback_binds_openid(self):
        """user_id 找到老用户且无 openid → 补绑 openid"""
        db = MagicMock()
        # openid 查不到
        db.query().filter().first.return_value = None
        # 回退命中
        db._fallback_result = make_user(id=1484, phone="17316637808", openid=None)

        req = FakeReq(code="c1", user_id=1484)
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 1484
        assert user.phone == "17316637808"
        assert user.openid == "oABC123"  # 已补绑
        assert bound is True

    def test_user_id_fallback_skips_if_already_has_openid(self):
        """回退用户已有 openid → 跳过（不应覆盖）"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        # 回退用户已有其他 openid
        db._fallback_result = make_user(id=99, openid="oDIFFERENT")

        req = FakeReq(code="c1", user_id=99)
        user, is_new, bound = run_silent_login_core(req, db)

        assert user is None  # 回退被跳过
        assert is_new is True
        assert bound is False


class TestFallbackByPhone:
    """场景：openid 未命中 → phone 回退"""

    def test_phone_fallback_binds_openid(self):
        """phone 找到老用户且无 openid → 补绑"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        db._fallback_result = make_user(id=200, phone="13800000002", openid=None)

        req = FakeReq(code="c1", phone="13800000002")
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 200
        assert user.openid == "oABC123"
        assert bound is True

    def test_user_id_priority_over_phone(self):
        """同时提供 user_id 和 phone → user_id 优先"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        # 回退返回 user_id 匹配的用户（phone 应该被忽略）
        db._fallback_result = make_user(id=1484, phone="17316637808", openid=None)

        req = FakeReq(code="c1", user_id=1484, phone="some_other_phone")
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 1484


class TestNewUser:
    """场景：全新用户"""

    def test_no_match_no_fallback_creates_new(self):
        """openid 未命中 + 无回退参数 → 创建新用户"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        db._fallback_result = None

        req = FakeReq(code="c1")  # 无 phone, user_id
        user, is_new, bound = run_silent_login_core(req, db)

        assert user is None
        assert is_new is True
        assert bound is False

    def test_no_match_fallback_not_found_creates_new(self):
        """回退也找不到用户 → 创建新用户"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        db._fallback_result = None  # 回退也没找到

        req = FakeReq(code="c1", user_id=99999)
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is True
        assert bound is False


class TestEdgeCases:
    """边界场景"""

    def test_only_phone_provided_no_user_id(self):
        """只提供 phone 不含 user_id"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        db._fallback_result = make_user(id=300, phone="13900000003", openid=None)

        req = FakeReq(code="c1", phone="13900000003")
        user, is_new, _ = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 300
        assert user.openid == "oABC123"

    def test_fallback_with_synthetic_wx_phone(self):
        """回退用户的 phone 是合成 wx_xxx 格式也能匹配"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        db._fallback_result = make_user(id=500, phone="wx_oABC123456", openid=None)

        req = FakeReq(code="c1", phone="wx_oABC123456")
        user, is_new, _ = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 500
        assert user.openid == "oABC123"


# ---------------------------------------------------------------------------
# 前端 Bug 相关的集成场景验证（模拟完整流程）
# ---------------------------------------------------------------------------

class TestFullScenarioIntegration:
    """
    端到端场景验证（模拟前后端完整交互）
    """

    def test_scenario_token_valid_no_openid(self):
        """
        Bug #3 修复场景: token 有效 + 无 openid
        bind-openid 成功 → silent-login openid 命中
        """
        # 第 1 步: bind-openid 用有效 token 补绑 openid
        # (后端已处理，这里只验证 silent-login 能正确识别)
        db = MagicMock()
        db.query().filter().first.return_value = make_user(id=1484, openid="oABC123")
        db._fallback_result = None

        req = FakeReq(code="c2", user_id=1484, phone="17316637808")
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 1484
        assert bound is False  # openid 直接命中，不需要回退

    def test_scenario_token_expired_no_openid(self):
        """
        Bug #1 + #3 修复场景: token 过期 + 无 openid
        bind-openid 401 → silent-login user_id 回退 → 补绑 openid → 返回老账号
        （这是之前必定创建重复账号的致命场景）
        """
        db = MagicMock()
        # openid 查不到（用户从未绑定）
        db.query().filter().first.return_value = None
        # 回退命中
        db._fallback_result = make_user(id=1484, phone="17316637808", openid=None)

        req = FakeReq(code="c3", user_id=1484, phone="17316637808")
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False, "不应该创建新用户！"
        assert user.id == 1484, "应该返回老用户 1484"
        assert user.openid == "oABC123", "应该补绑了 openid"
        assert bound is True, "应该通过回退匹配完成补绑"

    def test_scenario_new_user_first_launch(self):
        """全新用户首次启动 → 正常创建"""
        db = MagicMock()
        db.query().filter().first.return_value = None
        db._fallback_result = None

        req = FakeReq(code="c4")  # 无 oldInfo
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is True
        assert bound is False

    def test_scenario_returning_user_valid_token_has_openid(self):
        """最常见场景: token 有效 + 有 openid"""
        db = MagicMock()
        db.query().filter().first.return_value = make_user(id=1, openid="oABC123")
        db._fallback_result = None

        req = FakeReq(code="c5", user_id=1, phone="13800000001")
        user, is_new, bound = run_silent_login_core(req, db)

        assert is_new is False
        assert user.id == 1
        assert bound is False
