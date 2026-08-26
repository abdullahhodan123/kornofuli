from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
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
AMBER      = colors.HexColor('#B07D10')
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


def build_student_report_pdf(student, report_data, academy_name=None, tagline=None):
    """Build a full individual student report PDF and return a BytesIO buffer."""
    if not academy_name or not tagline:
        from home.models import SiteSettings
        site = SiteSettings.objects.first()
        if not academy_name:
            academy_name = site.academy_name if site else 'KBA'
        if not tagline:
            tagline = site.tagline if site else ''

    results          = report_data.get('results', [])
    subject_analysis = report_data.get('subject_analysis', [])
    overall          = report_data.get('overall', {})
    attendance       = report_data.get('attendance', {})
    payments         = report_data.get('payments', [])

    buf = BytesIO()
    page = A4
    left = right = 14 * mm
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
        title=f"{student.full_name} — Report Card",
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
    section_style = ParagraphStyle(
        'section', fontName='Helvetica-Bold', fontSize=12, leading=15,
        textColor=HEADER_BG, spaceBefore=10, spaceAfter=4,
    )
    note_style = ParagraphStyle(
        'note', fontName='Helvetica', fontSize=7.5, leading=9.5,
        alignment=1, textColor=MUTED, spaceBefore=4,
    )
    student_name_style = ParagraphStyle(
        'student_name', fontName='Helvetica-Bold', fontSize=13, leading=16,
        textColor=DARK_TEXT, spaceAfter=2,
    )
    student_sub_style = ParagraphStyle(
        'student_sub', fontName='Helvetica', fontSize=9, leading=12,
        textColor=MUTED, spaceAfter=1,
    )

    elements = []

    # ── Header ──
    elements.append(Paragraph(academy_name, title_style))
    if tagline:
        elements.append(Paragraph(tagline, tagline_style))
    elements.append(Paragraph('Student Report Card', ParagraphStyle(
        'subtitle', fontName='Helvetica-Bold', fontSize=13, leading=16,
        alignment=1, textColor=DARK_TEXT, spaceAfter=6,
    )))

    # ── Student Info Box ──
    info_data = [
        ['Student', student.full_name, 'Class', student.classroom.name if student.classroom else '—'],
        ['School', student.school_name or '—', 'Username', student.user.username],
    ]
    info_cols = [usable_width * 0.18, usable_width * 0.32,
                 usable_width * 0.18, usable_width * 0.32]
    info_table = Table(info_data, colWidths=info_cols)
    info_style = [
        ('BACKGROUND', (0, 0), (-1, -1), INFO_BG),
        ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('BOX', (0, 0), (-1, -1), 0.8, HEADER_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
        ('TEXTCOLOR', (2, 0), (2, -1), MUTED),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK_TEXT),
        ('TEXTCOLOR', (3, 0), (3, -1), DARK_TEXT),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]
    info_table.setStyle(TableStyle(info_style))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Signature Boxes (top) ──
    sig_box_width = usable_width * 0.42
    sig_gap = usable_width * 0.06

    sig_data = [[
        Paragraph('Guardian Signature', ParagraphStyle(
            'sig_label', fontName='Helvetica', fontSize=7.5, leading=9,
            alignment=1, textColor=MUTED, spaceBefore=8,
        )),
        '',
        Paragraph('Teacher Signature', ParagraphStyle(
            'sig_label2', fontName='Helvetica', fontSize=7.5, leading=9,
            alignment=1, textColor=MUTED, spaceBefore=8,
        )),
    ]]

    sig_cols = [sig_box_width, sig_gap, sig_box_width]
    sig_table = Table(sig_data, colWidths=sig_cols, rowHeights=[12 * mm])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 0), (0, 0), 0.4, GRID_COLOR),
        ('LINEBELOW', (2, 0), (2, 0), 0.4, GRID_COLOR),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Attendance Section ──
    elements.append(Paragraph('Attendance Overview', section_style))
    elements.append(_rule(usable_width, colors.HexColor('#C9D6E4')))
    elements.append(Spacer(1, 3 * mm))

    att = attendance or {}
    att_total   = att.get('total', 0)
    att_present = att.get('present', 0)
    att_absent  = att.get('absent', 0)
    att_late    = att.get('late', 0)
    att_pct     = att.get('pct', 0)

    att_data = [
        ['Total Classes', 'Present', 'Absent', 'Late', 'Attendance %'],
        [str(att_total), str(att_present), str(att_absent), str(att_late), f"{att_pct}%"],
    ]
    att_cols = [usable_width / 5] * 5
    att_table = Table(att_data, colWidths=att_cols)
    att_style = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_FG),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('BOX', (0, 0), (-1, -1), 0.8, HEADER_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (1, 1), (1, 1), GREEN),
        ('TEXTCOLOR', (2, 1), (2, 1), RED),
        ('TEXTCOLOR', (3, 1), (3, 1), AMBER),
        ('TEXTCOLOR', (4, 1), (4, 1), HEADER_BG),
    ]
    att_table.setStyle(TableStyle(att_style))
    elements.append(att_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Exam Performance Overview ──
    if overall:
        elements.append(Paragraph('Exam Performance Summary', section_style))
        elements.append(_rule(usable_width, colors.HexColor('#C9D6E4')))
        elements.append(Spacer(1, 3 * mm))

        ov_data = [
            ['Avg Percentage', 'Avg GPA', 'Best Exam', 'Worst Exam', 'Passed', 'Failed'],
            [
                f"{overall.get('avg_pct', 0)}%",
                str(overall.get('avg_gpa', 0)),
                f"{overall.get('best', 0)}%",
                f"{overall.get('worst', 0)}%",
                str(overall.get('passed', 0)),
                str(overall.get('failed', 0)),
            ],
        ]
        ov_cols = [usable_width / 6] * 6
        ov_table = Table(ov_data, colWidths=ov_cols)
        ov_style = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.8, HEADER_BG),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TEXTCOLOR', (4, 1), (4, 1), GREEN),
            ('TEXTCOLOR', (5, 1), (5, 1), RED),
        ]
        ov_table.setStyle(TableStyle(ov_style))
        elements.append(ov_table)
        elements.append(Spacer(1, 6 * mm))

    # ── Subject-wise Analysis ──
    if subject_analysis:
        elements.append(Paragraph('Subject-wise Analysis', section_style))
        elements.append(_rule(usable_width, colors.HexColor('#C9D6E4')))
        elements.append(Spacer(1, 3 * mm))

        sub_header = ['#', 'Subject', 'Avg %', 'Best', 'Lowest', 'Exams']
        sub_data = [sub_header]
        for i, s in enumerate(subject_analysis, 1):
            sub_data.append([
                str(i),
                s['subject'],
                f"{s['avg']}%",
                f"{s['high']}%",
                f"{s['low']}%",
                str(s['count']),
            ])

        sub_cols = [8 * mm, usable_width * 0.35, usable_width * 0.15,
                    usable_width * 0.15, usable_width * 0.15, usable_width * 0.12]
        sub_table = Table(sub_data, colWidths=sub_cols, repeatRows=1)

        sub_style_list = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.8, HEADER_BG),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ALT_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]
        sub_table.setStyle(TableStyle(sub_style_list))
        elements.append(sub_table)
        elements.append(Spacer(1, 6 * mm))

    # ── Detailed Exam Results ──
    if results:
        elements.append(Paragraph('Exam Results Detail', section_style))
        elements.append(_rule(usable_width, colors.HexColor('#C9D6E4')))
        elements.append(Spacer(1, 3 * mm))

        for result in results:
            elements.append(Paragraph(
                f"{result.exam.name}  ({result.exam.date.strftime('%d %b %Y')})",
                ParagraphStyle('exam_title', fontName='Helvetica-Bold', fontSize=10,
                               leading=13, textColor=DARK_TEXT, spaceBefore=4, spaceAfter=2),
            ))

            entries = {e.subject_id: e for e in result.mark_entries.all()}
            subjects_in_exam = [e.subject for e in entries.values()]

            ex_header = ['Subject', 'Obtained', 'Full', 'Pass', '%', 'Status']
            ex_data = [ex_header]
            for subj in subjects_in_exam:
                e = entries.get(subj.pk)
                if e:
                    if e.is_absent or e.marks_obtained is None:
                        ex_data.append([
                            subj.name + (' (O)' if subj.is_optional else ''),
                            'Absent',
                            str(subj.full_marks),
                            str(subj.pass_marks),
                            '0%',
                            'Absent',
                        ])
                    else:
                        status = 'Pass' if e.is_passed() else 'Fail'
                        ex_data.append([
                            subj.name + (' (O)' if subj.is_optional else ''),
                            _fmt(e.marks_obtained),
                            str(subj.full_marks),
                            str(subj.pass_marks),
                            f"{e.percentage()}%",
                            status,
                        ])
            ex_data.append([
                'Total',
                _fmt(result.total_marks()),
                str(result.total_full_marks()),
                '—',
                f"{result.percentage()}%",
                result.letter_grade(),
            ])

            ex_cols = [usable_width * 0.30, usable_width * 0.13, usable_width * 0.10,
                       usable_width * 0.10, usable_width * 0.13, usable_width * 0.14]
            ex_table = Table(ex_data, colWidths=ex_cols, repeatRows=1)

            ex_style_list = [
                ('BACKGROUND', (0, 0), (-1, 0), SUB_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), SUB_FG),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7.5),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.3, GRID_COLOR),
                ('BOX', (0, 0), (-1, -1), 0.6, SUB_FG),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), INFO_BG),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]

            # Color fail/absent cells
            for row_idx in range(1, len(ex_data) - 1):
                status_val = ex_data[row_idx][-1]
                if status_val == 'Fail':
                    ex_style_list.append(('TEXTCOLOR', (-1, row_idx), (-1, row_idx), RED))
                    ex_style_list.append(('FONTNAME', (-1, row_idx), (-1, row_idx), 'Helvetica-Bold'))
                elif status_val == 'Absent':
                    ex_style_list.append(('TEXTCOLOR', (-1, row_idx), (-1, row_idx), MUTED))
                    ex_style_list.append(('FONTNAME', (-1, row_idx), (-1, row_idx), 'Helvetica-Oblique'))
                else:
                    ex_style_list.append(('TEXTCOLOR', (-1, row_idx), (-1, row_idx), GREEN))

            # GPA + result status
            result_info = f"GPA: {result.gpa()}  |  Grade: {result.letter_grade()}  |  Position: #{result.serial or '—'}"
            ex_table.setStyle(TableStyle(ex_style_list))
            elements.append(ex_table)
            elements.append(Paragraph(result_info, ParagraphStyle(
                'result_info', fontName='Helvetica', fontSize=7.5, leading=10,
                textColor=MUTED, spaceBefore=1, spaceAfter=4,
            )))

    # ── Payment History ──
    if payments:
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph('Payment History', section_style))
        elements.append(_rule(usable_width, colors.HexColor('#C9D6E4')))
        elements.append(Spacer(1, 3 * mm))

        pay_header = ['#', 'Month', 'Year', 'Status']
        pay_data = [pay_header]
        for i, p in enumerate(payments, 1):
            status_text = 'Paid' if p.is_paid else 'Unpaid'
            pay_data.append([str(i), p.get_month_display(), str(p.year), status_text])

        pay_cols = [8 * mm, usable_width * 0.35, usable_width * 0.25, usable_width * 0.25]
        pay_table = Table(pay_data, colWidths=pay_cols, repeatRows=1)

        pay_style = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.8, HEADER_BG),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ALT_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        for i, p in enumerate(payments, 1):
            if p.is_paid:
                pay_style.append(('TEXTCOLOR', (3, i), (3, i), GREEN))
            else:
                pay_style.append(('TEXTCOLOR', (3, i), (3, i), RED))

        pay_table.setStyle(TableStyle(pay_style))
        elements.append(pay_table)

    # ── Footer ──
    elements.append(Spacer(1, 8 * mm))
    elements.append(_rule(usable_width, GRID_COLOR))
    elements.append(Paragraph(
        f"Generated by {academy_name}",
        note_style,
    ))

    doc.build(elements)
    buf.seek(0)
    return buf
