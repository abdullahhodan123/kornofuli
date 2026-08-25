from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


HEADER_BG  = colors.HexColor('#0C447C')
HEADER_FG  = colors.white
SUB_BG     = colors.HexColor('#DCE9F7')
SUB_FG     = colors.HexColor('#3A5A7E')
ALT_BG     = colors.HexColor('#F4F8FC')
GRID_COLOR = colors.HexColor('#B9C9DB')
INFO_BG    = colors.HexColor('#EFF4FA')
RED        = colors.HexColor('#B3261E')
GREEN      = colors.HexColor('#1E7A34')
MUTED      = colors.HexColor('#8A8A85')
DARK_TEXT  = colors.HexColor('#333333')


def _fmt(value):
    value = float(value)
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}"


def _rule(width, color=GRID_COLOR, height=0.7):
    table = Table([['']], colWidths=[width], rowHeights=[height])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table


def build_exam_result_pdf(exam, results, subjects, academy_name=None, tagline=None):
    """Build a full merit-list PDF for an exam and return a BytesIO buffer."""
    from home.models import SiteSettings

    site = None
    if not academy_name or not tagline:
        site = SiteSettings.objects.first()
    if not academy_name:
        academy_name = site.academy_name if site else 'KBA'
    if not tagline:
        tagline = site.tagline if site else ''

    buf = BytesIO()
    page = landscape(A4)
    left = right = 12 * mm
    top = 14 * mm
    bottom = 14 * mm
    usable_width = page[0] - left - right

    doc = SimpleDocTemplate(
        buf,
        pagesize=page,
        leftMargin=left,
        rightMargin=right,
        topMargin=top,
        bottomMargin=bottom,
        title=f"{exam.name} - Result Sheet",
        author=academy_name,
    )

    title_style = ParagraphStyle(
        'title', fontName='Helvetica-Bold', fontSize=17, leading=21,
        alignment=1, textColor=HEADER_BG, spaceAfter=1,
    )
    tagline_style = ParagraphStyle(
        'tagline', fontName='Helvetica', fontSize=8.5, leading=11,
        alignment=1, textColor=MUTED, spaceAfter=3,
    )
    exam_style = ParagraphStyle(
        'exam', fontName='Helvetica-Bold', fontSize=12.5, leading=16,
        alignment=1, textColor=DARK_TEXT, spaceAfter=6,
    )
    section_style = ParagraphStyle(
        'section', fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=HEADER_BG, spaceBefore=2, spaceAfter=2,
    )
    note_style = ParagraphStyle(
        'note', fontName='Helvetica', fontSize=7.5, leading=9.5,
        alignment=1, textColor=MUTED, spaceBefore=4,
    )

    n_subjects = len(subjects)
    total_full = sum(s.full_marks for s in subjects)

    header_row = ['SL', 'Student']
    header_row += [s.name + (' (O)' if s.is_optional else '') for s in subjects]
    header_row += ['Total', '%', 'GPA', 'Grade', 'Status']

    sub_header_row = ['', '']
    sub_header_row += [str(s.full_marks) for s in subjects]
    sub_header_row += [str(total_full), '', '', '', '']

    data = [header_row, sub_header_row]

    pass_count = 0
    failed_cells = []
    failed_status_rows = []

    for result in results:
        if not result.is_failed():
            pass_count += 1
        else:
            failed_status_rows.append(len(data))

        entries = {e.subject_id: e for e in result.mark_entries.all()}

        row = [str(result.serial or '')]
        row.append(result.student.full_name)

        for i, s in enumerate(subjects):
            e = entries.get(s.pk)
            if e is None:
                row.append('-')
            else:
                row.append(_fmt(e.marks_obtained))
                if float(e.marks_obtained) < float(s.pass_marks):
                    failed_cells.append((len(data), 2 + i))

        row += [
            f"{int(result.total_marks())}/{int(result.total_full_marks())}",
            f"{result.percentage()}%",
            str(result.gpa()),
            result.letter_grade(),
            'Pass' if not result.is_failed() else 'Fail',
        ]
        data.append(row)

    if len(data) == 2:
        data.append(['-'] * (2 + n_subjects + 5))

    elements = []
    elements.append(Paragraph(academy_name, title_style))
    if tagline:
        elements.append(Paragraph(tagline, tagline_style))
    elements.append(Paragraph(f"Result Sheet - {exam.name}", exam_style))

    # ── Exam info box ──
    info_data = [
        ['Class', exam.classroom.name, 'Exam Type', exam.get_exam_type_display()],
        ['Date', exam.date.strftime('%d %b %Y'), 'Participants', str(len(results))],
        ['Pass', str(pass_count), 'Fail', str(len(results) - pass_count)],
    ]
    info_cols = [usable_width * 0.20, usable_width * 0.30,
                 usable_width * 0.20, usable_width * 0.30]
    info_table = Table(info_data, colWidths=info_cols)

    info_style = [
        ('BACKGROUND', (0, 0), (-1, -1), INFO_BG),
        ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('BOX', (0, 0), (-1, -1), 0.8, HEADER_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
        ('TEXTCOLOR', (2, 0), (2, -1), MUTED),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK_TEXT),
        ('TEXTCOLOR', (3, 0), (3, -1), DARK_TEXT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TEXTCOLOR', (1, 2), (1, 2), GREEN),
        ('TEXTCOLOR', (3, 2), (3, 2), RED),
    ]
    info_table.setStyle(TableStyle(info_style))

    elements.append(info_table)
    elements.append(Spacer(1, 5 * mm))

    # ── Merit list section ──
    elements.append(Paragraph('Merit List', section_style))
    elements.append(_rule(usable_width, colors.HexColor('#C9D6E4')))
    elements.append(Spacer(1, 3 * mm))

    base_widths = [8 * mm, 34 * mm]
    base_widths += [13 * mm] * n_subjects
    base_widths += [17 * mm, 11 * mm, 12 * mm, 13 * mm, 14 * mm]

    scale = min(1.0, usable_width / sum(base_widths))
    col_widths = [w * scale for w in base_widths]

    status_col = n_subjects + 6

    table = Table(data, colWidths=col_widths, repeatRows=2)

    style = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('BACKGROUND', (0, 1), (-1, 1), SUB_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_FG),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 6.5),
        ('TEXTCOLOR', (0, 1), (-1, 1), SUB_FG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, ALT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('BOX', (0, 0), (-1, -1), 0.8, HEADER_BG),
        ('FONTSIZE', (0, 2), (-1, -1), 8),
        ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 2), (1, -1), 'Helvetica-Bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]

    for (r, c) in failed_cells:
        style.append(('TEXTCOLOR', (c, r), (c, r), RED))
        style.append(('FONTNAME', (c, r), (c, r), 'Helvetica-Bold'))

    for r in failed_status_rows:
        style.append(('TEXTCOLOR', (status_col, r), (status_col, r), RED))
        style.append(('FONTNAME', (status_col, r), (status_col, r), 'Helvetica-Bold'))

    table.setStyle(TableStyle(style))

    elements.append(table)

    note_parts = []
    if any(s.is_optional for s in subjects):
        note_parts.append('(O) = Optional subject')
    if note_parts:
        elements.append(Paragraph('  |  '.join(note_parts), note_style))

    elements.append(Paragraph(
        f"Generated by {academy_name}  |  {exam.date.strftime('%d %b %Y')}",
        note_style,
    ))

    doc.build(elements)
    buf.seek(0)
    return buf
