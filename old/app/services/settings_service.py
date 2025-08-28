from app.schemas.settings import SettingsUpdate, DeleteAccountRequest
from app.repositories.user_repo import UserRepo
from app.services.auth_service import AuthService
from app.models.user import User

class SettingsService:
    def __init__(self, user_repo: UserRepo, auth_svc: AuthService):
        self.user_repo = user_repo
        self.auth_svc = auth_svc

    async def update_settings(self, user_id: int, payload: SettingsUpdate) -> tuple[User, bool, str]:
        user = await self.user_repo.by_id(user_id)
        if not user:
            raise ValueError("User not found")

        reauth_required = False
        new_hash = None

        # --- Username change (allowed standalone) ---
        if payload.username and payload.username != user.username:
            if await self.user_repo.username_exists(payload.username, exclude_user_id=user.id):
                raise ValueError("Username already taken")

        # --- Email change (requires password) ---
        if payload.email and payload.email != user.email:
            if not payload.old_password:
                raise ValueError("Current password required to change email")
            if not self.auth_svc.verify_password(payload.old_password, user.password_hash):
                raise ValueError("Current password incorrect")
            if await self.user_repo.email_exists(payload.email, exclude_user_id=user.id):
                raise ValueError("Email already in use")

        # --- Password change (requires password) ---
        if payload.new_password:
            if not payload.old_password:
                raise ValueError("Current password required to change password")
            if not self.auth_svc.verify_password(payload.old_password, user.password_hash):
                raise ValueError("Current password incorrect")
            new_hash = self.auth_svc.hash_password(payload.new_password)
            reauth_required = True

        # --- Apply updates ---
        updated = await self.user_repo.update_user(
            user,
            username=payload.username,
            email=payload.email,
            password_hash=new_hash,
        )

        msg = "Settings updated"
        if reauth_required:
            msg += " (please sign in again)"
        return updated, reauth_required, msg

    async def delete_account(self, user_id: int, payload: DeleteAccountRequest) -> str:
        user = await self.user_repo.by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not self.auth_svc.verify_password(payload.password, user.password_hash):
            raise ValueError("Password incorrect")

        await self.user_repo.delete_user(user)
        return "Account deleted successfully"
