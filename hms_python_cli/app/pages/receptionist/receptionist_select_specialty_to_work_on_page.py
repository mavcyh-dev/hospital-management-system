import math

from app.pages.core.base_page import BasePage
from app.ui.prompts import KeyAction, prompt_choice, prompt_continue_message
from rich.table import Table
from rich.text import Text


class ReceptionistSelectSpecialtyToWorkOnPage(BasePage):
    items_per_scroll: int = 10
    scroll_offset: int = 0
    max_scroll_offset: int

    def run(self) -> BasePage | None:
        from app.pages.receptionist.receptionist_select_from_appointment_requests_in_specialty_page import (
            ReceptionistSelectFromAppointmentRequestsInSpecialty,
        )

        with self.app.session_scope() as session:
            self.details = (
                self.app.repos.appointment_request.get_specialty_importance_details(
                    session
                )
            )
        self.max_scroll_offset = max(
            0, math.ceil(len(self.details) / self.items_per_scroll) - 1
        )

        while True:
            self.clear()
            self.display_user_header(self.app)

            if len(self.details) == 0:
                prompt_continue_message(self.console, "No specialties.")
                return

            self._display_all_specialties_pending_appointment_requests()

            visible, start_index = self._get_visible_window()

            choices = [
                (
                    specialty_id,
                    f"No. {start_index + idx + 1}: {self.app.lookup_cache.get_specialty_name(specialty_id)}",
                )
                for idx, (specialty_id, _, _, _) in enumerate(visible)
            ]

            self.selected_choice = prompt_choice(
                "Select specialty to work on",
                choices,
                exitable=True,
                clearable=False,
                scrollable=len(self.details) > self.items_per_scroll,
                show_frame=True,
            )

            if self.selected_choice == KeyAction.BACK:
                return
            elif self.selected_choice == KeyAction.LEFT:
                self.scroll_offset = (self.scroll_offset - 1) % (
                    self.max_scroll_offset + 1
                )
            elif self.selected_choice == KeyAction.RIGHT:
                self.scroll_offset = (self.scroll_offset + 1) % (
                    self.max_scroll_offset + 1
                )
            else:
                choice_id = self.selected_choice
                return ReceptionistSelectFromAppointmentRequestsInSpecialty(
                    self.app, choice_id
                )

    def _get_visible_window(self):
        start = self.scroll_offset * self.items_per_scroll
        end = start + self.items_per_scroll
        return self.details[start:end], start

    def _display_all_specialties_pending_appointment_requests(self):
        visible, start_index = self._get_visible_window()

        title = f"Pending Appointment Requests by Specialty ({start_index+1}-{start_index+len(visible)}/{len(self.details)})"
        table = Table(title=title, title_justify="left")
        table.add_column("No.")
        table.add_column("Specialty")
        table.add_column("Count")
        table.add_column("Earliest Datetime")

        for offset, (specialty_id, count, pref_dt, creation_dt) in enumerate(visible):
            global_index = start_index + offset
            name = self.app.lookup_cache.get_specialty_name(specialty_id)
            if pref_dt:
                dt = f"PREF {pref_dt.strftime("%Y-%m-%d %H:%M")}"
            else:
                dt = (
                    f"CREA {creation_dt.strftime("%Y-%m-%d %H:%M")}"
                    if creation_dt
                    else Text("[NA]", style="italic dim")
                )
            table.add_row(
                str(global_index + 1),
                name,
                str(count),
                dt,
            )

        self.print(table)
        self.print("")
