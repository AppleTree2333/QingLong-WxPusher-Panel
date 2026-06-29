from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Sequence

import requests

WXPUSHER_API = "https://wxpusher.zjiecode.com/api/send/message"

CONTENT_TYPE_TEXT = 1
CONTENT_TYPE_HTML = 2
CONTENT_TYPE_MARKDOWN = 3

MAX_SUMMARY_LENGTH = 96
MAX_CONTENT_LENGTH = 12000
MAX_METRICS = 4
MAX_ITEMS = 18
MAX_TAGS_PER_ITEM = 4
MAX_LINES_PER_ITEM = 4
MAX_TASKS_PER_ITEM = 6
MAX_EXTRAS_PER_ITEM = 4
MAX_TITLE_LENGTH = 40
MAX_VALUE_LENGTH = 24
MAX_DESC_LENGTH = 120
MAX_META_LENGTH = 48
MAX_LINE_LENGTH = 72
MAX_TAG_LENGTH = 18
MAX_TASK_TITLE_LENGTH = 22
MAX_TASK_DETAIL_LENGTH = 42
MAX_EXTRA_LABEL_LENGTH = 18
MAX_EXTRA_VALUE_LENGTH = 24

_VALID_THEMES = {"light", "dark", "auto"}


@dataclass
class WxPusherConfig:
    app_token: str
    uids: list[str]


@dataclass
class PanelMetric:
    label: str
    value: str
    tone: str = "primary"


@dataclass
class PanelTag:
    text: str
    tone: str = "neutral"


@dataclass
class PanelTask:
    title: str
    status: str = "neutral"
    detail: str = ""
    value: str = ""


@dataclass
class PanelExtra:
    label: str
    value: str
    tone: str = "neutral"


@dataclass
class PanelItem:
    title: str
    value: str = ""
    desc: str = ""
    meta: str = ""
    status: str = "neutral"
    tags: list[PanelTag] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    tasks: list[PanelTask] = field(default_factory=list)
    extras: list[PanelExtra] = field(default_factory=list)


_TONE_STYLES = {
    "primary": {
        "accent": "var(--t-primary-ac)",
        "text": "var(--t-primary-tx)",
        "soft_bg": "var(--t-primary-bg)",
        "soft_text": "var(--t-primary-st)",
    },
    "success": {
        "accent": "var(--t-success-ac)",
        "text": "var(--t-success-tx)",
        "soft_bg": "var(--t-success-bg)",
        "soft_text": "var(--t-success-st)",
    },
    "warning": {
        "accent": "var(--t-warning-ac)",
        "text": "var(--t-warning-tx)",
        "soft_bg": "var(--t-warning-bg)",
        "soft_text": "var(--t-warning-st)",
    },
    "danger": {
        "accent": "var(--t-danger-ac)",
        "text": "var(--t-danger-tx)",
        "soft_bg": "var(--t-danger-bg)",
        "soft_text": "var(--t-danger-st)",
    },
    "neutral": {
        "accent": "var(--t-neutral-ac)",
        "text": "var(--t-neutral-tx)",
        "soft_bg": "var(--t-neutral-bg)",
        "soft_text": "var(--t-neutral-st)",
    },
}

