from app.core.app import App
from app.ui.inputs.base_input import BaseInput
from app.ui.inputs.filter_input import FilterInput, FilterItem, InputResult, KeyAction
from app.ui.prompts import prompt_continue_message


class DoctorBySpecialtyInput(BaseInput):
    def __init__(self, app: App):
        super().__init__(app)

    def prompt(
        self, default: InputResult | None = None, consumed: InputResult | None = None
    ) -> InputResult | KeyAction:
        """
        A doctor selector that accepts a specialty for filtering purposes.

        :param consumed: Consumes specialty_id.
        :type consumed: InputResult | None
        """

        if consumed is None:
            self.console.print("No specialty selected.")
            input("Press ENTER to continue...")
            return InputResult(value=None)

        with self.app.session_scope() as session:
            doctors = self.app.repos.doctor_profile.list_by_specialty(
                session, consumed.value
            )

            if len(doctors) == 0:
                prompt_continue_message(
                    self.console,
                    f"No doctors found for specialty {consumed.display_value}.",
                )
                return InputResult(value=None)

            filter_items: list[FilterItem] = []
            for doctor in doctors:
                doctor_profile_id = doctor.profile_id
                person = doctor.profile.person
                full_name = person.full_name
                phone_number = doctor.office_phone_number

                filter_items.append(
                    FilterItem(
                        value=doctor_profile_id, filter_values=[full_name, phone_number]
                    )
                )

            filter_items.sort(
                key=lambda item: item.filter_values[0] if item.filter_values[0] else ""
            )

        filter_input = FilterInput(
            self.app, f"Doctors in {consumed.display_value}", filter_items
        )
        return filter_input.prompt()
