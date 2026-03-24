"""
준공도서 패키지 자동화 서비스
작업일보, 품질시험, 검측이력, 사진대장, 인허가 현황을 종합하여
준공도서 PDF 번들을 생성합니다.
"""
import io
import zipfile
from datetime import date
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.daily_report import DailyReport
from app.models.quality import QualityTest, QualityResult
from app.models.inspection import InspectionRequest, InspectionStatus
from app.models.permit import PermitItem, PermitStatus

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def _html_to_pdf(html: str) -> bytes:
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except ImportError:
        raise RuntimeError("WeasyPrint가 설치되지 않았습니다. `pip install weasyprint`")


async def build_completion_package(
    db: AsyncSession,
    project_id,
) -> tuple[bytes, str]:
    """
    준공도서 ZIP 패키지 생성.
    반환: (zip_bytes, filename)
    """
    import uuid
    pid = uuid.UUID(str(project_id))
    today = date.today()

    # 프로젝트 정보
    proj_r = await db.execute(select(Project).where(Project.id == pid))
    project = proj_r.scalar_one_or_none()
    if not project:
        raise ValueError("프로젝트를 찾을 수 없습니다")

    # 데이터 수집
    dr_r = await db.execute(
        select(DailyReport).where(DailyReport.project_id == pid).order_by(DailyReport.report_date)
    )
    daily_reports = dr_r.scalars().all()

    qt_r = await db.execute(
        select(QualityTest).where(QualityTest.project_id == pid).order_by(QualityTest.test_date)
    )
    quality_tests = qt_r.scalars().all()

    insp_r = await db.execute(
        select(InspectionRequest).where(InspectionRequest.project_id == pid).order_by(InspectionRequest.requested_date)
    )
    inspections = insp_r.scalars().all()

    permit_r = await db.execute(
        select(PermitItem).where(PermitItem.project_id == pid).order_by(PermitItem.sort_order)
    )
    permits = permit_r.scalars().all()

    # 통계
    total_dr = len(daily_reports)
    total_qt = len(quality_tests)
    pass_qt   = sum(1 for q in quality_tests if q.result == QualityResult.PASS)
    total_insp = len(inspections)
    completed_insp = sum(1 for i in inspections if i.status == InspectionStatus.COMPLETED)
    total_permits = len(permits)
    approved_permits = sum(1 for p in permits if p.status == PermitStatus.APPROVED)

    # 1. 준공 요약 PDF
    summary_html = _jinja.get_template("completion_summary.html").render(
        project=project,
        today=today,
        total_dr=total_dr,
        total_qt=total_qt,
        pass_qt=pass_qt,
        pass_rate=round(pass_qt / total_qt * 100, 1) if total_qt else 0,
        total_insp=total_insp,
        completed_insp=completed_insp,
        total_permits=total_permits,
        approved_permits=approved_permits,
        daily_reports=daily_reports[:5],   # 최근 5개 미리보기
        quality_tests=quality_tests[-10:],  # 마지막 10개 미리보기
    )
    summary_pdf = _html_to_pdf(summary_html)

    # 2. 품질시험 목록 PDF
    qt_html = _jinja.get_template("quality_list.html").render(
        project=project,
        quality_tests=quality_tests,
        today=today,
    )
    qt_pdf = _html_to_pdf(qt_html)

    # 3. 검측 이력 PDF
    insp_html = _jinja.get_template("inspection_list.html").render(
        project=project,
        inspections=inspections,
        today=today,
    )
    insp_pdf = _html_to_pdf(insp_html)

    # 4. 인허가 현황 PDF
    permit_html = _jinja.get_template("permit_list.html").render(
        project=project,
        permits=permits,
        today=today,
    )
    permit_pdf = _html_to_pdf(permit_html)

    # ZIP 번들 생성
    zip_buffer = io.BytesIO()
    project_code = getattr(project, "code", str(pid)[:8])
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"01_준공요약_{project_code}.pdf", summary_pdf)
        zf.writestr(f"02_품질시험목록_{project_code}.pdf", qt_pdf)
        zf.writestr(f"03_검측이력_{project_code}.pdf", insp_pdf)
        zf.writestr(f"04_인허가현황_{project_code}.pdf", permit_pdf)
        zf.writestr("README.txt", (
            f"준공도서 패키지\n"
            f"프로젝트: {project.name}\n"
            f"생성일: {today}\n\n"
            f"포함 문서:\n"
            f"  01_준공요약 — 전체 공사 실적 요약\n"
            f"  02_품질시험목록 — 전체 품질시험 기록 ({total_qt}건)\n"
            f"  03_검측이력 — 검측 요청·완료 이력 ({total_insp}건)\n"
            f"  04_인허가현황 — 인허가 취득 현황 ({total_permits}건)\n"
        ).encode("utf-8"))

    zip_buffer.seek(0)
    filename = f"completion_{project_code}_{today}.zip"
    return zip_buffer.read(), filename