_THEME_PALETTES = {
    "light": {
        "bg": "#f9fafb",
        "text": "#09090b",
        "muted": "#52525b",
        "subtle": "#a1a1aa",
        "surface": "#ffffff",
        "surface-soft": "#f4f4f5",
        "border": "#e4e4e7",
        "hero-bg": "linear-gradient(135deg, #18181b 0%, #27272a 100%)",
        "hero-text": "#ffffff",
        "hero-meta": "#a1a1aa",
        "hero-border": "rgba(255, 255, 255, 0.1)",
        "hero-shadow": "0 8px 20px -6px rgba(0, 0, 0, 0.15)",
        "card-shadow": "0 2px 8px -2px rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)",
        "metric-shadow": "0 1px 2px rgba(0, 0, 0, 0.02)",
        "t-primary-ac": "#3b82f6", "t-primary-tx": "#2563eb", "t-primary-bg": "#eff6ff", "t-primary-st": "#1d4ed8",
        "t-success-ac": "#10b981", "t-success-tx": "#059669", "t-success-bg": "#ecfdf5", "t-success-st": "#047857",
        "t-warning-ac": "#f59e0b", "t-warning-tx": "#d97706", "t-warning-bg": "#fffbeb", "t-warning-st": "#b45309",
        "t-danger-ac": "#ef4444", "t-danger-tx": "#dc2626", "t-danger-bg": "#fef2f2", "t-danger-st": "#b91c1c",
        "t-neutral-ac": "#71717a", "t-neutral-tx": "#52525b", "t-neutral-bg": "#f4f4f5", "t-neutral-st": "#3f3f46",
    },
    "dark": {
        "bg": "#09090b",
        "text": "#f4f4f5",
        "muted": "#a1a1aa",
        "subtle": "#52525b",
        "surface": "#18181b",
        "surface-soft": "#27272a",
        "border": "#27272a",
        "hero-bg": "linear-gradient(135deg, #1f1f22 0%, #18181b 100%)",
        "hero-text": "#ffffff",
        "hero-meta": "#a1a1aa",
        "hero-border": "rgba(255, 255, 255, 0.05)",
        "hero-shadow": "0 8px 20px -6px rgba(0, 0, 0, 0.5)",
        "card-shadow": "0 4px 12px rgba(0, 0, 0, 0.2)",
        "metric-shadow": "0 2px 8px rgba(0, 0, 0, 0.2)",
        "t-primary-ac": "#60a5fa", "t-primary-tx": "#93c5fd", "t-primary-bg": "rgba(59,130,246,0.15)", "t-primary-st": "#bfdbfe",
        "t-success-ac": "#34d399", "t-success-tx": "#6ee7b7", "t-success-bg": "rgba(16,185,129,0.15)", "t-success-st": "#a7f3d0",
        "t-warning-ac": "#fbbf24", "t-warning-tx": "#fcd34d", "t-warning-bg": "rgba(245,158,11,0.15)", "t-warning-st": "#fde68a",
        "t-danger-ac": "#f87171", "t-danger-tx": "#fca5a5", "t-danger-bg": "rgba(239,68,68,0.15)", "t-danger-st": "#fecaca",
        "t-neutral-ac": "#a1a1aa", "t-neutral-tx": "#d4d4d8", "t-neutral-bg": "rgba(113,113,122,0.15)", "t-neutral-st": "#e4e4e7",
    },
}


def load_wxpusher_config(
    app_token: str | None = None,
    uids: str | Sequence[str] | None = None,
) -> WxPusherConfig | None:
    app_token = (app_token or os.getenv("WXPUSHER_APP_TOKEN", "")).strip()
    uid_list = _normalize_uids(uids if uids is not None else os.getenv("WXPUSHER_UID", ""))
    if not app_token or not uid_list:
        return None
    return WxPusherConfig(app_token=app_token, uids=uid_list)


