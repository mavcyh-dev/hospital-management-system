from app.core.app import App
from app.ui.inputs.base_input import BaseInput
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.input_result import InputResult
from app.ui.utils import prompt_choice, prompt_text


class DoctorBySpecialtyInput(BaseInput):
    def __init__(self, app: App, label: str):
        super().__init__(app)

    def prompt(
        self, default: InputResult | None = None, consumed: InputResult | None = None
    ):
        """
        A doctor selector that accepts a specialty for filtering purposes.

        :param consumed: Consumes specialty_id.
        :type consumed: InputResult | None
        """

        if consumed is None:
            return InputResult(value=None)

        with self.app.session_scope() as session:
            doctors = self.app.repos.doctor_profile.list_by_specialty(
                session, consumed.value
            )

            if len(doctors) == 0:
                self.console.print(
                    f"No doctors found for specialty {consumed.display_value}."
                )
                input("Press ENTER to continue...")
                return InputResult(value=None)

            filter_items = []
            for doctor in doctors:
                person = doctor.profile.person
                first_name = person.first_name
                last_name = person.last_name
                full_name = f"{first_name} {last_name}"
                phone_number = doctor.office_phone_number

                filter_items.append(
                    FilterItem(value=doctor, filter_values=[full_name, phone_number])
                )

        filter_input = FilterInput(
            self.app, f"Doctors in {consumed.display_value}", filter_items
        )
        return filter_input.prompt()
