"""
PDF 생성 서비스 — WeasyPrint + Jinja2
"""
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)

INSPECTION_TYPE_LABELS = {
    "rebar": "철근 배근 검측",
    "formwork": "거푸집 검측",
    "concrete": "콘크리트 타설 검측",
    "pipe_burial": "관 매설 검측",
    "compaction": "다짐 검측",
    "waterproofing": "방수 검측",
    "finishing": "마감 검측",
}

REPORT_TYPE_LABELS = {
    "weekly": "주간",
    "monthly": "월간",
}

REPORT_STATUS_LABELS = {
    "draft": "초안",
    "reviewed": "검토완료",
    "submitted": "제출완료",
}


def _render_html(template_name: str, **context) -> str:
    template = _jinja_env.get_template(template_name)
    return template.render(now=datetime.now().strftime("%Y-%m-%d %H:%M"), **context)


def _html_to_pdf(html: str) -> bytes:
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except ImportError:
        raise RuntimeError(
            "WeasyPrint가 설치되지 않았습니다. `pip install weasyprint` 실행 후 재시도하세요."
        )


def generate_daily_report_pdf(report, project) -> bytes:
    html = _render_html("daily_report.html", report=report, project=project)
    return _html_to_pdf(html)


def generate_inspection_pdf(inspection, project) -> bytes:
    type_label = INSPECTION_TYPE_LABELS.get(inspection.inspection_type, inspection.inspection_type)
    html = _render_html(
        "inspection.html",
        inspection=inspection,
        project=project,
        inspection_type_label=type_label,
    )
    return _html_to_pdf(html)


def generate_report_pdf(report, project) -> bytes:
    type_label = REPORT_TYPE_LABELS.get(report.report_type.value, report.report_type.value)
    status_label = REPORT_STATUS_LABELS.get(report.status.value, report.status.value)
    period_label = f"{report.period_start} ~ {report.period_end} ({type_label})"
    html = _render_html(
        "report.html",
        report=report,
        project=project,
        report_type_label=type_label,
        status_label=status_label,
        period_label=period_label,
        content_json=report.content_json,
        ai_draft_text=report.ai_draft_text,
    )
    return _html_to_pdf(html)
