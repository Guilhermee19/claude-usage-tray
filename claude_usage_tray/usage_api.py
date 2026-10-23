"""Leitura do uso do plano Claude via endpoint OAuth usado pelo /usage do Claude Code."""
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CREDENTIALS_PATH = Path(
    os.environ.get("CLAUDE_USAGE_CREDENTIALS", Path.home() / ".claude" / ".credentials.json")
)


class UsageError(Exception):
    """Erro base; `message` é exibido ao usuário."""


class NoCredentials(UsageError):
    pass


class TokenExpired(UsageError):
    pass


class RateLimited(UsageError):
    pass


class NetworkError(UsageError):
    pass


@dataclass
class Window:
    label: str
    subtitle: str
    percent: float
    resets_at: datetime | None


@dataclass
class Usage:
    session: Window | None
    weekly: Window | None
    weekly_models: list[Window] = field(default_factory=list)
    plan: str = ""
    fetched_at: datetime = field(default_factory=datetime.now)


def _read_credentials() -> dict:
    try:
        data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise NoCredentials("Credenciais não encontradas — faça login no Claude Code")
    except (OSError, json.JSONDecodeError) as exc:
        raise NoCredentials(f"Não deu pra ler as credenciais: {exc}")
    oauth = data.get("claudeAiOauth") or {}
    if not oauth.get("accessToken"):
        raise NoCredentials("Sem token OAuth — faça login no Claude Code")
    return oauth


def _parse_window(label: str, subtitle: str, raw: dict | None) -> Window | None:
    if not raw or raw.get("utilization") is None:
        return None
    resets = raw.get("resets_at")
    resets_at = datetime.fromisoformat(resets.replace("Z", "+00:00")).astimezone() if resets else None
    return Window(label, subtitle, float(raw["utilization"]), resets_at)


def fetch_usage() -> Usage:
    oauth = _read_credentials()
    expires_at = oauth.get("expiresAt")
    if expires_at and expires_at / 1000 < time.time():
        raise TokenExpired("Token expirado — abra o Claude Code")

    req = urllib.request.Request(
        USAGE_URL,
        headers={
            "Authorization": f"Bearer {oauth['accessToken']}",
            "anthropic-beta": "oauth-2025-04-20",
            "Content-Type": "application/json",
            "User-Agent": "claude-usage-tray/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise TokenExpired("Token inválido — abra o Claude Code")
        if exc.code == 429:
            raise RateLimited("Muitas requisições — tentando mais tarde")
        raise NetworkError(f"Erro HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise NetworkError(f"Sem conexão: {getattr(exc, 'reason', exc)}")

    models = [
        w
        for w in (
            _parse_window("Semanal — Opus", "Somente Opus", data.get("seven_day_opus")),
            _parse_window("Semanal — Sonnet", "Somente Sonnet", data.get("seven_day_sonnet")),
        )
        if w
    ]
    return Usage(
        session=_parse_window("Sessão", "Janela móvel de 5 horas", data.get("five_hour")),
        weekly=_parse_window("Semanal", "Todos os modelos", data.get("seven_day")),
        weekly_models=models,
        plan=str(oauth.get("subscriptionType") or "").capitalize(),
    )


STATUS_URL = "https://status.anthropic.com/api/v2/status.json"
STATUS_TEXT = {
    "none": "Todos os sistemas operacionais",
    "minor": "Instabilidade parcial",
    "major": "Instabilidade grave",
    "critical": "Serviço fora do ar",
}


@dataclass
class ServiceStatus:
    ok: bool
    text: str


def fetch_status() -> ServiceStatus | None:
    """Status público do Claude; falha silenciosa porque é só informativo."""
    req = urllib.request.Request(STATUS_URL, headers={"User-Agent": "claude-usage-tray/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            indicator = json.load(resp)["status"]["indicator"]
    except (OSError, ValueError, KeyError):
        return None
    return ServiceStatus(indicator == "none", STATUS_TEXT.get(indicator, "Status desconhecido"))


def format_reset(dt: datetime | None) -> str:
    if not dt:
        return ""
    now = datetime.now().astimezone()
    if dt.date() == now.date():
        return f"Reseta hoje às {dt:%H:%M}"
    days = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    return f"Reseta {days[dt.weekday()]} {dt:%d/%m} às {dt:%H:%M}"
