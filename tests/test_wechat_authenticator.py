from wechat_reader.browser.wechat_authenticator import WechatAuthenticator
from wechat_reader.browser.session_manager import SessionManager


def test_disallow_browser_login_returns_false_without_opening_browser() -> None:
    authenticator = WechatAuthenticator()

    authenticator.session_manager.is_session_valid = lambda: True
    authenticator._verify_session = lambda: False

    browser_login_called = False

    def fake_browser_login() -> bool:
        nonlocal browser_login_called
        browser_login_called = True
        return True

    authenticator._do_browser_login = fake_browser_login

    assert authenticator.ensure_authenticated(allow_browser_login=False) is False
    assert browser_login_called is False


def test_session_manager_uses_env_session_file(monkeypatch, tmp_path) -> None:
    session_file = tmp_path / "custom-session.json"

    monkeypatch.setenv("WECHAT_READER_SESSION_FILE", str(session_file))

    manager = SessionManager()

    assert manager.session_file == session_file
