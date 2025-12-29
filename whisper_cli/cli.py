"""Command-line interface for Whisper CLI."""

import sys
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from .audio_processor import AudioProcessor, AudioProcessorError
from .transcriber import WhisperTranscriber, TranscriberError


console = Console()


@click.command()
@click.argument('audio_file', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path (default: stdout)'
)
@click.option(
    '--device',
    type=click.Choice(['auto', 'cpu', 'cuda'], case_sensitive=False),
    default='auto',
    help='Device to use for inference (default: auto)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.version_option(version='1.0.0', prog_name='whisper-cli')
def main(audio_file, output, device, verbose):
    """
    Transcribe audio files using Whisper-large-v3.

    AUDIO_FILE: Path to the audio file to transcribe

    Supported formats: WAV, MP3, FLAC, M4A, OGG, OPUS, WEBM

    Examples:

        whisper-cli audio.wav

        whisper-cli audio.mp3 -o transcript.txt

        whisper-cli audio.wav --device cpu --verbose
    """
    try:
        # Validate audio file
        if verbose:
            console.print("[cyan]Validating audio file...[/cyan]")

        audio_path = AudioProcessor.validate_file(audio_file)

        if verbose:
            file_info = AudioProcessor.get_file_info(audio_path)
            console.print(f"[green]✓[/green] File: {file_info['name']}")
            console.print(f"[green]✓[/green] Size: {file_info['size_mb']} MB")
            console.print(f"[green]✓[/green] Format: {file_info['format']}")

        # Initialize transcriber
        transcriber = WhisperTranscriber(device=device, verbose=verbose)

        if verbose:
            device_info = transcriber.get_device_info()
            console.print(f"[cyan]Using device: {device_info['device']}[/cyan]")

        # Transcribe with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Transcribing audio...", total=None)

            try:
                transcription = transcriber.transcribe(audio_path)
            finally:
                progress.remove_task(task)

        # Output results
        if output:
            # Write to file
            output_path = Path(output)
            output_path.write_text(transcription, encoding='utf-8')
            console.print(f"[green]✓[/green] Transcription saved to: {output_path}")

            if verbose:
                console.print(f"\n[dim]Preview:[/dim]")
                preview = transcription[:200] + "..." if len(transcription) > 200 else transcription
                console.print(preview)
        else:
            # Print to stdout
            console.print("\n[bold]Transcription:[/bold]")
            console.print(transcription)

    except AudioProcessorError as e:
        console.print(f"[red]Error:[/red] {str(e)}", err=True)
        sys.exit(1)

    except TranscriberError as e:
        console.print(f"[red]Transcription Error:[/red] {str(e)}", err=True)
        sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)

    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {str(e)}", err=True)
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
