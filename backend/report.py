from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, os
from datetime import datetime

def generate_bpm_chart(vitals: list) -> str:
    times = [v.timestamp.strftime('%H:%M:%S') for v in vitals[-50:]]
    bpms  = [v.bpm  for v in vitals[-50:]]
    spo2s = [v.spo2 for v in vitals[-50:]]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5), facecolor='white')

    ax1.plot(times, bpms, color='#3b82f6', linewidth=2)
    ax1.axhline(y=100, color='red',    linestyle='--', alpha=0.5, label='Max (100)')
    ax1.axhline(y=50,  color='orange', linestyle='--', alpha=0.5, label='Min (50)')
    ax1.set_ylabel('BPM')
    ax1.set_title('Heart Rate Trend')
    ax1.legend(fontsize=8)
    ax1.tick_params(axis='x', rotation=45, labelsize=7)
    ax1.grid(True, alpha=0.3)

    ax2.plot(times, spo2s, color='#10b981', linewidth=2)
    ax2.axhline(y=94, color='red', linestyle='--', alpha=0.5, label='Min safe (94%)')
    ax2.set_ylabel('SpO2 %')
    ax2.set_title('Blood Oxygen Level')
    ax2.set_ylim([85, 101])
    ax2.legend(fontsize=8)
    ax2.tick_params(axis='x', rotation=45, labelsize=7)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path = f'/tmp/chart_{datetime.now().timestamp()}.png'
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    return path

def generate_health_score(vitals, alerts):
    if not vitals: return 50
    recent   = vitals[-20:]
    avg_bpm  = sum(v.bpm  for v in recent) / len(recent)
    avg_spo2 = sum(v.spo2 for v in recent) / len(recent)
    score = 100
    if avg_bpm  > 100: score -= 20
    if avg_bpm  < 55:  score -= 25
    if avg_spo2 < 96:  score -= 10
    if avg_spo2 < 94:  score -= 20
    score -= min(len(alerts) * 5, 30)
    return max(0, min(100, round(score)))

def generate_report(patient, vitals, alerts) -> bytes:
    buffer  = io.BytesIO()
    doc     = SimpleDocTemplate(buffer, pagesize=A4,
                                 rightMargin=2*cm, leftMargin=2*cm,
                                 topMargin=2*cm,   bottomMargin=2*cm)
    styles  = getSampleStyleSheet()
    story   = []

    # title style
    title_style = ParagraphStyle('title',
        parent=styles['Heading1'],
        fontSize=20, textColor=colors.HexColor('#1e40af'),
        alignment=TA_CENTER, spaceAfter=6)
    sub_style = ParagraphStyle('sub',
        parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER, spaceAfter=20)
    section_style = ParagraphStyle('section',
        parent=styles['Heading2'],
        fontSize=13, textColor=colors.HexColor('#1f2937'),
        spaceBefore=16, spaceAfter=8)

    # Header
    story.append(Paragraph("HealthMonitor — Daily Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", sub_style))

    # Patient info table
    story.append(Paragraph("Patient Information", section_style))
    score = generate_health_score(vitals, alerts)
    score_color = '#16a34a' if score > 75 else '#d97706' if score > 50 else '#dc2626'

    info_data = [
        ['Name',          patient.name,      'Patient ID', patient.id],
        ['Age',           str(patient.age),  'Phone',    patient.phone],
        ['Report Date',   datetime.now().strftime('%d/%m/%Y'),
         'Health Score',  str(score) + '/100'],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#dbeafe')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#dbeafe')),
        ('FONTNAME',   (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',   (2,0), (2,-1), 'Helvetica-Bold'),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1),
         [colors.HexColor('#f8fafc'), colors.white]),
        ('PADDING',    (0,0), (-1,-1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # Vitals summary
    if vitals:
        story.append(Paragraph("Vitals Summary", section_style))
        bpms  = [v.bpm  for v in vitals]
        spo2s = [v.spo2 for v in vitals]
        summary_data = [
            ['Metric', 'Min', 'Max', 'Average', 'Status'],
            ['Heart Rate (BPM)',
             f'{min(bpms):.0f}', f'{max(bpms):.0f}',
             f'{sum(bpms)/len(bpms):.1f}',
             'Normal' if 50 <= sum(bpms)/len(bpms) <= 100 else 'Abnormal'],
            ['SpO2 (%)',
             f'{min(spo2s):.1f}', f'{max(spo2s):.1f}',
             f'{sum(spo2s)/len(spo2s):.1f}',
             'Normal' if sum(spo2s)/len(spo2s) >= 94 else 'Low'],
            ['Total Readings', str(len(vitals)), '', '', ''],
            ['Total Alerts',   str(len(alerts)), '', '', ''],
        ]
        summary_table = Table(summary_data,
                              colWidths=[5*cm, 2.5*cm, 2.5*cm, 3*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1),
             [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING',    (0,0), (-1,-1), 8),
            ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # Chart
        story.append(Paragraph("Vital Signs Chart", section_style))
        chart_path = generate_bpm_chart(vitals)
        story.append(Image(chart_path, width=16*cm, height=8*cm))
        story.append(Spacer(1, 12))

    # Alert log
    story.append(Paragraph("Alert Log", section_style))
    if alerts:
        alert_data = [['Time', 'Type', 'Score', 'Reason']]
        for a in alerts[:20]:
            alert_data.append([
                a.timestamp.strftime('%H:%M:%S'),
                a.alert_type,
                f'{a.anomaly_score:.2f}',
                a.shap_reason[:50] + ('...' if len(a.shap_reason) > 50 else '')
            ])
        alert_table = Table(alert_data, colWidths=[2.5*cm, 3.5*cm, 2*cm, 9*cm])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1),
             [colors.HexColor('#fef2f2'), colors.white]),
            ('PADDING',    (0,0), (-1,-1), 6),
        ]))
        story.append(alert_table)
    else:
        story.append(Paragraph("No alerts recorded today.",
                                styles['Normal']))

    # Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This report was generated automatically by HealthMonitor AI System. "
        "Please consult a medical professional for diagnosis.",
        ParagraphStyle('footer', parent=styles['Normal'],
                       fontSize=8, textColor=colors.HexColor('#9ca3af'),
                       alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()