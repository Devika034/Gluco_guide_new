import io
import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, MedicalProfile, MealPlan, SpikePrediction, PatientRiskBaseline, QuestionnaireScore

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

router = APIRouter(prefix="/report", tags=["Reports"])

@router.get("/health-summary/{user_id}")
def download_health_summary(user_id: int, db: Session = Depends(get_db)):
    # 1. Fetch user data dynamically from database tables
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    medical_profile = db.query(MedicalProfile).filter(MedicalProfile.user_id == user_id).order_by(desc(MedicalProfile.created_at)).first()
    if not medical_profile:
        raise HTTPException(status_code=400, detail="No medical profile found for this user")

    # Fetch latest meal plan
    latest_meal = db.query(MealPlan).filter(MealPlan.user_id == user_id).order_by(desc(MealPlan.created_at)).first()
    
    # Fetch latest spike prediction
    latest_spike = db.query(SpikePrediction).filter(SpikePrediction.user_id == user_id).order_by(desc(SpikePrediction.created_at)).first()

    # Fetch latest risk baseline
    risk_baseline = db.query(PatientRiskBaseline).filter(PatientRiskBaseline.patient_id == str(user_id)).order_by(desc(PatientRiskBaseline.created_at)).first()

    # Fetch questionnaire scores / trend
    q_trend_neuropathy = db.query(QuestionnaireScore.trend).filter(
        QuestionnaireScore.user_id == user_id, 
        QuestionnaireScore.disease_type == "Neuropathy"
    ).order_by(desc(QuestionnaireScore.created_at)).scalar() or "Stable"
    
    q_trend_retinopathy = db.query(QuestionnaireScore.trend).filter(
        QuestionnaireScore.user_id == user_id, 
        QuestionnaireScore.disease_type == "Retinopathy"
    ).order_by(desc(QuestionnaireScore.created_at)).scalar() or "Stable"
    
    q_trend_nephropathy = db.query(QuestionnaireScore.trend).filter(
        QuestionnaireScore.user_id == user_id, 
        QuestionnaireScore.disease_type == "Nephropathy"
    ).order_by(desc(QuestionnaireScore.created_at)).scalar() or "Stable"

    # 2. Build the PDF using ReportLab
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    section_style = styles['Heading2']
    section_style.textColor = colors.indigo
    section_style.spaceAfter = 10

    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 8

    bold_normal = ParagraphStyle('boldNormal', parent=normal_style, fontName='Helvetica-Bold')

    elements = []

    # Title
    elements.append(Paragraph("GlucoGuide – AI Health Summary Report", title_style))
    date_str = datetime.datetime.now().strftime("%d %B %Y")
    elements.append(Paragraph(f"Generated on: {date_str}", ParagraphStyle('centNormal', parent=normal_style, alignment=1)))
    elements.append(Spacer(1, 0.2*inch))

    # --- Section 1: Patient Information ---
    elements.append(Paragraph("1. Patient Information", section_style))
    
    bmi_category = "Normal"
    bmi_val = medical_profile.bmi or 0
    if bmi_val >= 30: bmi_category = "Obese"
    elif bmi_val >= 25: bmi_category = "Overweight"
    elif bmi_val < 18.5: bmi_category = "Underweight"

    act_level_str = {0: "Active", 1: "Sedentary", 2: "Very Active"}.get(medical_profile.activity_level, "Unknown")
    fam_hist_str = "Yes" if medical_profile.family_history else "No"
    alc_smok_str = "Yes" if medical_profile.alcohol_smoking else "No"

    patient_info_data = [
        ["Name:", user.full_name],
        ["Age:", f"{medical_profile.age or 'N/A'} years"],
        ["BMI:", f"{bmi_val:.1f} ({bmi_category})"],
        ["Diabetes Duration:", f"{medical_profile.duration_years or 'N/A'} years"],
        ["Activity Level:", act_level_str],
        ["Family History of Diabetes:", fam_hist_str],
        ["Alcohol/Smoking:", alc_smok_str]
    ]

    t1 = Table(patient_info_data, colWidths=[2.5*inch, 3.5*inch])
    t1.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 0.2*inch))

    # --- Section 2: Medical Parameters ---
    elements.append(Paragraph("2. Medical Parameters Extracted from Reports", section_style))
    
    def num_str(val):
        return str(val) if val is not None else "N/A"

    def interpret_hba1c(val):
        if val is None: return "Unknown"
        if val < 5.7: return "Normal"
        if val < 6.5: return "Prediabetes range"
        if val <= 7.0: return "Within target"
        return "Above recommended level"

    def interpret_bg(val):
        if val is None: return "Unknown"
        if val < 100: return "Normal"
        if val <= 125: return "Impaired fasting glucose"
        return "Higher than normal"

    def interpret_bp(sys, dia):
        if sys is None or dia is None: return "Unknown"
        if sys < 120 and dia < 80: return "Normal"
        if sys >= 140 or dia >= 90: return "Hypertensive"
        return "Elevated"

    def interpret_chol(val):
        if val is None: return "Unknown"
        if val < 200: return "Desirable"
        if val < 240: return "Borderline high"
        return "High"

    med_params = [
        ["Parameter", "Value", "Interpretation"],
        ["HbA1c", f"{num_str(medical_profile.hba1c)} %", interpret_hba1c(medical_profile.hba1c)],
        ["Fasting Glucose", f"{num_str(medical_profile.fasting_glucose)} mg/dL", interpret_bg(medical_profile.fasting_glucose)],
        ["Blood Pressure", f"{num_str(medical_profile.bp_systolic)} / {num_str(medical_profile.bp_diastolic)} mmHg", interpret_bp(medical_profile.bp_systolic, medical_profile.bp_diastolic)],
        ["Cholesterol", f"{num_str(medical_profile.cholesterol)} mg/dL", interpret_chol(medical_profile.cholesterol)],
        ["BMI", f"{bmi_val:.1f}", bmi_category]
    ]

    t2 = Table(med_params, colWidths=[2*inch, 1.5*inch, 2.5*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 0.1*inch))
    
    # Dynamic Medical Summary
    issues = []
    if medical_profile.hba1c and medical_profile.hba1c > 7.0: issues.append("elevated HbA1c")
    if medical_profile.fasting_glucose and medical_profile.fasting_glucose > 130: issues.append("elevated fasting glucose")
    if medical_profile.cholesterol and medical_profile.cholesterol >= 240: issues.append("high cholesterol")
    if medical_profile.bp_systolic and medical_profile.bp_systolic >= 140: issues.append("high blood pressure")

    med_summary_text = ""
    if len(issues) > 0:
        med_summary_text = f"The patient shows {', '.join(issues)}. These factors increase the risk of long-term diabetic complications if not managed properly."
    else:
        med_summary_text = "The patient's logged medical parameters are generally within target ranges. Continue maintaining healthy habits."
    
    elements.append(Paragraph(f"<b>Summary:</b><br/>{med_summary_text}", normal_style))
    elements.append(Spacer(1, 0.2*inch))

    # --- Section 3: AI Complication Risk Prediction ---
    elements.append(Paragraph("3. AI Complication Risk Prediction", section_style))
    elements.append(Paragraph("Based on the uploaded reports and clinical indicators, GlucoGuide predicts the following complication risks:", normal_style))
    
    if risk_baseline:
        risk_data = [
            ["Disease", "5-Year Risk", "10-Year Risk"],
            ["Diabetic Neuropathy", f"{risk_baseline.neuropathy_5y:.1f}%", f"{risk_baseline.neuropathy_10y:.1f}%"],
            ["Diabetic Retinopathy", f"{risk_baseline.retinopathy_5y:.1f}%", f"{risk_baseline.retinopathy_10y:.1f}%"],
            ["Diabetic Nephropathy", f"{risk_baseline.nephropathy_5y:.1f}%", f"{risk_baseline.nephropathy_10y:.1f}%"]
        ]
        
        t3 = Table(risk_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(t3)
        
        # Dynamic Risk Interpretation
        highest_risk = "Unknown"
        max_val = -1
        risks_dict = {
            "diabetic neuropathy": risk_baseline.neuropathy_10y,
            "diabetic retinopathy": risk_baseline.retinopathy_10y,
            "diabetic nephropathy": risk_baseline.nephropathy_10y
        }
        for k, v in risks_dict.items():
            if v > max_val:
                max_val = v
                highest_risk = k

        risk_interp = f"The highest estimated long-term risk is observed for <b>{highest_risk}</b>. Early lifestyle changes and consistent monitoring are strongly recommended."
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(f"<b>Interpretation:</b><br/>{risk_interp}", normal_style))
    else:
        elements.append(Paragraph("<i>No AI risk baseline has been calculated yet. Please ensure full medical data is uploaded.</i>", normal_style))

    elements.append(Spacer(1, 0.2*inch))

    # --- Section 4: Glucose Spike Behaviour Analysis ---
    elements.append(Paragraph("4. Glucose Spike Behavour Analysis", section_style))
    elements.append(Paragraph("The AI spike prediction model analyzed the patient's logged meals and medical parameters.", normal_style))
    
    if latest_spike:
        elements.append(Paragraph(f"<b>Latest Analyzed Context:</b>", normal_style))
        spike_info = [
            [Paragraph("Meal Average GI:", bold_normal), f"{latest_spike.avg_gi:.1f}"],
            [Paragraph("Meal Total GL:", bold_normal), f"{latest_spike.total_gl:.1f}"],
            [Paragraph("Current Glucose:", bold_normal), f"{latest_spike.current_glucose or 'Unknown'} mg/dL"]
        ]
        t4a = Table(spike_info, colWidths=[2.0*inch, 3.0*inch])
        elements.append(t4a)
        elements.append(Spacer(1, 0.1*inch))
        
        spike_pred = [
            [Paragraph("Predicted Spike Probability:", bold_normal), f"{latest_spike.spike_probability:.1f}% ({latest_spike.severity})"]
        ]
        t4b = Table(spike_pred, colWidths=[2.5*inch, 3.5*inch])
        elements.append(t4b)
        
        spike_interp = ""
        if latest_spike.avg_gi > 60:
            spike_interp += "• High GI foods significantly increase glucose spike probability.<br/>"
        if latest_spike.total_gl > 20:
            spike_interp += "• Meals with high glycemic load heavily elevate post-meal glucose.<br/>"
        if medical_profile.hba1c and medical_profile.hba1c > 6.5:
            spike_interp += "• Elevated HbA1c indicates higher overall spike sensitivity.<br/>"
             
        if spike_interp == "":
            spike_interp = "• Meal profile indicates low risk of significant glucose spikes."
             
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("<b>Observations:</b>", normal_style))
        elements.append(Paragraph(spike_interp, normal_style))
    else:
        elements.append(Paragraph("<i>No spike predictions have been requested yet. Use the Spike Predictor to log meals.</i>", normal_style))

    elements.append(Spacer(1, 0.2*inch))
    
    # Page Break for clarity if needed, ReportLab handles it mostly, but good to group
    
    # --- Section 5: Dietary Recommendations ---
    elements.append(Paragraph("5. Dietary Recommendation Summary", section_style))
    
    gi_status = "low"
    if latest_spike and latest_spike.avg_gi > 60: gi_status = "high"
    elif latest_spike and latest_spike.avg_gi > 45: gi_status = "moderate"
    
    if gi_status == "high":
        elements.append(Paragraph("The system strongly recommends shifting to a <b>low-GI diet</b> balanced with complex carbohydrates to reduce post-meal spikes.", normal_style))
        elements.append(Paragraph("<b>Recommended Foods:</b><br/>• Oats, millets, and high-fiber foods<br/>• Non-starchy vegetables (Avial, thoran)<br/>• Lean proteins (Fish curry, chicken, pulses)", normal_style))
        elements.append(Paragraph("<b>Foods to Limit:</b><br/>• White rice in large portions<br/>• Sugary drinks and desserts<br/>• Deep fried foods", normal_style))
    else:
        elements.append(Paragraph("The current dietary GI profile is reasonable. Continue maintaining a balanced, fiber-rich diet.", normal_style))
        elements.append(Paragraph("<b>Recommended Foods:</b><br/>• Complex carbs and whole grains<br/>• Adequate protein and healthy fats<br/>• Leafy greens and water", normal_style))

    elements.append(Spacer(1, 0.2*inch))

    # --- Section 6: Lifestyle Recommendations ---
    elements.append(Paragraph("6. Lifestyle Recommendations", section_style))
    elements.append(Paragraph("To reduce complication risk, the following lifestyle changes are recommended:", normal_style))
    
    lifestyle_tips = []
    if medical_profile.activity_level != 2: # Not very active
        lifestyle_tips.append("• Maintain at least 30-45 minutes of moderate physical activity daily")
    if bmi_category in ["Overweight", "Obese"]:
        lifestyle_tips.append("• Adopt a supervised fitness plan to reduce BMI towards the 25.0 target")
    if medical_profile.bp_systolic and medical_profile.bp_systolic >= 130:
        lifestyle_tips.append("• Reduce dietary sodium/salt intake to help manage elevated blood pressure")
    if medical_profile.cholesterol and medical_profile.cholesterol >= 200:
        lifestyle_tips.append("• Limit saturated fats and trans fats to improve lipid profiles")
    if medical_profile.alcohol_smoking:
        lifestyle_tips.append("• Consider smoking cessation and limiting alcohol to improve cardiovascular margins")
    
    lifestyle_tips.append("• Monitor blood glucose regularly and maintain routine checkups every 3–6 months")
    
    for tip in lifestyle_tips:
        elements.append(Paragraph(tip, normal_style))

    elements.append(Spacer(1, 0.2*inch))

    # --- Section 7: Disease Progress Monitoring ---
    elements.append(Paragraph("7. Disease Progress Monitoring", section_style))
    elements.append(Paragraph("The proactive tracker analysis suggests the following observational symptom trends:", normal_style))
    
    trend_data = [
        ["Neuropathy Trend:", q_trend_neuropathy],
        ["Retinopathy Trend:", q_trend_retinopathy],
        ["Nephropathy Trend:", q_trend_nephropathy]
    ]
    t7 = Table(trend_data, colWidths=[2.0*inch, 3.5*inch])
    elements.append(t7)
    
    if "Worsening" in q_trend_neuropathy or "Worsening" in q_trend_retinopathy or "Worsening" in q_trend_nephropathy:
        elements.append(Paragraph("<br/><b>Special Note:</b> A worsening trend was detected in recent questionnaire responses. Immediate clinical consultation regarding these symptoms is advised.", normal_style))
    else:
        elements.append(Paragraph("<br/>Regular symptom tracking and dietary discipline can significantly assist doctors in reducing long term clinical risks.", normal_style))

    elements.append(Spacer(1, 0.2*inch))

    # --- Section 8: Overall Health Assessment ---
    elements.append(Paragraph("8. Overall Health Assessment", section_style))
    
    high_risk_factors = 0
    if bmi_val >= 30: high_risk_factors += 1
    if medical_profile.hba1c and medical_profile.hba1c > 7.5: high_risk_factors += 1
    if medical_profile.bp_systolic and medical_profile.bp_systolic > 140: high_risk_factors += 1
    
    if risk_baseline:
        if risk_baseline.nephropathy_10y > 50 or risk_baseline.neuropathy_10y > 50 or risk_baseline.retinopathy_10y > 50:
            high_risk_factors += 2

    risk_cat = "Low"
    if high_risk_factors >= 3: risk_cat = "High"
    elif high_risk_factors >= 1: risk_cat = "Moderate"
    
    assessment_text = f"The patient currently falls in the <b>{risk_cat} Risk Category</b> for long-term diabetic complications based on the aggregated data profile.<br/><br/>"
    assessment_text += "However, with appropriate dietary control, physical activity, and regular monitoring, the risk can be significantly managed and delayed.<br/>"
    assessment_text += "GlucoGuide recommends continuing the personalized meal tracking and frequently monitoring predictive glucose spikes after meals."
    
    elements.append(Paragraph(assessment_text, normal_style))
    elements.append(Spacer(1, 0.4*inch))

    # --- Section 9: Disclaimer ---
    disclaimer_style = ParagraphStyle('disclaimer', parent=normal_style, fontSize=9, italic=True, textColor=colors.dimgrey)
    disclaimer_text = """
    <b>Important Disclaimer</b><br/><br/>
    This report is generated by the GlucoGuide AI system based on uploaded medical reports and user inputs.<br/>
    It is intended for educational and monitoring purposes and should not replace professional medical advice.<br/><br/>
    Please consult a qualified healthcare professional for clinical decisions.
    """
    
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("<b>Generated By</b><br/>GlucoGuide – The Diabetes Companion<br/>AI Powered Personalized Diabetes Monitoring System", disclaimer_style))

    # Build PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()

    headers = {
        'Content-Disposition': f'attachment; filename="glucoguide_health_summary_{user.full_name.replace(" ", "_")}.pdf"'
    }
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
