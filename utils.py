from rich.progress import Progress, SpinnerColumn, TextColumn


def loading_spinner(func):
    def wrapper(*args, **kwargs):
        if not kwargs.pop("spinner"):
            return func(*args, **kwargs)
        with Progress(
                SpinnerColumn(),
                TextColumn("[green]Requesting OpenAI..."),
                transient=True
        ) as progress:
            progress.add_task("request")
            return func(*args, **kwargs)
    return wrapper
