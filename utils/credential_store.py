"""Windows Credential Manager backed secret storage."""

from typing import Optional


class CredentialStoreError(RuntimeError):
    pass


class CredentialStore:
    """Store secrets in Windows Credential Manager via pywin32."""

    PREFIX = "ReportAssistant"

    @classmethod
    def _target(cls, name: str) -> str:
        return f"{cls.PREFIX}:{name}"

    @staticmethod
    def _load_win32cred():
        try:
            import win32cred
            return win32cred
        except ImportError as exc:
            raise CredentialStoreError("pywin32/win32cred不可用，无法安全保存凭据") from exc

    @classmethod
    def set_secret(cls, name: str, username: str, secret: str) -> None:
        if not secret:
            return
        win32cred = cls._load_win32cred()
        credential = {
            "Type": win32cred.CRED_TYPE_GENERIC,
            "TargetName": cls._target(name),
            "UserName": username or name,
            "CredentialBlob": secret,
            "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
        }
        win32cred.CredWrite(credential, 0)

    @classmethod
    def get_username(cls, name: str) -> str:
        win32cred = cls._load_win32cred()
        try:
            credential = win32cred.CredRead(cls._target(name), win32cred.CRED_TYPE_GENERIC)
        except Exception:
            return ""
        return str(credential.get("UserName", "") or "")

    @classmethod
    def get_secret(cls, name: str) -> str:
        win32cred = cls._load_win32cred()
        try:
            credential = win32cred.CredRead(cls._target(name), win32cred.CRED_TYPE_GENERIC)
        except Exception:
            return ""
        blob = credential.get("CredentialBlob", "")
        if isinstance(blob, bytes):
            return blob.decode("utf-16-le", errors="ignore").rstrip("\x00") or blob.decode("utf-8", errors="ignore")
        return str(blob or "")

    @classmethod
    def delete_secret(cls, name: str) -> None:
        win32cred = cls._load_win32cred()
        try:
            win32cred.CredDelete(cls._target(name), win32cred.CRED_TYPE_GENERIC, 0)
        except Exception:
            pass
