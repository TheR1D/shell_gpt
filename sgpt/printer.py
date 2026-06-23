import time
from abc import ABC, abstractmethod
from typing import Generator, Literal

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from typer import secho


DEFAULT_LIVE_REFRESH_INTERVAL = 0.5
VALID_VERTICAL_OVERFLOW = {"ellipsis", "visible", "crop"}


class Printer(ABC):
    console = Console()

    @abstractmethod
    def live_print(self, chunks: Generator[str, None, None]) -> str:
        pass

    @abstractmethod
    def static_print(self, text: str) -> str:
        pass

    def __call__(self, chunks: Generator[str, None, None], live: bool = True) -> str:
        if live:
            return self.live_print(chunks)
        with self.console.status("[bold green]Loading..."):
            full_completion = "".join(chunks)
        self.static_print(full_completion)
        return full_completion


class MarkdownPrinter(Printer):
    def __init__(
        self,
        theme: str,
        vertical_overflow: Literal["ellipsis", "visible", "crop"] = "visible",
        refresh_interval: float = DEFAULT_LIVE_REFRESH_INTERVAL,
    ) -> None:
        if vertical_overflow not in VALID_VERTICAL_OVERFLOW:
            raise ValueError(
                f"Invalid vertical_overflow: {vertical_overflow!r}. "
                f"Must be one of: {', '.join(sorted(VALID_VERTICAL_OVERFLOW))}"
            )
        if refresh_interval < 0:
            raise ValueError("refresh_interval must be greater than or equal to 0")
        self.console = Console()
        self.theme = theme
        self.vertical_overflow = vertical_overflow
        self.refresh_interval = refresh_interval

    def live_print(self, chunks: Generator[str, None, None]) -> str:
        full_completion = ""
        with Live(
            console=self.console,
            vertical_overflow=self.vertical_overflow,
            auto_refresh=False,
        ) as live:
            last_refresh = time.monotonic()
            for chunk in chunks:
                full_completion += chunk
                if (
                    self.refresh_interval == 0
                    or time.monotonic() - last_refresh >= self.refresh_interval
                ):
                    live.update(
                        Markdown(markup=full_completion, code_theme=self.theme),
                        refresh=True,
                    )
                    last_refresh = time.monotonic()

            # Ensure the complete output is always rendered when streaming finishes.
            live.update(
                Markdown(markup=full_completion, code_theme=self.theme),
                refresh=True,
            )

        return full_completion

    def static_print(self, text: str) -> str:
        markdown = Markdown(markup=text, code_theme=self.theme)
        self.console.print(markdown)
        return text


class TextPrinter(Printer):
    def __init__(self, color: str) -> None:
        self.color = color

    def live_print(self, chunks: Generator[str, None, None]) -> str:
        full_text = ""
        for chunk in chunks:
            full_text += chunk
            secho(chunk, fg=self.color, nl=False)
        else:
            print()  # Add new line after last chunk.
        return full_text

    def static_print(self, text: str) -> str:
        secho(text, fg=self.color)
        return text