def send_wxpusher(
    summary: str,
    content: str,
    content_type: int = CONTENT_TYPE_HTML,
    app_token: str | None = None,
    uids: str | Sequence[str] | None = None,
    timeout: int = 15,
    verify_pay_type: int | None = 0,
    extra_payload: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    config = load_wxpusher_config(app_token=app_token, uids=uids)
    if not config:
        return False, {"msg": "missing WXPUSHER_APP_TOKEN or WXPUSHER_UID"}

    summary = _truncate_text(summary, MAX_SUMMARY_LENGTH)
    content = _prepare_content(content=content, content_type=content_type, max_length=MAX_CONTENT_LENGTH)

    payload: dict[str, Any] = {
        "appToken": config.app_token,
        "content": content,
        "summary": summary,
        "contentType": content_type,
        "uids": config.uids,
    }
    if verify_pay_type is not None:
        payload["verifyPayType"] = verify_pay_type
    if extra_payload:
        payload.update(extra_payload)

    try:
        response = requests.post(WXPUSHER_API, json=payload, timeout=timeout)
        try:
            data = response.json()
        except ValueError:
            data = {"msg": response.text, "status_code": response.status_code}

        ok = data.get("code") == 1000 or bool(data.get("success"))
        if ok:
            ok, record_errors = _validate_send_records(data)
            if record_errors:
                data["record_errors"] = record_errors
        if not ok and "status_code" not in data:
            data["status_code"] = response.status_code
        return ok, data
    except requests.RequestException as exc:
        return False, {"msg": str(exc)}


def build_html_panel(
    title: str,
    items: Sequence[PanelItem | dict[str, Any]],
    metrics: Sequence[PanelMetric | dict[str, Any]] | None = None,
    subtitle: str = "",
    footer: str = "",
    generated_at: str | None = None,
    theme: str = "auto",
) -> str:
    theme = _normalize_theme(theme)
    generated_at = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M")
    source_metrics = list(metrics or [])
    source_items = list(items)
    normalized_metrics = [_coerce_metric(metric) for metric in source_metrics[:MAX_METRICS]]
    normalized_items = [_coerce_item(item) for item in source_items[:MAX_ITEMS]]
    hidden_metrics = max(len(source_metrics) - len(normalized_metrics), 0)
    hidden_items = max(len(source_items) - len(normalized_items), 0)

    blocks = [
        _render_theme_style_block(),
        f'<div class="wxp-shell wxp-theme-{theme}">',
        _render_header(title=title, subtitle=subtitle, generated_at=generated_at),
    ]

    if normalized_metrics:
        blocks.append(_render_metrics(normalized_metrics))
        if hidden_metrics:
            blocks.append(_render_hint(f"其余 {hidden_metrics} 项指标已折叠"))

    for item in normalized_items:
        blocks.append(_render_item(item))

    footer_text = footer or (
        f"其余 {hidden_items} 个条目已折叠，请登录青龙查看完整日志" if hidden_items else ""
    )
    if footer_text:
        blocks.append(_render_footer(footer_text))

    blocks.append("</div>")
    return "".join(blocks)


def push_html_panel(
    summary: str,
    title: str,
    items: Sequence[PanelItem | dict[str, Any]],
    metrics: Sequence[PanelMetric | dict[str, Any]] | None = None,
    subtitle: str = "",
    footer: str = "",
    generated_at: str | None = None,
    app_token: str | None = None,
    uids: str | Sequence[str] | None = None,
    timeout: int = 15,
    verify_pay_type: int | None = 0,
    theme: str = "auto",
) -> tuple[bool, dict[str, Any], str]:
    html_content = build_html_panel(
        title=title,
        items=items,
        metrics=metrics,
        subtitle=subtitle,
        footer=footer,
        generated_at=generated_at,
        theme=theme,
    )
    ok, data = send_wxpusher(
        summary=summary,
        content=html_content,
        content_type=CONTENT_TYPE_HTML,
        app_token=app_token,
        uids=uids,
        timeout=timeout,
        verify_pay_type=verify_pay_type,
    )
    return ok, data, html_content


def build_example_panel(script_name: str = "QingLong Daily Report", theme: str = "auto") -> str:
    metrics = [
        PanelMetric(label="Success", value="5", tone="success"),
        PanelMetric(label="Skipped", value="2", tone="neutral"),
        PanelMetric(label="Failed", value="1", tone="danger"),
        PanelMetric(label="Accounts", value="8", tone="primary"),
    ]
    items = [
        PanelItem(
            title="account_a",
            value="+12",
            desc="Points increased and daily tasks completed.",
            meta="score 348 | latency 1.2s",
            status="success",
            extras=[PanelExtra("streak", "7d", "primary"), PanelExtra("balance", "348", "success")],
            tasks=[
                PanelTask("browse", "success", "community opened", "ok"),
                PanelTask("signin", "success", "reward received", "+12"),
            ],
            tags=[PanelTag("browse ok", "success"), PanelTag("signin ok", "success")],
        ),
        PanelItem(
            title="account_b",
            value="retry",
            desc="Cookie expired, task skipped to avoid noisy retries.",
            meta="needs relogin",
            status="warning",
            lines=["skip follow-up tasks", "keep previous score unchanged"],
            tasks=[PanelTask("signin", "danger", "cookie expired", "fail")],
            tags=[PanelTag("cookie expired", "warning")],
        ),
    ]
    return build_html_panel(
        title=script_name,
        subtitle="Compact status board",
        metrics=metrics,
        items=items,
        footer="Generated by wxpusher_utils.py",
        theme=theme,
    )


def _render_theme_style_block() -> str:
    light_vars = _theme_vars("light")
    dark_vars = _theme_vars("dark")
    return (
        "<style>"
        ".wxp-shell{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue',Arial,sans-serif;"
        "-webkit-font-smoothing:antialiased;max-width:420px;margin:0 auto;padding:16px 12px;"
        "background:var(--bg);color:var(--text);}"
        ".wxp-theme-light{" + light_vars + "}"
        ".wxp-theme-dark{" + dark_vars + "}"
        ".wxp-theme-auto{" + light_vars + "}"
        "@media (prefers-color-scheme: dark){.wxp-theme-auto{" + dark_vars + "}}"
        ".wxp-hero{border-radius:16px;padding:20px 20px 18px;background:var(--hero-bg);"
        "box-shadow:var(--hero-shadow);color:var(--hero-text);border:1px solid var(--hero-border);}"
        ".wxp-hero-title{font-size:20px;font-weight:700;letter-spacing:-0.5px;}"
        ".wxp-hero-meta{margin-top:8px;font-size:13px;color:var(--hero-meta);}"
        ".wxp-metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:16px;}"
        ".wxp-metric{background:var(--surface);border:1px solid var(--border);border-radius:12px;"
        "padding:14px 16px;box-shadow:var(--metric-shadow);}"
        ".wxp-metric-label{font-size:13px;font-weight:500;color:var(--muted);}"
        ".wxp-metric-value{margin-top:6px;font-size:24px;font-weight:700;letter-spacing:-0.5px;}"
        ".wxp-item{margin-top:12px;background:var(--surface);border:1px solid var(--border);"
        "border-radius:16px;padding:16px;box-shadow:var(--card-shadow);}"
        ".wxp-item-row{display:flex;justify-content:space-between;align-items:center;gap:12px;}"
        ".wxp-item-title{font-size:16px;font-weight:600;letter-spacing:-0.3px;color:var(--text);}"
        ".wxp-item-desc{margin-top:6px;font-size:14px;line-height:1.5;color:var(--muted);}"
        ".wxp-item-meta{margin-top:6px;font-size:12px;color:var(--subtle);}"
        ".wxp-value-pill{padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;letter-spacing:0.2px;}"
        ".wxp-section{margin-top:12px;padding-top:12px;border-top:1px solid var(--border);}"
        ".wxp-section-title{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;"
        "color:var(--subtle);margin-bottom:10px;}"
        ".wxp-line{display:flex;align-items:baseline;margin-top:6px;font-size:13px;line-height:1.5;color:var(--muted);}"
        ".wxp-line-dot{flex-shrink:0;width:6px;height:6px;border-radius:50%;margin-right:8px;transform:translateY(-1px);}"
        ".wxp-tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;}"
        ".wxp-tag{padding:4px 8px;border-radius:6px;font-size:12px;font-weight:500;}"
        ".wxp-task{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;"
        "border-radius:8px;background:var(--surface-soft);border:1px solid var(--border);margin-top:8px;}"
        ".wxp-task-title{font-size:13px;font-weight:600;color:var(--text);}"
        ".wxp-task-detail{margin-top:2px;font-size:12px;color:var(--muted);}"
        ".wxp-extra-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:10px;}"
        ".wxp-extra{padding:10px 12px;border-radius:8px;background:var(--surface-soft);border:1px solid var(--border);}"
        ".wxp-extra-label{font-size:12px;color:var(--subtle);}"
        ".wxp-extra-value{margin-top:4px;font-size:14px;font-weight:600;}"
        ".wxp-hint,.wxp-footer{margin-top:16px;text-align:center;font-size:12px;color:var(--subtle);}"
        "</style>"
    )


def _render_header(title: str, subtitle: str, generated_at: str) -> str:
    meta_parts = []
    if subtitle:
        meta_parts.append(_escape(subtitle))
    meta_parts.append(_escape(generated_at))
    return (
        '<div class="wxp-hero">'
        f'<div class="wxp-hero-title">{_escape(title)}</div>'
        f'<div class="wxp-hero-meta">{" | ".join(meta_parts)}</div>'
        "</div>"
    )


def _render_metrics(metrics: Sequence[PanelMetric]) -> str:
    blocks = ['<div class="wxp-metrics">']
    for metric in metrics:
        tone_style = _tone_style(metric.tone)
        blocks.append('<div class="wxp-metric">')
        blocks.append(f'<div class="wxp-metric-label">{_escape(metric.label)}</div>')
        blocks.append(
            f'<div class="wxp-metric-value" style="color:{tone_style["text"]};">'
            f'{_escape(metric.value)}</div>'
        )
        blocks.append("</div>")
    blocks.append("</div>")
    return "".join(blocks)


def _render_item(item: PanelItem) -> str:
    tone_style = _tone_style(item.status)
    blocks = ['<div class="wxp-item">', '<div class="wxp-item-row">']
    blocks.append(f'<div class="wxp-item-title">{_escape(item.title)}</div>')
    if item.value:
        blocks.append(
            f'<div class="wxp-value-pill" style="background:{tone_style["soft_bg"]};'
            f'color:{tone_style["soft_text"]};">{_escape(item.value)}</div>'
        )
    blocks.append("</div>")

    if item.desc:
        blocks.append(f'<div class="wxp-item-desc">{_escape(item.desc)}</div>')
    if item.meta:
        blocks.append(f'<div class="wxp-item-meta">{_escape(item.meta)}</div>')
    if item.extras:
        blocks.append(_render_extras(item.extras))
    if item.tasks:
        blocks.append(_render_tasks(item.tasks))
    if item.lines:
        blocks.append(_render_lines(item.lines, tone_style["accent"]))
    if item.tags:
        blocks.append(_render_tags(item.tags))

    blocks.append("</div>")
    return "".join(blocks)


def _render_extras(extras: Sequence[PanelExtra]) -> str:
    blocks = ['<div class="wxp-section"><div class="wxp-section-title">补充信息</div><div class="wxp-extra-grid">']
    for extra in extras:
        tone_style = _tone_style(extra.tone)
        blocks.append('<div class="wxp-extra">')
        blocks.append(f'<div class="wxp-extra-label">{_escape(extra.label)}</div>')
        blocks.append(
            f'<div class="wxp-extra-value" style="color:{tone_style["text"]};">{_escape(extra.value)}</div>'
        )
        blocks.append("</div>")
    blocks.append("</div></div>")
    return "".join(blocks)


def _render_tasks(tasks: Sequence[PanelTask]) -> str:
    blocks = ['<div class="wxp-section"><div class="wxp-section-title">任务明细</div>']
    for task in tasks:
        tone_style = _tone_style(task.status)
        blocks.append('<div class="wxp-task">')
        blocks.append('<div>')
        blocks.append(f'<div class="wxp-task-title">{_escape(task.title)}</div>')
        if task.detail:
            blocks.append(f'<div class="wxp-task-detail">{_escape(task.detail)}</div>')
        blocks.append("</div>")
        if task.value:
            blocks.append(
                f'<div class="wxp-value-pill" style="background:{tone_style["soft_bg"]};'
                f'color:{tone_style["soft_text"]};">{_escape(task.value)}</div>'
            )
        blocks.append("</div>")
    blocks.append("</div>")
    return "".join(blocks)


def _render_lines(lines: Sequence[str], accent_color: str) -> str:
    blocks = ['<div class="wxp-section"><div class="wxp-section-title">补充说明</div>']
    for line in lines:
        blocks.append(
            '<div class="wxp-line">'
            f'<span class="wxp-line-dot" style="background:{accent_color};"></span>'
            f"<span>{_escape(line)}</span>"
            "</div>"
        )
    blocks.append("</div>")
    return "".join(blocks)


def _render_tags(tags: Sequence[PanelTag]) -> str:
    blocks = ['<div class="wxp-tags">']
    for tag in tags:
        tone_style = _tone_style(tag.tone)
        blocks.append(
            f'<span class="wxp-tag" style="background:{tone_style["soft_bg"]};'
            f'color:{tone_style["soft_text"]};">{_escape(tag.text)}</span>'
        )
    blocks.append("</div>")
    return "".join(blocks)


def _render_hint(text: str) -> str:
    return f'<div class="wxp-hint">{_escape(text)}</div>'


def _render_footer(text: str) -> str:
    return f'<div class="wxp-footer">{_escape(text)}</div>'


def _normalize_uids(uids: str | Sequence[str] | None) -> list[str]:
    if uids is None:
        return []
    if isinstance(uids, str):
        return [item.strip() for item in uids.split(",") if item.strip()]

    result: list[str] = []
    for item in uids:
        value = _clean_str(item)
        if value:
            result.append(value)
    return result


def _coerce_metric(metric: PanelMetric | dict[str, Any]) -> PanelMetric:
    if isinstance(metric, PanelMetric):
        return PanelMetric(
            label=_clean_str(metric.label, "Metric", MAX_TITLE_LENGTH),
            value=_clean_str(metric.value, "-", MAX_VALUE_LENGTH),
            tone=_normalize_tone(metric.tone, "primary"),
        )
    return PanelMetric(
        label=_clean_str(metric.get("label"), "Metric", MAX_TITLE_LENGTH),
        value=_clean_str(metric.get("value"), "-", MAX_VALUE_LENGTH),
        tone=_normalize_tone(metric.get("tone"), "primary"),
    )


def _coerce_item(item: PanelItem | dict[str, Any]) -> PanelItem:
    if isinstance(item, PanelItem):
        return PanelItem(
            title=_clean_str(item.title, "Untitled", MAX_TITLE_LENGTH),
            value=_clean_str(item.value, "", MAX_VALUE_LENGTH),
            desc=_clean_str(item.desc, "", MAX_DESC_LENGTH),
            meta=_clean_str(item.meta, "", MAX_META_LENGTH),
            status=_normalize_tone(item.status, "neutral"),
            tags=[_coerce_tag(tag) for tag in item.tags[:MAX_TAGS_PER_ITEM]],
            lines=_normalize_lines(item.lines[:MAX_LINES_PER_ITEM]),
            tasks=[_coerce_task(task) for task in item.tasks[:MAX_TASKS_PER_ITEM]],
            extras=[_coerce_extra(extra) for extra in item.extras[:MAX_EXTRAS_PER_ITEM]],
        )

    tags = [_coerce_tag(tag) for tag in list(item.get("tags", []))[:MAX_TAGS_PER_ITEM]]
    lines = _normalize_lines(list(item.get("lines", []))[:MAX_LINES_PER_ITEM])
    tasks = [_coerce_task(task) for task in list(item.get("tasks", []))[:MAX_TASKS_PER_ITEM]]
    extras = [_coerce_extra(extra) for extra in list(item.get("extras", []))[:MAX_EXTRAS_PER_ITEM]]

    return PanelItem(
        title=_clean_str(item.get("title"), "Untitled", MAX_TITLE_LENGTH),
        value=_clean_str(item.get("value"), "", MAX_VALUE_LENGTH),
        desc=_clean_str(item.get("desc"), "", MAX_DESC_LENGTH),
        meta=_clean_str(item.get("meta"), "", MAX_META_LENGTH),
        status=_normalize_tone(item.get("status"), "neutral"),
        tags=tags,
        lines=lines,
        tasks=tasks,
        extras=extras,
    )


def _coerce_tag(tag: PanelTag | dict[str, Any] | str) -> PanelTag:
    if isinstance(tag, PanelTag):
        return PanelTag(
            text=_clean_str(tag.text, "", MAX_TAG_LENGTH),
            tone=_normalize_tone(tag.tone, "neutral"),
        )
    if isinstance(tag, str):
        return PanelTag(text=_clean_str(tag, "", MAX_TAG_LENGTH), tone="neutral")
    return PanelTag(
        text=_clean_str(tag.get("text"), "", MAX_TAG_LENGTH),
        tone=_normalize_tone(tag.get("tone"), "neutral"),
    )


def _coerce_task(task: PanelTask | dict[str, Any]) -> PanelTask:
    if isinstance(task, PanelTask):
        return PanelTask(
            title=_clean_str(task.title, "Task", MAX_TASK_TITLE_LENGTH),
            status=_normalize_tone(task.status, "neutral"),
            detail=_clean_str(task.detail, "", MAX_TASK_DETAIL_LENGTH),
            value=_clean_str(task.value, "", MAX_VALUE_LENGTH),
        )
    return PanelTask(
        title=_clean_str(task.get("title"), "Task", MAX_TASK_TITLE_LENGTH),
        status=_normalize_tone(task.get("status"), "neutral"),
        detail=_clean_str(task.get("detail"), "", MAX_TASK_DETAIL_LENGTH),
        value=_clean_str(task.get("value"), "", MAX_VALUE_LENGTH),
    )


def _coerce_extra(extra: PanelExtra | dict[str, Any]) -> PanelExtra:
    if isinstance(extra, PanelExtra):
        return PanelExtra(
            label=_clean_str(extra.label, "extra", MAX_EXTRA_LABEL_LENGTH),
            value=_clean_str(extra.value, "-", MAX_EXTRA_VALUE_LENGTH),
            tone=_normalize_tone(extra.tone, "neutral"),
        )
    return PanelExtra(
        label=_clean_str(extra.get("label"), "extra", MAX_EXTRA_LABEL_LENGTH),
        value=_clean_str(extra.get("value"), "-", MAX_EXTRA_VALUE_LENGTH),
        tone=_normalize_tone(extra.get("tone"), "neutral"),
    )


def _normalize_lines(lines: Iterable[Any]) -> list[str]:
    result: list[str] = []
    for line in lines:
        text = _clean_str(line, "", MAX_LINE_LENGTH)
        if text:
            result.append(text)
    return result


def _theme_vars(theme: str) -> str:
    palette = _THEME_PALETTES[theme]
    return "".join(f"--{key}:{value};" for key, value in palette.items())


def _normalize_theme(theme: Any) -> str:
    value = _clean_str(theme, "auto").lower()
    return value if value in _VALID_THEMES else "auto"


def _tone_style(tone: str) -> dict[str, str]:
    return _TONE_STYLES.get(tone, _TONE_STYLES["neutral"])


def _escape(text: Any) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def _clean_str(value: Any, default: str = "", max_length: int | None = None) -> str:
    if value is None:
        text = default
    else:
        text = str(value).strip()
        if not text:
            text = default
    if max_length is not None and len(text) > max_length:
        return _truncate_text(text, max_length)
    return text


def _truncate_text(text: Any, max_length: int) -> str:
    value = "" if text is None else str(text)
    if max_length <= 1 or len(value) <= max_length:
        return value[:max_length]
    return value[: max_length - 1] + "…"


def _normalize_tone(value: Any, default: str) -> str:
    tone = _clean_str(value, default)
    return tone if tone in _TONE_STYLES else default


def _prepare_content(content: str, content_type: int, max_length: int) -> str:
    if len(content) <= max_length:
        return content
    if content_type == CONTENT_TYPE_HTML:
        preview = _truncate_text(_strip_html(content), 280)
        return build_html_panel(
            title="消息过长，已自动折叠",
            subtitle="内容已降级为摘要预览",
            metrics=[PanelMetric("状态", "已折叠", "warning")],
            items=[
                PanelItem(
                    title="预览",
                    desc="本次推送内容超过安全长度限制，已自动降级。",
                    lines=[preview],
                    status="warning",
                )
            ],
            theme="auto",
        )
    return _truncate_text(content, max_length)


def _strip_html(content: str) -> str:
    text = re.sub(r"<[^>]+>", " ", content)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _validate_send_records(data: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    records = data.get("data")
    if not isinstance(records, list) or not records:
        return True, []

    record_errors: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("code") != 1000:
            record_errors.append(record)
    return not record_errors, record_errors


__all__ = [
    "CONTENT_TYPE_HTML",
    "CONTENT_TYPE_MARKDOWN",
    "CONTENT_TYPE_TEXT",
    "PanelExtra",
    "PanelItem",
    "PanelMetric",
    "PanelTag",
    "PanelTask",
    "WXPUSHER_API",
    "WxPusherConfig",
    "build_example_panel",
    "build_html_panel",
    "load_wxpusher_config",
    "push_html_panel",
    "send_wxpusher",
]
