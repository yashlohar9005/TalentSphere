import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_growth_opportunity_pdf(
    user_name, current_role, next_best_role, promotion_ready_pct,
    salary_growth_pct, strong_areas, improvement_areas,
    recommended_certs, action_plan
):
    """
    Generates a PDF bytes buffer containing the Growth Opportunity Analysis.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    sub_heading = styles['Heading2']
    normal_text = styles['Normal']
    
    elements = []
    
    # Title
    elements.append(Paragraph(f"Growth Opportunity Analysis", title_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph(f"<b>Professional:</b> {user_name}", normal_text))
    elements.append(Paragraph(f"<b>Current Role:</b> {current_role}", normal_text))
    elements.append(Spacer(1, 12))
    
    # AI Generated Section
    elements.append(Paragraph("AI Generated Insights", sub_heading))
    elements.append(Paragraph(f"<b>Next Best Role:</b> {next_best_role}", normal_text))
    elements.append(Paragraph(f"<b>Promotion Readiness:</b> {promotion_ready_pct}%", normal_text))
    elements.append(Paragraph(f"<b>Potential Salary Growth:</b> {salary_growth_pct}%", normal_text))
    elements.append(Spacer(1, 12))
    
    # Skills Analysis
    elements.append(Paragraph("Skills Analysis", sub_heading))
    
    # Strong Areas
    elements.append(Paragraph("<b>Strong Areas (Keep Building):</b>", normal_text))
    for skill in strong_areas:
        elements.append(Paragraph(f"• {skill}", normal_text))
    elements.append(Spacer(1, 8))
    
    # Improvement Areas
    elements.append(Paragraph("<b>Improvement Areas (Focus Next):</b>", normal_text))
    for skill in improvement_areas:
        elements.append(Paragraph(f"• {skill}", normal_text))
    elements.append(Spacer(1, 12))
    
    # Certifications
    if recommended_certs:
        elements.append(Paragraph("Recommended Certifications", sub_heading))
        cert_data = [["Certification", "Priority", "Related Skill"]]
        for cert in recommended_certs:
            cert_data.append([cert['Certification'], cert['Priority'], cert['Related Skill']])
            
        cert_table = Table(cert_data, colWidths=[250, 100, 150])
        cert_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(cert_table)
        elements.append(Spacer(1, 12))
        
    # 90-Day Action Plan
    if action_plan:
        elements.append(Paragraph("90-Day Action Plan (AI Roadmap)", sub_heading))
        plan_data = [["Month", "Focus"]]
        for p in action_plan:
            plan_data.append([p['Month'], p['Focus']])
            
        plan_table = Table(plan_data, colWidths=[100, 400])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.lightsteelblue),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(plan_table)
        
    doc.build(elements)
    buffer.seek(0)
    return buffer
