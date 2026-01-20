from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from rich.console import Console

if TYPE_CHECKING:
    from app.core.app import App


class BasePage(ABC):
    """Base class for all pages in the application"""

    app: App
    console: Console

    def __init__(self, app: App):
        self.app: App = app
        self.console: Console = app.console

    @abstractmethod
    def run(self) -> Optional["BasePage"]:
        """
        Execute the page's logic and determine the next page to transition to.

        Returns:
            The next page to transition to, or None to exit the application.
        """
        pass

    # Convenience methods for common operations

    def display_user_header(self, app: App) -> None:
        """Display the application header. Only applicable if logged in."""
        if (
            not app.current_user
            or not app.current_person
            or not app.current_profile_type
        ):
            return
        c_user = app.current_user
        c_person = app.current_person
        username = c_user.username
        first_name = c_person.first_name
        last_name = c_person.last_name
        profile_type_name = app.current_profile_type.display
        self.console.print(
            f"[bold blue]NYP HMS[/] | User [italic]{username}[/] as {profile_type_name} | {first_name} {last_name}"
        )

    def clear(self):
        """Clear the console"""
        self.console.clear()

    def print(self, *args, **kwargs):
        """Print to console"""
        self.console.print(*args, **kwargs)

    def print_error(self, message: str):
        """Print an error message"""
        self.console.print(f"[red]Error: {message}[/]")

    def print_success(self, message: str):
        """Print a success message"""
        self.console.print(f"[green]{message}[/]")

    def print_warning(self, message: str):
        """Print a warning message"""
        self.console.print(f"[yellow]{message}[/]")
