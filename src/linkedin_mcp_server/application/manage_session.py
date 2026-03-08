"""Manage browser session lifecycle."""

from linkedin_mcp_server.domain.models.responses import SessionStatus
from linkedin_mcp_server.ports.auth import AuthPort
from linkedin_mcp_server.ports.browser import BrowserPort


class ManageSessionUseCase:
    """Handles session lifecycle operations (login, logout, status, close)."""

    def __init__(self, browser: BrowserPort, auth: AuthPort):
        self._browser = browser
        self._auth = auth

    async def close_browser(self) -> SessionStatus:
        """Close the browser instance and release resources."""
        await self._browser.close()
        return SessionStatus(is_valid=False, message="Browser closed")

    async def check_status(self) -> SessionStatus:
        """Check the current session status with detailed information."""
        has_creds = self._auth.has_credentials()
        is_valid = await self._auth.is_authenticated() if has_creds else False
        browser_alive = self._browser.is_alive()

        if is_valid:
            message = "Authenticated"
        elif has_creds and browser_alive:
            message = "Session expired — re-authenticate with --login"
        elif has_creds:
            message = "Credentials exist but session not verified"
        else:
            message = "No credentials — authenticate with --login"

        return SessionStatus(
            is_valid=is_valid,
            profile_path=str(self._auth.get_profile_path()),
            message=message,
        )

    async def login(self, warm_up: bool = True) -> SessionStatus:
        """Interactively log in to LinkedIn."""
        success = await self._auth.login_interactive(warm_up=warm_up)
        return SessionStatus(
            is_valid=success,
            profile_path=str(self._auth.get_profile_path()),
            message="Login successful" if success else "Login failed",
        )

    def logout(self) -> SessionStatus:
        """Clear stored credentials."""
        success = self._auth.clear_credentials()
        return SessionStatus(
            is_valid=False,
            message="Credentials cleared" if success else "Failed to clear",
        )

    async def export_cookies(self) -> SessionStatus:
        """Export session cookies for portability."""
        success = await self._auth.export_cookies()
        return SessionStatus(
            is_valid=success,
            profile_path=str(self._auth.get_profile_path()),
            message="Cookies exported" if success else "Cookie export failed",
        )

    async def import_cookies(self) -> SessionStatus:
        """Import session cookies from portable file."""
        success = await self._auth.import_cookies()
        if success:
            # Verify the imported cookies work
            is_valid = await self._auth.is_authenticated()
            return SessionStatus(
                is_valid=is_valid,
                profile_path=str(self._auth.get_profile_path()),
                message=(
                    "Cookies imported and verified"
                    if is_valid
                    else "Cookies imported but session invalid"
                ),
            )
        return SessionStatus(
            is_valid=False,
            profile_path=str(self._auth.get_profile_path()),
            message="Cookie import failed",
        )
