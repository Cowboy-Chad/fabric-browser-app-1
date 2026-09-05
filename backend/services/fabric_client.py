import asyncio
import shlex
from typing import Optional
from config import FABRIC_PATH, OPENROUTER_MODEL, OPENROUTER_VENDOR, DEFAULT_TEMPERATURE, YOUTUBE_COOKIES_BROWSER


def _build_ytdlp_args(youtube_cookies_browser: str) -> str:
    if youtube_cookies_browser:
        args = f"--sleep-requests 1 --sleep-interval 5 --max-sleep-interval 30 --cookies-from-browser {youtube_cookies_browser} --write-auto-subs --sub-langs en --sub-format vtt"
    else:
        args = "--sleep-requests 5 --sleep-interval 10 --max-sleep-interval 60 --write-auto-subs --sub-langs en --sub-format vtt"
    return args


def _build_cmd(pattern, youtube_url, spotify_url, scrape_url, model, vendor, temperature, additional_args):
    cmd = [FABRIC_PATH]
    if vendor:
        cmd.extend(["-V", vendor])
    cmd.extend(["-m", model])
    cmd.extend(["-t", str(temperature)])
    if pattern:
        cmd.extend(["-p", pattern])
    if youtube_url:
        cmd.extend(["-y", youtube_url])
        cmd.extend([f"--yt-dlp-args={_build_ytdlp_args(YOUTUBE_COOKIES_BROWSER)}"])
    elif spotify_url:
        cmd.extend(["--spotify", spotify_url])
    elif scrape_url:
        cmd.extend(["-u", scrape_url])
    if additional_args:
        cmd.extend(additional_args)
    return cmd


async def get_youtube_metadata(url: str) -> tuple[str, str, str, str, str, str, str]:
    try:
        cmd = ["yt-dlp"]
        if YOUTUBE_COOKIES_BROWSER:
            cmd.extend(["--sleep-requests", "1", "--sleep-interval", "5", "--max-sleep-interval", "30", "--cookies-from-browser", YOUTUBE_COOKIES_BROWSER])
        else:
            cmd.extend(["--sleep-requests", "5", "--sleep-interval", "10", "--max-sleep-interval", "60"])
        cmd.extend(["--print", "title", "--print", "view_count", "--print", "timestamp",
            "--print", "channel", "--print", "channel_url", "--print", "channel_follower_count",
            "--print", "duration_string", url])
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode("utf-8", errors="replace").strip().split("\n")
        title = lines[0] if len(lines) > 0 else ""
        view_count = lines[1] if len(lines) > 1 else ""
        timestamp = lines[2] if len(lines) > 2 else ""
        channel = lines[3] if len(lines) > 3 else ""
        channel_url = lines[4] if len(lines) > 4 else ""
        subs = lines[5] if len(lines) > 5 else ""
        duration = lines[6] if len(lines) > 6 else ""
        return title, view_count, timestamp, channel, channel_url, subs, duration
    except Exception:
        return "", "", "", "", "", "", ""


async def run_fabric(
    pattern: Optional[str] = None,
    input_text: Optional[str] = None,
    youtube_url: Optional[str] = None,
    spotify_url: Optional[str] = None,
    scrape_url: Optional[str] = None,
    model: str = OPENROUTER_MODEL,
    vendor: str = OPENROUTER_VENDOR,
    temperature: float = DEFAULT_TEMPERATURE,
    additional_args: Optional[list[str]] = None,
) -> tuple[str, str, str]:
    cmd = _build_cmd(pattern, youtube_url, spotify_url, scrape_url, model, vendor, temperature, additional_args)
    cmd_str = " ".join(shlex.quote(c) for c in cmd)

    if input_text:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input_text.encode("utf-8"))
    else:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

    out = stdout.decode("utf-8", errors="replace") if stdout else ""
    err = stderr.decode("utf-8", errors="replace") if stderr else ""

    return out.strip(), err.strip(), cmd_str


async def run_fabric_with_input(
    input_text: str,
    pattern: str,
    model: str = OPENROUTER_MODEL,
    vendor: str = OPENROUTER_VENDOR,
    temperature: float = DEFAULT_TEMPERATURE,
) -> tuple[str, str, str]:
    return await run_fabric(
        pattern=pattern, input_text=input_text,
        model=model, vendor=vendor, temperature=temperature,
    )