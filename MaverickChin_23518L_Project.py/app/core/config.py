from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    appointment_timeslot_min_interval_minutes: int = 10
    appointment_preferred_datetime_max_days_from_current: int = 180
    appointment_min_days_from_start_allow_cancel: int = 2


APP_CONFIG = AppConfig()
