import pyfiglet
from rich.padding import Padding
from rich.text import Text


app_logo = Padding(
    Text.from_markup(
        pyfiglet.figlet_format("nyp HMS", font="larry3d"), style="dodger_blue2"
    ),
    (0, 1),
)
