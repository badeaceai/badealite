import streamlit as st
from openai import OpenAI
import json
import datetime
import io
import os
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, Image, NextPageTemplate,
    PageTemplate, Frame
)
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Image, Frame
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
import io
import os
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, PageTemplate, Frame, PageBreak, Image, Paragraph, NextPageTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import uuid
import pandas as pd
import streamlit as st
from openai import OpenAI
import json
import datetime
import io
import os
import re
import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, Image, NextPageTemplate,
    PageTemplate, Frame
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import ssl
import logging
# 11/12/2024
# Email Configuration
EMAIL_SENDER = "badea@ceaiglobal.com"
EMAIL_PASSWORD = "MyFinB2024123#"
SMTP_SERVER = "mail.ceaiglobal.com"
SMTP_PORT = 465

# Set up logging
logging.basicConfig(level=logging.INFO)

def send_email_with_attachments(receiver_email, organization_name, subject, body, attachments):
    """
    Send email with PDF report attachment using ceaiglobal.com email
    
    Args:
        receiver_email (str): Recipient's email address
        organization_name (str): Name of the organization
        subject (str): Email subject
        body (str): Email body text
        attachments (list): List of tuples containing (file_buffer, filename, mime_type)
    """
    try:
        # Log attempt
        logging.info(f"Attempting to send email to: {receiver_email}")
        
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = receiver_email
        msg['Subject'] = f"{subject} - {organization_name}"

        # Attach the body
        msg.attach(MIMEText(body, 'plain'))

        # Attach files
        for file_buffer, filename, mime_type in attachments:
            attachment = MIMEBase(*mime_type.split('/'))
            attachment.set_payload(file_buffer.getvalue())
            encoders.encode_base64(attachment)
            
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            msg.attach(attachment)

        # Create SSL context
        context = ssl.create_default_context()
        
        # Attempt to send email
        logging.info("Connecting to SMTP server...")
        try:
            # Try SSL first
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                logging.info("Connected with SSL")
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
                
        except Exception as ssl_error:
            logging.warning(f"SSL connection failed: {str(ssl_error)}")
            logging.info("Trying TLS connection...")
            # If SSL fails, try TLS
            with smtplib.SMTP(SMTP_SERVER, 587) as server:
                server.starttls(context=context)
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
                
        st.success(f"Report sent successfully to {receiver_email}")
        logging.info(f"Email sent successfully to {receiver_email}")
        return True
        
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logging.error(error_msg, exc_info=True)
        st.error(error_msg)
        print(f"Detailed email error: {str(e)}")  # For debugging
        return False
# Constants
FIELDS_OF_INDUSTRY = [
    "Agriculture", "Forestry", "Fishing", "Mining and Quarrying",
    "Oil and Gas Exploration", "Automotive", "Aerospace",
    "Electronics", "Textiles and Apparel", "Food and Beverage Manufacturing",
    "Steel and Metalworking", "Construction and Infrastructure",
    "Energy and Utilities", "Chemical Production",
    "Banking and Financial Services", "Insurance", "Retail and E-commerce",
    "Tourism and Hospitality", "Transportation and Logistics",
    "Real Estate and Property Management", "Healthcare and Pharmaceuticals",
    "Telecommunications", "Media and Entertainment", "Others"
]

ORGANIZATION_TYPES = [
    "Public Listed Company",
    "Financial Institution",
    "SME/Enterprise",
    "Government Agency",
    "NGO",
    "Others"
]

ESG_READINESS_QUESTIONS = {
    "1. Have you started formal ESG initiatives within your organization?": [
        "No, we haven't started yet.",
        "Yes, we've started basic efforts but lack a structured plan.",
        "Yes, we have a formalized ESG framework in place.",
        "Yes, we are actively implementing and reporting ESG practices.",
        "Yes, practices are monitored, tracked to work towards our ESG goals."
    ],
    "2. What is your primary reason for considering ESG initiatives?": [
        "To regularise because of sanctions imposed by regulators",
        "To comply with regulations and avoid penalties.",
        "To improve reputation and meet stakeholder demands.",
        "To attract investors or access green funding.",
        "To align with broader sustainability and ethical goals."
    ],
    "3. Do you have a team or individual responsible for ESG in your organization?": [
        "No, there is no one currently assigned to ESG matters.",
        "Yes, but they are not exclusively focused on ESG.",
        "Yes, we have a dedicated ESG team or officer.",
        "Yes, and we also involve external advisors for support.",
        "There is a framework with top-down board involvement."
    ],
    "4. Are you aware of the ESG standards relevant to your industry?": [
        "No, I am unfamiliar with industry-specific ESG standards.",
        "I've heard of them but don't fully understand how to apply them.",
        "Yes, I am somewhat familiar and have started researching.",
        "Yes, and we have begun aligning our operations with these standards.",
        "Have full frameworks for compliance with all required standards."
    ],
    "5. Do you currently measure your environmental or social impacts?": [
        "No, we have not started measuring impacts.",
        "Yes, we measure basic indicators (e.g., waste, energy use).",
        "Yes, we measure basic Scope1/Scope2 and less than 2 parameters S3 with no tracking system.",
        "Yes, we track a range of metrics but need a better system.",
        "Yes, we have comprehensive metrics with detailed reports."
    ],
    "6. What is your biggest challenge in starting or scaling ESG initiatives?": [
        "Lack of knowledge, awareness and expertise.",
        "Insufficient budget and resources.",
        "No ESG Culture",
        "Difficulty aligning ESG goals with business priorities.",
        "Regulatory complexity and compliance requirements."
    ],
    "7. Carbon Footprint/GHG Protocol": [
        "No carbon footprint calculations.",
        "Scope 1/Scope 2 internally available - not published.",
        "Scope 1/Scope 2 published - websites etc.",
        "Working towards targets for carbon footprint reduction.",
        "Aligned with international guidelines (under guidelines of GHG Protocol, SDG Goals etc)."
    ],
    "8. Other parameters": [
        "No detailed parameter calculations.",
        "Scope 1/Scope 2 internally available - not published.",
        "Scope 1/Scope 2 published - websites etc.",
        "Working towards targets for carbon footprint reduction.",
        "Aligned with international guidelines (under guidelines of GHG Protocol, SDG Goals etc)."
    ],
    "9. Social": [
        "No detailed parameter calculations.",
        "Minimum compliance, penalized from regulatory bodies in past 3 years.",
        "Compliant with local/international human rights/labour law compliance standards.",
        "Compliant - no sanctions, detailed parameters (Diversity numbers, Employee participation, Inclusion policies published online).",
        "As above, having received compliance recognition from regulatory bodies."
    ],
    "10. Governance": [
        "No ESG dedicated team.",
        "Very basic governance.",
        "Governance policies (ABC, Code of Conduct) published in website.",
        "Very comprehensive policy with dedicated ESG head.",
        "Governance aligned with international standard practices."
    ]
}
# Location options
COMPANY_LOCATIONS = [ "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", "Congo-Brazzaville", "Congo-Kinshasa", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", "São Tomé and Príncipe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe" ]

# Business nature options
BUSINESS_NATURE = [ "Social Infrastructure", "Energy", "Agriculture Value Chains", "SMEs and Entrepreneurship Finance", "Digital Economy (ICT)", "Transportation", "Urban Development", "Financial Services", "Healthcare", "Education", "Agribusiness and Agro-Industry", "Infrastructure", "Tourism and Hospitality", "Natural Resources", "Real Estate and Property Development", "Manufacturing and Heavy Industries", "SMEs and Entrepreneurship Development", "Other" ]

# Project cost options
PROJECT_COST_RANGES = [ "Less than $1 million", "$1 million–$5 million", "$5 million–$10 million", "More than $10 million" ]

# Self funding options
SELF_FUNDING_RANGES = [ "Less than 10%", "10%–25%", "25%–50%", "More than 50%" ]

# Financial projection options
FINANCIAL_PROJECTION = [ "Yes", "No" ]

# Revenue options
REVENUE_RANGES = [ "Less than $1 million", "$1 million–$5 million", "$5 million–$10 million", "More than $10 million" ]

# Break even options
BREAK_EVEN_PERIODS = [ "Less than 1 year", "1–2 years", "2–5 years", "More than 5 years" ]

# Job creation options
JOB_CREATION_RANGES = [ "Less than 50 jobs", "50–100 jobs", "100–500 jobs", "More than 500 jobs" ]

# Community benefit options
COMMUNITY_BENEFIT_RANGES = [ "Less than 10%", "10%–25%", "25%–50%", "More than 50%" ]

# Local economy contribution options
LOCAL_ECONOMY_IMPACTS = [ "Increase in local employment", "Boost in GDP contribution", "Development of infrastructure", "Support for local businesses" ]

# SDG options
SDG_OPTIONS = [ "SDG 1: No Poverty", "SDG 2: Zero Hunger", "SDG 7: Affordable and Clean Energy", "SDG 8: Decent Work and Economic Growth", "SDG 9: Industry, Innovation, and Infrastructure", "SDG 13: Climate Action" ]

# Financial Health Check Questions Structure
FINANCIAL_CHECK_QUESTIONS = {
    "Project Overview": {
        "country": {
            "type": "selectbox",
            "label": "Where is the company located?",
            "options": COMPANY_LOCATIONS
        },
        "business_nature": {
            "type": "selectbox",
            "label": "Nature of Business",
            "options": BUSINESS_NATURE
        },
        "project_cost": {
            "type": "selectbox",
            "label": "What is the total project cost or investment required?",
            "options": PROJECT_COST_RANGES
        }
    },
    "Financial Status": {
        "self_funding": {
            "type": "selectbox",
            "label": "What percentage of the project cost will be self-funded or from other sources?",
            "options": SELF_FUNDING_RANGES
        },
        "financial_projection": {
            "type": "radio",
            "label": "Do you have a detailed financial projection for the project?",
            "options": FINANCIAL_PROJECTION
        },
        "expected_revenue": {
            "type": "selectbox",
            "label": "What is your expected revenue?",
            "options": REVENUE_RANGES
        },
        "break_even": {
            "type": "selectbox",
            "label": "When do you expect the project to break even?",
            "options": BREAK_EVEN_PERIODS
        }
    },
    "Project Impact": {
        "job_creation": {
            "type": "selectbox",
            "label": "What is the projected number of jobs that will be created?",
            "options": JOB_CREATION_RANGES
        },
        "community_benefit": {
            "type": "selectbox",
            "label": "What percentage of the local community will benefit from this project?",
            "options": COMMUNITY_BENEFIT_RANGES
        },
        "local_economy": {
            "type": "multiselect",
            "label": "How will this project contribute to the local economy?",
            "options": LOCAL_ECONOMY_IMPACTS
        },
        "sdg_alignment": {
            "type": "multiselect",
            "label": "Select relevant UN Sustainable Development Goals (SDGs)",
            "options": SDG_OPTIONS
        }
    }
}
import pandas as pd
from io import BytesIO

def generate_excel_report(user_data):
    """Generate Excel report with user input data"""
    output = BytesIO()
    
    # Create Excel writer object
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    workbook = writer.book
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D9D9D9',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'text_wrap': True,
        'valign': 'top',
        'border': 1
    })
    
    # Create General Information sheet
    general_info = {
        'Field': [
            'Organization Name',
            'Industry',
            'Core Activities',
            'Full Name',
            'Email',
            'Mobile Number'
        ],
        'Value': [
            user_data.get('organization_name', ''),
            user_data.get('industry', ''),
            user_data.get('core_activities', ''),
            user_data.get('full_name', ''),
            user_data.get('email', ''),
            user_data.get('mobile_number', '')
        ]
    }
    df_general = pd.DataFrame(general_info)
    df_general.to_excel(writer, sheet_name='General Information', index=False)
    
    # Format General Information sheet
    worksheet = writer.sheets['General Information']
    for col_num, value in enumerate(df_general.columns.values):
        worksheet.write(0, col_num, value, header_format)
    worksheet.set_column('A:A', 30)
    worksheet.set_column('B:B', 50)
    
    # Format data cells
    for row_num in range(len(df_general)):
        for col_num in range(len(df_general.columns)):
            worksheet.write(row_num + 1, col_num, df_general.iloc[row_num, col_num], cell_format)
    
    # Create ESG Responses sheet
    esg_responses = user_data.get('esg_responses', {})
    esg_data = {
        'Question': list(esg_responses.keys()),
        'Response': list(esg_responses.values())
    }
    df_esg = pd.DataFrame(esg_data)
    df_esg.to_excel(writer, sheet_name='ESG Responses', index=False)
    
    # Format ESG Responses sheet
    worksheet = writer.sheets['ESG Responses']
    for col_num, value in enumerate(df_esg.columns.values):
        worksheet.write(0, col_num, value, header_format)
    worksheet.set_column('A:A', 60)
    worksheet.set_column('B:B', 60)
    
    # Format data cells
    for row_num in range(len(df_esg)):
        for col_num in range(len(df_esg.columns)):
            worksheet.write(row_num + 1, col_num, df_esg.iloc[row_num, col_num], cell_format)
    
    # Create Framework Selection sheet
    frameworks_data = []
    for org_type in user_data.get('organization_types', []):
        if org_type == "Others" and "other_frameworks" in user_data:
            # Add each custom framework
            for framework in user_data["other_frameworks"]:
                frameworks_data.append({
                    'Framework Type': 'Others',
                    'Framework Name': framework
                })
        else:
            frameworks_data.append({
                'Framework Type': org_type,
                'Framework Name': 'Standard Framework'
            })
    
    df_frameworks = pd.DataFrame(frameworks_data)
    df_frameworks.to_excel(writer, sheet_name='Framework Selection', index=False)
    
    # Format Framework Selection sheet
    worksheet = writer.sheets['Framework Selection']
    for col_num, value in enumerate(df_frameworks.columns.values):
        worksheet.write(0, col_num, value, header_format)
    worksheet.set_column('A:A', 30)
    worksheet.set_column('B:B', 50)
    
    # Format data cells
    for row_num in range(len(df_frameworks)):
        for col_num in range(len(df_frameworks.columns)):
            worksheet.write(row_num + 1, col_num, df_frameworks.iloc[row_num, col_num], cell_format)
    
    writer.close()
    output.seek(0)
    return output
class PDFWithTOC(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        SimpleDocTemplate.__init__(self, *args, **kwargs)
        self.page_numbers = {}
        self.current_page = 1
        # Store both company name and personal info
        if 'personal_info' in kwargs:
            self.company_name = kwargs['personal_info'].get('name', '')
            self.personal_info = kwargs['personal_info']  # Store the full personal info
            del kwargs['personal_info']

    def afterPage(self):
        self.current_page += 1

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style == 'heading':
                text = flowable.getPlainText()
                self.page_numbers[text] = self.current_page
def create_esg_score_charts(scores, styles, elements):
    """Create dashboard-style ESG score visualizations for PDF report"""
    from reportlab.graphics.shapes import Drawing, String, Rect, Line
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.textlabels import Label
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    # Custom colors for dashboard
    PRIMARY_COLOR = colors.black
    SECONDARY_COLOR = colors.HexColor('#3B82F6')
    BACKGROUND_COLOR = colors.HexColor('#F3F4F6')
    TEXT_COLOR = colors.HexColor('#1F2937')
    BORDER_COLOR = colors.HexColor('#E5E7EB')
    SUBTEXT_COLOR = colors.HexColor('#6B7280')

    # Create custom paragraph styles
    title_style = ParagraphStyle(
        'DashboardTitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=15,
        spaceBefore=10
    )

    metric_value_style = ParagraphStyle(
        'MetricValue',
        parent=styles['Normal'],
        fontSize=12,
        textColor=TEXT_COLOR,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=5
    )

    metric_label_style = ParagraphStyle(
        'MetricLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=SUBTEXT_COLOR,
        alignment=TA_CENTER,
        spaceBefore=5
    )

    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=PRIMARY_COLOR,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=5
    )

    # Add dashboard title
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("ESG Readiness Dashboard", title_style))
    elements.append(Spacer(1, 0.2*inch))

    # Create metric cards
    overall_data = [[
        [
            Paragraph(f"{scores['overall_score']:.2f}", metric_value_style),
            Paragraph("Overall Score", metric_label_style)
        ],
        [
            Paragraph(f"{scores['readiness_level']}", metric_value_style),
            Paragraph("Readiness Level", metric_label_style)
        ],
        [
            Paragraph(f"{(scores['overall_score'] / 5) * 100:.1f}%", metric_value_style),
            Paragraph("ESG Maturity", metric_label_style)
        ]
    ]]

    overall_table = Table(overall_data, colWidths=[2*inch, 2*inch, 2*inch])
    overall_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BACKGROUND_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('LINEABOVE', (0, 0), (-1, 0), 2, PRIMARY_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(overall_table)
    elements.append(Spacer(1, 0.3*inch))

    # Create charts with increased height
    # Category scores chart
    drawing1 = Drawing(250, 280)  # Increased height further
    title1 = String(125, 265, 'Category Scores', fontSize=10, textAnchor='middle', fillColor=TEXT_COLOR)
    drawing1.add(title1)

    bc1 = VerticalBarChart()
    bc1.x = 35
    bc1.y = 50  # Increased bottom margin for labels
    bc1.height = 180
    bc1.width = 190

    data1 = [list(scores['category_scores'].values())]
    bc1.data = data1

    bc1.valueAxis.valueMin = 0
    bc1.valueAxis.valueMax = 5
    bc1.valueAxis.valueStep = 1
    bc1.bars[0].fillColor = SECONDARY_COLOR
    bc1.categoryAxis.categoryNames = list(scores['category_scores'].keys())
    bc1.categoryAxis.labels.boxAnchor = 'ne'
    bc1.categoryAxis.labels.angle = 45
    bc1.categoryAxis.labels.fontSize = 5
    bc1.categoryAxis.labels.dy = -10  # Increased negative value to move labels down
    bc1.valueAxis.labels.fontSize = 8
    bc1.valueAxis.gridStrokeColor = BORDER_COLOR
    bc1.valueAxis.strokeColor = TEXT_COLOR
    bc1.categoryAxis.strokeColor = TEXT_COLOR

    drawing1.add(bc1)

    # Question scores chart (match height for consistency)
    drawing2 = Drawing(250, 280)  # Match new height
    title2 = String(125, 265, 'Question Scores', fontSize=10, textAnchor='middle', fillColor=TEXT_COLOR)
    drawing2.add(title2)


    bc2 = VerticalBarChart()
    bc2.x = 35
    bc2.y = 30
    bc2.height = 180  # Increased height to match
    bc2.width = 190

    data2 = [list(scores['individual_scores'].values())]
    bc2.data = data2

    bc2.valueAxis.valueMin = 0
    bc2.valueAxis.valueMax = 5
    bc2.valueAxis.valueStep = 1
    bc2.bars[0].fillColor = SECONDARY_COLOR
    q_labels = [f"Q{i+1}" for i in range(len(scores['individual_scores']))]
    bc2.categoryAxis.categoryNames = q_labels
    bc2.categoryAxis.labels.boxAnchor = 'ne'
    bc2.categoryAxis.labels.fontSize = 8
    bc2.categoryAxis.labels.dy = -15
    bc2.valueAxis.labels.fontSize = 8
    bc2.valueAxis.gridStrokeColor = BORDER_COLOR
    bc2.valueAxis.strokeColor = TEXT_COLOR
    bc2.categoryAxis.strokeColor = TEXT_COLOR

    drawing2.add(bc2)

    # Create a table for charts
    charts_table = Table([[drawing1, drawing2]], colWidths=[250, 250])
    charts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BACKGROUND_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))

    elements.append(charts_table)
    elements.append(Spacer(1, 0.3*inch))

    # Score interpretation table
    elements.append(PageBreak())
    elements.append(Paragraph("Score Ranges & Maturity Levels", section_title_style))
    elements.append(Spacer(1, 0.15*inch))

    interpretation_data = [
        ["Score Range", "Maturity Level"],
        ["1.0-1.5", "Initial Stage"],
        ["1.6-2.5", "Developing"],
        ["2.6-3.5", "Established"],
        ["3.6-4.5", "Advanced"],
        ["4.6-5.0", "Leading"]
    ]

    interpretation_table = Table(interpretation_data, colWidths=[1.5*inch, 2*inch])
    interpretation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 1), (-1, -1), BACKGROUND_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(interpretation_table)
    elements.append(Spacer(1, 0.3*inch))

    # Detailed scores table
    elements.append(Paragraph("Detailed Question Analysis", section_title_style))
    elements.append(Spacer(1, 0.15*inch))

    question_data = [["Question", "Score"]]
    question_data.extend([[question, f"{score:.2f}"] for question, score in scores['individual_scores'].items()])

    question_table = Table(question_data, colWidths=[5*inch, 0.5*inch])
    question_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BACKGROUND_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
    ]))

    elements.append(question_table)
    elements.append(Spacer(1, 0.2*inch))
    elements.append(PageBreak())
def generate_pdf(esg_data, personal_info, toc_page_numbers):
    buffer = io.BytesIO()
    
    # Initialize PDF document
    doc = PDFWithTOC(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=1.5*inch,
        bottomMargin=inch,
        personal_info=personal_info
    )
    
    # Define frames for different page types
    full_page_frame = Frame(
        0, 0, letter[0], letter[1],
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0
    )
    
    normal_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='normal'
    )
    
    disclaimer_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='disclaimer'
    )
    
    # Define cover page function with text overlay
    # def cover_page(canvas, doc):
    #     """Draw the cover page with image and text overlay"""
    #     canvas.saveState()
    #     try:
    #         # Load and draw the background image (only once)
    #         if os.path.exists("frontemma.jpg"):
    #             canvas.drawImage(
    #                 "frontemma.jpg",
    #                 0, 0,
    #                 width=letter[0],
    #                 height=letter[1],
    #                 preserveAspectRatio=False  # Ensure full-page coverage
    #             )

    #         # Draw organization name
    #             canvas.setFont("Helvetica", 24)
    #             org_name = f"{doc.personal_info.get('name', '')}"
    #             canvas.setFillColorRGB(1, 1, 1)  # Set text color to white
    #             org_name = f"{doc.personal_info.get('name', '')}"
    #             # Set coordinates for the top-left corner
    #             x = doc.leftMargin  # Use left margin for alignment
    #             y = letter[1] - doc.topMargin  # Top margin distance from the top of the page

    #             # Draw the string
    #             canvas.drawString(x, y, org_name)
    #     except Exception as e:
    #         print(f"Error in cover_page function: {str(e)}")
    #     finally:
    #         canvas.restoreState()

    # Define page templates
    templates = [
        # PageTemplate(id='Cover', frames=[full_page_frame], onPage=cover_page),
        PageTemplate(id='Later', frames=[normal_frame], onPage=create_header_footer),
        PageTemplate(id='dis', frames=[normal_frame], onPage=create_header_footer_disclaimer)
    ]
    doc.addPageTemplates(templates)
    
    # Create styles
    styles = create_custom_styles()
    
    # TOC style
    toc_style = ParagraphStyle(
        'TOCEntry',
        parent=styles['normal'],
        fontSize=12,
        leading=20,
        leftIndent=20,
        rightIndent=30,
        spaceBefore=10,
        spaceAfter=10,
        fontName='Helvetica'
    )
    styles['toc'] = toc_style
    
    # Initialize elements list
    elements = []
    
    # Add cover page
    # elements.append(NextPageTemplate('Cover'))
    # elements.append(Spacer(1, letter[1]))
    # elements.append(PageBreak())
    
    # Switch to normal pages and add TOC
    elements.append(NextPageTemplate('Later'))
    # elements.append(PageBreak())
    elements.append(Paragraph("Table of Contents", styles['heading']))
    
    # Section data
    section_data = [
        ("ESG Initial Assessment", esg_data['analysis1']),
        ("Framework Analysis", esg_data['analysis2']),
        ("Continuation Framework Analysis",esg_data['analysis3']),
        ("Management Issues", esg_data['management_questions']),
        ("Implementation Challenges", esg_data['implementation_challenges']),
        ("Advisory Plan", esg_data['advisory']),
        ("SROI Analysis", esg_data['sroi'])
    ]
    
    # Format TOC entries
    def create_toc_entry(num, title, page_num):
        title_with_num = f"{num}. {title}"
        dots = '.' * (50 - len(title_with_num))
        return f"{title_with_num} {dots} {page_num}"

    # Add TOC entries
    static_entry = create_toc_entry(1, "Profile Analysis", 3)
    elements.append(Paragraph(static_entry, toc_style))
    
    for i, ((title, _), page_num) in enumerate(zip(section_data, toc_page_numbers), 2):
        toc_entry = create_toc_entry(i, title, page_num)
        elements.append(Paragraph(toc_entry, toc_style))
    
    elements.append(PageBreak())
    
    # Add content pages
    elements.extend(create_second_page(styles, personal_info))
    elements.append(PageBreak())
    
    # Add ESG scores chart if available
    
    # Add main content
    for i, (title, content) in enumerate(section_data):
        elements.append(Paragraph(title, styles['heading']))
        process_content(content, styles, elements)
        if i < len(section_data) - 1:
            elements.append(PageBreak())
    
    # Add disclaimer
    elements.append(NextPageTemplate('dis'))
    elements.append(PageBreak())
    create_disclaimer_page(styles, elements)
    
    # Add back cover
    # elements.append(NextPageTemplate('Cover'))
    # elements.append(PageBreak())
    # if os.path.exists("backemma.png"):
    #     img = Image("backemma.png", width=letter[0], height=letter[1])
    #     elements.append(img)
    
    # Build the PDF
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
def generate_pdf_summary(summary_data, personal_info, toc_page_numbers):
    buffer = io.BytesIO()
    
    # Initialize PDF document
    doc = PDFWithTOC(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=1.5*inch,
        bottomMargin=inch,
        personal_info=personal_info
    )
    
    # Define frames for different page types
    full_page_frame = Frame(
        0, 0, letter[0], letter[1],
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0
    )
    
    normal_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='normal'
    )
    
    disclaimer_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='disclaimer'
    )
    
    # Define cover page function with text overlay
    # def cover_page(canvas, doc):
    #     """Draw the cover page with image and text overlay"""
    #     canvas.saveState()
    #     try:
    #         # Load and draw the background image (only once)
    #         if os.path.exists("frontemma.jpg"):
    #             canvas.drawImage(
    #                 "frontemma.jpg",
    #                 0, 0,
    #                 width=letter[0],
    #                 height=letter[1],
    #                 preserveAspectRatio=False  # Ensure full-page coverage
    #             )

    #         # Draw organization name
    #             canvas.setFont("Helvetica", 24)
    #             org_name = f"{doc.personal_info.get('name', '')}"
    #             canvas.setFillColorRGB(1, 1, 1)  # Set text color to white
    #             org_name = f"{doc.personal_info.get('name', '')}"
    #             # Set coordinates for the top-left corner
    #             x = doc.leftMargin  # Use left margin for alignment
    #             y = letter[1] - doc.topMargin  # Top margin distance from the top of the page

    #             # Draw the string
    #             canvas.drawString(x, y, org_name)
    #     except Exception as e:
    #         print(f"Error in cover_page function: {str(e)}")
    #     finally:
    #         canvas.restoreState()

    # Define page templates
    templates = [
        # PageTemplate(id='Cover', frames=[full_page_frame], onPage=cover_page),
        PageTemplate(id='Later', frames=[normal_frame], onPage=create_header_footer),
        PageTemplate(id='dis', frames=[normal_frame], onPage=create_header_footer_disclaimer)
    ]
    doc.addPageTemplates(templates)
    
    # Create styles
    styles = create_custom_styles()
    
    # TOC style
    toc_style = ParagraphStyle(
        'TOCEntry',
        parent=styles['normal'],
        fontSize=12,
        leading=20,
        leftIndent=20,
        rightIndent=30,
        spaceBefore=10,
        spaceAfter=10,
        fontName='Helvetica'
    )
    styles['toc'] = toc_style
    
    # Initialize elements list
    elements = []
    
    # Add cover page
    # elements.append(NextPageTemplate('Cover'))
    # elements.append(Spacer(1, letter[1]))
    # elements.append(PageBreak())
    
    # Switch to normal pages and add TOC
    elements.append(NextPageTemplate('Later'))
    # elements.append(PageBreak())
    elements.append(Paragraph("Table of Contents", styles['heading']))
    
    # Section data
    section_data = [
        ("Executive Summary", summary_data['summary'])
    ]
    
    # Format TOC entries
    def create_toc_entry(num, title, page_num):
        title_with_num = f"{num}. {title}"
        dots = '.' * (50 - len(title_with_num))
        return f"{title_with_num} {dots} {page_num}"

    # Add TOC entries
    static_entry = create_toc_entry(1, "Profile Analysis", 3)
    elements.append(Paragraph(static_entry, toc_style))
    static_entry = create_toc_entry(2, "ESG Dashboard", 4)
    elements.append(Paragraph(static_entry, toc_style))
    
    for i, ((title, _), page_num) in enumerate(zip(section_data, toc_page_numbers), 2):
        toc_entry = create_toc_entry(i, title, page_num)
        elements.append(Paragraph(toc_entry, toc_style))
    
    elements.append(PageBreak())
    
    # Add content pages
    elements.extend(create_second_page(styles, personal_info))
    elements.append(PageBreak())
    
    # Add ESG scores chart if available
    if 'esg_scores' in summary_data:
        create_esg_score_charts(summary_data['esg_scores'], styles, elements)
    
    # Add main content
    for i, (title, content) in enumerate(section_data):
        elements.append(Paragraph(title, styles['heading']))
        process_content(content, styles, elements)
        if i < len(section_data) - 1:
            elements.append(PageBreak())
    
    # Add disclaimer
    elements.append(NextPageTemplate('dis'))
    elements.append(PageBreak())
    create_disclaimer_page(styles, elements)
    
    # Add back cover
    # elements.append(NextPageTemplate('Cover'))
    # elements.append(PageBreak())
    # if os.path.exists("backemma.png"):
    #     img = Image("backemma.png", width=letter[0], height=letter[1])
    #     elements.append(img)
    
    # Build the PDF
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if hasattr(self, '_pageNumber'):
            self.setFont("Helvetica", 9)


def process_content(content, styles, elements):
    """Process content with improved table detection and formatting"""
    if not content:
        return
    
    # Split content into sections
    sections = content.split('\n\n')
    in_table = False
    table_data = []
    
    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Check if this section contains a table
        if any('|' in line for line in lines):
            # Process table content
            table_data = []
            for line in lines:
                if '|' in line and '-|-' not in line:  # Skip separator lines
                    cells = [cell.strip() for cell in line.split('|')]
                    # Remove empty cells from start/end
                    cells = [cell for cell in cells if cell]
                    if cells:  # Only add non-empty rows
                        table_data.append(cells)
            
            if table_data:
                # Create and format table
                table = create_formatted_table(table_data, styles)
                elements.append(Spacer(1, 0.2*inch))
                elements.append(table)
                elements.append(Spacer(1, 0.2*inch))
            continue
        
        # Process non-table content
        for line in lines:
            if line.strip():
                elements.append(Paragraph(line.strip(), styles['content']))
                elements.append(Spacer(1, 0.1*inch))

    return elements


def create_disclaimer_page(styles, elements):
    """Create a single-page disclaimer using Lato font family"""
    
    # Register Lato fonts
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        # Fallback to Helvetica if Lato fonts are not available
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
    
    # Define custom styles for the disclaimer page with Lato
    disclaimer_styles = {
        'title': ParagraphStyle(
            'DisclaimerTitle',
            parent=styles['normal'],
            fontSize=24,
            fontName=bold_font,
            leading=28,
            spaceBefore=0,
            spaceAfter=10,
        ),
        'section_header': ParagraphStyle(
            'SectionHeader',
            parent=styles['normal'],
            fontSize=11,
            fontName=bold_font,
            leading=13,
            spaceBefore=2,
            spaceAfter=3,
        ),
        'body_text': ParagraphStyle(
            'BodyText',
            parent=styles['normal'],
            fontSize=9,
            fontName=base_font,
            leading=10,
            spaceBefore=1,
            spaceAfter=3,
            alignment=TA_JUSTIFY,
        ),
        'item_header': ParagraphStyle(
            'ItemHeader',
            parent=styles['normal'],
            fontSize=9,
            fontName=bold_font,
            leading=11,
            spaceBefore=4,
            spaceAfter=1,
        ),
        'confidential': ParagraphStyle(
            'Confidential',
            parent=styles['normal'],
            fontSize=8,
            fontName=base_font,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceBefore=1,
        )
    }    
    # Main Content
    elements.append(Paragraph("Limitations of AI in Financial and Strategic Evaluations", 
                            disclaimer_styles['section_header']))

    # AI Limitations Section
    limitations = [
        ("1. Data Dependency and Quality",
         "AI models rely heavily on the quality and completeness of the data fed into them. The accuracy of the analysis is contingent upon the integrity of the input data. Inaccurate, outdated, or incomplete data can lead to erroneous conclusions and recommendations. Users should ensure that the data used in AI evaluations is accurate and up-to-date."),
        
        ("2. Algorithmic Bias and Limitations",
         "AI algorithms are designed based on historical data and predefined models. They may inadvertently incorporate biases present in the data, leading to skewed results. Additionally, AI models might not fully capture the complexity and nuances of human behavior or unexpected market changes, potentially impacting the reliability of the analysis."),
        
        ("3. Predictive Limitations",
         "While AI can identify patterns and trends, it cannot predict future events with certainty. Financial markets and business environments are influenced by numerous unpredictable factors such as geopolitical events, economic fluctuations, and technological advancements. AI's predictions are probabilistic and should not be construed as definitive forecasts."),
        
        ("4. Interpretation of Results",
         "AI-generated reports and analyses require careful interpretation. The insights provided by AI tools are based on algorithms and statistical models, which may not always align with real-world scenarios. It is essential to involve human expertise in interpreting AI outputs and making informed decisions."),
        
        ("5. Compliance and Regulatory Considerations",
         "The use of AI in financial evaluations and business strategy formulation must comply with relevant regulations and standards. Users should be aware of legal and regulatory requirements applicable to AI applications in their jurisdiction and ensure that their use of AI tools aligns with these requirements.")
    ]

    for title, content in limitations:
        elements.append(Paragraph(title, disclaimer_styles['item_header']))
        elements.append(Paragraph(content, disclaimer_styles['body_text']))

    # RAA Capital Partners Section
    elements.append(Paragraph("RAA Capital Partners Sdn Bhd and Advisory Partners' Disclaimer",
                            disclaimer_styles['section_header']))

    elements.append(Paragraph(
        "RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners provide AI-generated reports and insights as a tool to assist in financial and business strategy evaluations. However, the use of these AI-generated analyses is subject to the following disclaimers:",
        disclaimer_styles['body_text']
    ))

    disclaimers = [
        ("1. No Guarantee of Accuracy or Completeness",
         "While RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners strive to ensure that the AI-generated reports and insights are accurate and reliable, we do not guarantee the completeness or accuracy of the information provided. The insights are based on the data and models used, which may not fully account for all relevant factors or changes in the market."),
        
        ("2. Not Financial or Professional Advice",
         "The AI-generated reports and insights are not intended as financial, investment, legal, or professional advice. Users should consult with qualified professionals before making any financial or strategic decisions based on AI-generated reports. RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners are not responsible for any decisions made based on the reports provided."),
        
        ("3. Limitation of Liability",
         "RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners shall not be liable for any loss or damage arising from the use of AI-generated reports and insights. This includes, but is not limited to, any direct, indirect, incidental, or consequential damages resulting from reliance on the reports or decisions made based on them."),
        
        ("4. No Endorsement of Third-Party Tools",
         "The use of third-party tools and data sources in AI evaluations is at the user's discretion. RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners do not endorse or guarantee the performance or accuracy of any third-party tools or data sources used in conjunction with the AI-generated reports.")
    ]

    for title, content in disclaimers:
        elements.append(Paragraph(title, disclaimer_styles['item_header']))
        elements.append(Paragraph(content, disclaimer_styles['body_text']))


def clean_text(text):
    """Clean and format text by removing unwanted formatting while preserving structure"""
    if not text:
        return ""
    
    # Remove style and HTML tags
    text = re.sub(r'<userStyle>.*?</userStyle>', '', text)
    text = re.sub(r'<br\s*/?>|<para>|</para>', ' ', text)  # Replace <br>, <para> tags with space
    text = re.sub(r'<[^>]+>', '', text)  # Remove any other HTML tags
    
    # Remove Markdown formatting while preserving structure
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'_(.*?)_', r'\1', text)        # Underscore
    
    # Improve spacing around punctuation
    text = re.sub(r':(?!\s)', ': ', text)         # Add space after colons
    text = re.sub(r'\s+([.,;!?])', r'\1', text)   # Remove space before punctuation
    text = re.sub(r'([.,;!?])(?!\s)', r'\1 ', text)  # Add space after punctuation
    
    # Handle headers while preserving hierarchy
    text = re.sub(r'^#{1,6}\s*(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Handle bullet points
    text = re.sub(r'^\s*-\s*', '• ', text, flags=re.MULTILINE)
    
    # Preserve paragraph structure
    paragraphs = text.split('\n\n')
    paragraphs = [' '.join(p.split()) for p in paragraphs]
    text = '\n\n'.join(paragraphs)
    
    # Remove any remaining <userStyle>Normal</userStyle> tags
    text = text.replace('<userStyle>Normal</userStyle>', '')
    
    return text.strip()

def create_formatted_table(table_data, styles):
    """Create a professionally formatted table with consistent styling"""
    # Ensure all rows have the same number of columns
    max_cols = max(len(row) for row in table_data)
    table_data = [row + [''] * (max_cols - len(row)) for row in table_data]
    
    # Calculate dynamic column widths based on content length
    total_width = 6.5 * inch
    col_widths = []
    
    if max_cols > 1:
        # Calculate max content length for each column
        col_lengths = [0] * max_cols
        for row in table_data:
            for i, cell in enumerate(row):
                content_length = len(str(cell))
                col_lengths[i] = max(col_lengths[i], content_length)
                
        # Distribute widths proportionally based on content length
        total_length = sum(col_lengths)
        for length in col_lengths:
            width = max((length / total_length) * total_width, inch)  # Minimum 1 inch
            col_widths.append(width)
            
        # Adjust widths to fit page
        scale = total_width / sum(col_widths)
        col_widths = [w * scale for w in col_widths]
    else:
        col_widths = [total_width]
    
    # Create table with calculated widths
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Define table style commands
    style_commands = [
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        
        # Content styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2B6CB0')),
        
        # Alignment
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Cell padding
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]
    
    # Apply style commands
    table.setStyle(TableStyle(style_commands))
    
    # Apply word wrapping
    wrapped_data = []
    for i, row in enumerate(table_data):
        wrapped_row = []
        for cell in row:
            if isinstance(cell, (str, int, float)):
                # Use content style for all cells except headers
                style = styles['subheading'] if i == 0 else styles['content']
                wrapped_cell = Paragraph(str(cell), style)
            else:
                wrapped_cell = cell
            wrapped_row.append(wrapped_cell)
        wrapped_data.append(wrapped_row)
    
    # Create final table with wrapped data
    final_table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
    final_table.setStyle(TableStyle(style_commands))
    
    return final_table

def create_highlight_box(text, styles):
    """Create a highlighted box with improved styling"""
    content = Paragraph(f"• {text}", styles['content'])
    
    table = Table(
        [[content]],
        colWidths=[6*inch],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('BORDER', (0,0), (-1,-1), 1, colors.black),
            ('PADDING', (0,0), (-1,-1), 15),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOX', (0,0), (-1,-1), 2, colors.HexColor('#E2E8F0')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 18),
            ('TOPPADDING', (0,0), (-1,-1), 18),
        ])
    )
    
    return table

def process_table_content(lines, styles, elements):
    """Process table content with improved header handling"""
    table_data = []
    header_processed = False
    
    for line in lines:
        if '-|-' in line:  # Skip separator lines
            continue
            
        cells = [cell.strip() for cell in line.split('|')]
        cells = [cell for cell in cells if cell]
        
        if cells:
            # Handle cells with bold markers
            cells = [re.sub(r'\*\*(.*?)\*\*', r'\1', cell) for cell in cells]
            
            # Create paragraphs with appropriate styles
            if not header_processed:
                cells = [Paragraph(str(cell), styles['subheading']) for cell in cells]
                header_processed = True
            else:
                cells = [Paragraph(str(cell), styles['content']) for cell in cells]
                
            table_data.append(cells)
    
    if table_data:
        elements.append(Spacer(1, 0.2*inch))
        table = create_formatted_table(table_data, styles)
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
def create_custom_styles():
    base_styles = getSampleStyleSheet()
    
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Italic', 'fonts/Lato-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-BoldItalic', 'fonts/Lato-BoldItalic.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'

    custom_styles = {}
    
    # Normal style (both capitalized and lowercase versions)
    custom_styles['Normal'] = ParagraphStyle(
        'Normal',
        parent=base_styles['Normal'],
        fontSize=10,
        leading=12,
        fontName=base_font,
        alignment=TA_JUSTIFY
    )
    
    custom_styles['normal'] = custom_styles['Normal']  # Add lowercase version
    
    # TOC style
    custom_styles['TOCEntry'] = ParagraphStyle(
        'TOCEntry',
        parent=base_styles['Normal'],
        fontSize=12,
        leading=16,
        leftIndent=20,
        fontName=base_font,
        alignment=TA_JUSTIFY
    )
    
    custom_styles['toc'] = custom_styles['TOCEntry']  # Add lowercase version
    
    # Title style
    custom_styles['title'] = ParagraphStyle(
        'CustomTitle',
        parent=custom_styles['Normal'],  # Changed parent to our custom Normal
        fontSize=24,
        textColor=colors.HexColor('#2B6CB0'),
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName=bold_font,
        leading=28.8
    )
    
    # Heading style
    custom_styles['heading'] = ParagraphStyle(
        'CustomHeading',
        parent=custom_styles['Normal'],  # Changed parent to our custom Normal
        fontSize=26,
        textColor=colors.HexColor('#1a1a1a'),
        spaceBefore=20,
        spaceAfter=15,
        fontName=bold_font,
        leading=40.5,
        alignment=TA_JUSTIFY
    )
    
    # Subheading style
    custom_styles['subheading'] = ParagraphStyle(
        'CustomSubheading',
        parent=custom_styles['Normal'],  # Changed parent to our custom Normal
        fontSize=12,
        textColor=colors.HexColor('#4A5568'),
        spaceBefore=15,
        spaceAfter=10,
        fontName=bold_font,
        leading=18.2,
        alignment=TA_JUSTIFY
    )
    
    # Content style
    custom_styles['content'] = ParagraphStyle(
        'CustomContent',
        parent=custom_styles['Normal'],  # Changed parent to our custom Normal
        fontSize=10,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_JUSTIFY,
        spaceBefore=6,
        spaceAfter=6,
        fontName=base_font,
        leading=15.4
    )
    
    # Bullet style
    custom_styles['bullet'] = ParagraphStyle(
        'CustomBullet',
        parent=custom_styles['Normal'],  # Changed parent to our custom Normal
        fontSize=10,
        textColor=colors.HexColor('#1a1a1a'),
        leftIndent=20,
        firstLineIndent=0,
        fontName=base_font,
        leading=15.4,
        alignment=TA_JUSTIFY
    )
    
    # Add any additional required style variations
    custom_styles['BodyText'] = custom_styles['Normal']
    custom_styles['bodytext'] = custom_styles['Normal']
    
    return custom_styles

def process_content(content, styles, elements):
    """Process content with markdown-style heading detection"""
    if not content:
        return
    
    # Split content into sections
    sections = content.split('\n')
    current_paragraph = []
    
    i = 0
    while i < len(sections):
        line = sections[i].strip()
        
        # Skip empty lines
        if not line:
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                elements.append(Paragraph(para_text, styles['content']))  # Changed from 'normal' to 'content'
                elements.append(Spacer(1, 0.1*inch))
                current_paragraph = []
            i += 1
            continue
        
        # Handle headings
        if line.startswith('###') and not line.startswith('####'):
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                elements.append(Paragraph(para_text, styles['content']))  # Changed from 'normal' to 'content'
                current_paragraph = []
            
            heading_text = line.replace('###', '').strip()
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(heading_text, styles['subheading']))
            elements.append(Spacer(1, 0.15*inch))
            
        elif line.startswith('####'):
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                elements.append(Paragraph(para_text, styles['content']))  # Changed from 'normal' to 'content'
                current_paragraph = []
            
            subheading_text = line.replace('####', '').strip()
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(subheading_text, styles['subheading']))
            elements.append(Spacer(1, 0.1*inch))
            
        # Handle tables
        elif '|' in line:
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                elements.append(Paragraph(para_text, styles['content']))  # Changed from 'normal' to 'content'
                current_paragraph = []
            
            # Collect table lines
            table_lines = [line]
            while i + 1 < len(sections) and '|' in sections[i + 1]:
                i += 1
                table_lines.append(sections[i].strip())
            
            # Process table
            if table_lines:
                process_table_content(table_lines, styles, elements)
                
        else:
            # Handle bold text and normal content
            processed_line = line
            if '**' in processed_line:
                processed_line = re.sub(r'\*\*(.*?)\*\*', lambda m: f'<b>{m.group(1)}</b>', processed_line)
            
            current_paragraph.append(processed_line)
        
        i += 1
    
    # Handle any remaining paragraph content
    if current_paragraph:
        para_text = ' '.join(current_paragraph)
        elements.append(Paragraph(para_text, styles['content']))  # Changed from 'normal' to 'content'
        elements.append(Spacer(1, 0.1*inch))
    
    return elements

def process_table_content(lines, styles, elements):
    """Process table content with improved header handling"""
    table_data = []
    header_processed = False
    
    for line in lines:
        if '-|-' in line:  # Skip separator lines
            continue
            
        cells = [cell.strip() for cell in line.split('|')]
        cells = [cell for cell in cells if cell]
        
        if cells:
            # Handle cells with bold markers
            cells = [re.sub(r'\*\*(.*?)\*\*', r'\1', cell) for cell in cells]
            
            if not header_processed:
                cells = [Paragraph(str(cell), styles['subheading']) for cell in cells]
                header_processed = True
            else:
                cells = [Paragraph(str(cell), styles['content']) for cell in cells]
            table_data.append(cells)
    
    if table_data:
        elements.append(Spacer(1, 0.2*inch))
        table = create_formatted_table(table_data, styles)
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))

def process_paragraph(para, styles, elements):
    """Process individual paragraph with enhanced formatting"""
    clean_para = clean_text(para)
    if not clean_para:
        return
    
    # Handle bulleted lists
    if clean_para.startswith(('•', '-', '*', '→')):
        text = clean_para.lstrip('•-*→ ').strip()
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['content'],
            leftIndent=20,
            firstLineIndent=0,
            spaceBefore=6,
            spaceAfter=6,
            bulletIndent=10,
            bulletFontName='Symbol'
        )
        elements.append(Paragraph(f"• {text}", bullet_style))
        elements.append(Spacer(1, 0.05*inch))
    
    # Handle numbered points
    elif re.match(r'^\d+\.?\s+', clean_para):
        text = re.sub(r'^\d+\.?\s+', '', clean_para)
        elements.extend([
            Spacer(1, 0.1*inch),
            create_highlight_box(text, styles),
            Spacer(1, 0.1*inch)
        ])
    
    # Handle quoted text
    elif clean_para.strip().startswith('"') and clean_para.strip().endswith('"'):
        quote_style = ParagraphStyle(
            'Quote',
            parent=styles['content'],
            fontSize=11,
            leftIndent=30,
            rightIndent=30,
            spaceBefore=12,
            spaceAfter=12,
            leading=16,
            textColor=colors.HexColor('#2D3748'),
            borderColor=colors.HexColor('#E2E8F0'),
            borderWidth=1,
            borderPadding=10,
            borderRadius=5
        )
        elements.append(Paragraph(clean_para, quote_style))
        elements.append(Spacer(1, 0.1*inch))
    
    # Handle section titles
    elif re.match(r'^[A-Z][^.!?]*:$', clean_para):
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(clean_para, styles['subheading']))
        elements.append(Spacer(1, 0.1*inch))
    
    # Handle special metrics or scores
    elif "Overall Score:" in clean_para or re.match(r'^[\d.]+%|[$€£¥][\d,.]+', clean_para):
        metric_style = ParagraphStyle(
            'Metric',
            parent=styles['content'],
            fontSize=11,
            textColor=colors.HexColor('#2B6CB0'),
            spaceAfter=6
        )
        elements.append(Paragraph(clean_para, metric_style))
    
    # Regular paragraphs
    else:
        elements.append(Paragraph(clean_para, styles['content']))
        elements.append(Spacer(1, 0.05*inch))
def create_second_page(styles, company_info):
    elements = []
    report_id = str(uuid.uuid4())[:8]
    
    elements.append(Spacer(1, 0.5*inch))
    
    title_table = Table(
        [[Paragraph("Company Profile Analysis", styles['heading'])]],
        colWidths=[7*inch],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ])
    )
    elements.append(title_table)
    
    elements.append(Spacer(0.5, 0.1*inch))
    
    # Create info table
    info_table = Table(
        [
            [Paragraph("Business Profile", styles['subheading'])],
            [Table(
                [
                    ["Company Name", str(company_info.get('name', 'N/A'))],
                    ["Industry", str(company_info.get('industry', 'N/A'))],
                    ["Contact Person", str(company_info.get('full_name', 'N/A'))],
                    ["Mobile Number", str(company_info.get('mobile_number', 'N/A'))],
                    ["Email", str(company_info.get('email', 'N/A'))],
                    ["Report Date", str(company_info.get('date', 'N/A'))],
                    ["Status / ID", f"POC | ID: {report_id}"]
                ],
                colWidths=[1.5*inch, 4.5*inch],
                style=TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ])
            )]
        ],
        colWidths=[6*inch],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ])
    )
    
    elements.append(info_table)
    return elements

def scale_image_to_fit(image_path, max_width, max_height):
    """Scale image to fit within maximum dimensions while maintaining aspect ratio."""
    from PIL import Image as PILImage
    import os
    
    if not os.path.exists(image_path):
        return None
        
    try:
        img = PILImage.open(image_path)
        img_width, img_height = img.size
        
        # Calculate scaling factor
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale = min(width_ratio, height_ratio)
        
        new_width = img_width * scale
        new_height = img_height * scale
        
        return new_width, new_height
    except Exception as e:
        print(f"Error scaling image: {str(e)}")
        return None

def create_front_page(styles, org_info):
    """Create a front page using a full-page cover image with text overlay."""
    elements = []
    
    if os.path.exists("frontemma.jpg"):
        # Create a template for the first page
        def first_page(canvas, doc):
            canvas.saveState()
            
            # Draw the background image
            canvas.drawImage(
                "frontemma.jpg",
                0, 0,
                width=letter[0],
                height=letter[1],
                preserveAspectRatio=True
            )
            
            # Add text overlay
            canvas.setFillColorRGB(1, 1, 1)  # White text
            canvas.setFont("Helvetica-Bold", 36)
            
            # Center the title text
            title_text = "ESG Assessment Report"
            title_width = canvas.stringWidth(title_text, "Helvetica-Bold", 36)
            x_position = (letter[0] - title_width) / 2
            canvas.drawString(x_position, letter[1] - 3*inch, title_text)
            
            # Add organization name
            canvas.setFont("Helvetica", 24)
            org_text = f"Organization: {org_info['organization_name']}"
            org_width = canvas.stringWidth(org_text, "Helvetica", 24)
            x_position = (letter[0] - org_width) / 2
            canvas.drawString(x_position, letter[1] - 4*inch, org_text)
            
            # Add date
            canvas.setFont("Helvetica", 18)
            date_text = f"Date: {org_info['date']}"
            date_width = canvas.stringWidth(date_text, "Helvetica", 18)
            x_position = (letter[0] - date_width) / 2
            canvas.drawString(x_position, letter[1] - 4.5*inch, date_text)
            
            canvas.restoreState()
            
        # Create a PageTemplate that uses our custom first page layout
        first_page_template = PageTemplate(
            id='FirstPage',
            frames=[Frame(0, 0, letter[0], letter[1], id='normal')],
            onPage=first_page
        )
        elements.append(NextPageTemplate('FirstPage'))
        elements.append(Spacer(1, letter[1]))  # Add a full-page spacer
        
    else:
        # Fallback content if image is missing
        elements.extend([
            Spacer(1, 2*inch),
            Paragraph("ESG Assessment Report", styles['title']),
            Spacer(1, 1*inch),
            Paragraph(f"Organization: {org_info['organization_name']}", styles['content']),
            Paragraph(f"Date: {org_info['date']}", styles['content'])
        ])
    
    return elements

def create_header_footer(canvas, doc):
    """Add header and footer with adjustments for positioning text, logos, and images."""
    canvas.saveState()
    
    # Register Lato fonts if available
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        # Fallback to Helvetica if Lato fonts are not available
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
    
    if doc.page > 1:  # Only show on pages after the first page
        # Adjust position for top-right logos
        x_start = doc.width + doc.leftMargin - 0.5 * inch  # Shift logos slightly to the right
        y_position = doc.height + doc.topMargin - 0.1 * inch
        image_width = 0.5 * inch
        image_height = 0.5 * inch

        # Draw logos
        if os.path.exists("badea.jpg"):
            canvas.drawImage(
                "badea.jpg", 
                x_start, 
                y_position, 
                width=250, 
                height=image_height, 
                mask="auto"
            )
        
        
        # Add contact person name
        canvas.setFont(base_font, 12)
        canvas.drawString(
            doc.leftMargin,
            doc.height + doc.topMargin - 0.03 * inch,  # Higher position for name
            f"{doc.personal_info.get('full_name', '') if hasattr(doc, 'personal_info') else ''}"
        )
        
        # Add company name below
        canvas.setFont(base_font, 16)
        canvas.drawString(
            doc.leftMargin,
            doc.height + doc.topMargin - 0.25 * inch,  # Lower position for company
            f"{doc.company_name if hasattr(doc, 'company_name') else ''}"
        )
        
        # Adjust line position to be below both texts
        line_y_position = doc.height + doc.topMargin - 0.45 * inch
        canvas.setLineWidth(0.5)
        canvas.line(
            doc.leftMargin,
            line_y_position,
            doc.width + doc.rightMargin,
            line_y_position
        )
        
        # Footer - Add image beside text
        # footer_image_path =   # Replace with your image file
        # footer_image_width = 0.5 * inch
        # footer_image_height = 0.5 * inch
        # footer_image_x = doc.leftMargin  # Align to the left margin
        # footer_image_y = 0.5 * inch - footer_image_height / 2  # Match Y-axis with page number

        # Draw the footer image
        # if os.path.exists(footer_image_path):
        #     canvas.drawImage(
        #         footer_image_path,
        #         footer_image_x,
        #         footer_image_y,
        #         width=footer_image_width,
        #         height=footer_image_height,
        #         mask="auto"
        #     )
        
        # Add "Generated on" text aligned with page number
        footer_text_x =0.2 * inch  # Space after the image
        footer_text_y = 0.4 * inch  # Align with page number
        canvas.setFont(base_font, 9)
        canvas.drawString(
            footer_text_x,
            footer_text_y,
            f"Generated on {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        )
        
        # Add page number on the right
        canvas.drawRightString(
            doc.width + doc.rightMargin,
            0.4 * inch,  # Align with the footer text
            f"Page {doc.page}"
        )
    canvas.restoreState()

def create_header_footer_disclaimer(canvas, doc):
    """Add header and footer with smaller, transparent images in the top right and a line below the header."""
    canvas.saveState()
    
    # Register Lato fonts if available
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        # Fallback to Helvetica if Lato fonts are not available
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
    
    if doc.page > 1:  # Only show on pages after the first page
        # Adjust the position to the top right
        x_start = doc.width + doc.leftMargin - 1.0 * inch
        y_position = doc.height + doc.topMargin - 0.1 * inch
        image_width = 0.5 * inch
        image_height = 0.5 * inch

        # Draw images
        images = ["ceai.png", "raa.png", "emma.png"]
        for i, img in enumerate(images):
            if os.path.exists(img):
                canvas.drawImage(
                    img, 
                    x_start - i * (image_width + 0.1 * inch),
                    y_position, 
                    width=image_width, 
                    height=image_height, 
                    mask="auto"
                )
        
        # Add Header Text
        canvas.setFont(bold_font, 27)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 0.1*inch, 
                         "Disclaimer")

        # Draw line below the header text
        line_y_position = doc.height + doc.topMargin - 0.30 * inch
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, line_y_position, doc.width + doc.rightMargin, line_y_position)

        # Footer
        # footer_image_path = "raa.png"  # Replace with your image file
        # footer_image_width = 0.5 * inch
        # footer_image_height = 0.5 * inch
        # footer_image_x = doc.leftMargin  # Align to the left margin
        # footer_image_y = 0.5 * inch - footer_image_height / 2  # Match Y-axis with page number

        # # Draw the footer image
        # if os.path.exists(footer_image_path):
        #     canvas.drawImage(
        #         footer_image_path,
        #         footer_image_x,
        #         footer_image_y,
        #         width=footer_image_width,
        #         height=footer_image_height,
        #         mask="auto"
        #     )
        
        # Add "Generated on" text aligned with page number
        footer_text_x = 0.2 * inch  # Space after the image
        footer_text_y = 0.4 * inch  # Align with page number
        canvas.setFont(base_font, 9)
        canvas.drawString(
            footer_text_x,
            footer_text_y,
            f"Generated on {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        )
        canvas.drawRightString(doc.width + doc.rightMargin, 0.5 * inch, 
                             f"Page {doc.page}")
    
    canvas.restoreState()
def get_esg_analysis1(user_data, api_key):
    """Initial ESG analysis based on profile"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on this organization's profile and ESG readiness responses:
    {user_data}
    
    Provide a 635-word analysis with specific references to the data provided, formatted
    in narrative form with headers and paragraphs.NO NUMBERING POINTS 
    -Must be in paragph form """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting initial analysis: {str(e)}")
        return None

def get_esg_analysis2(user_data, finance_data, api_key):
    """Get organization-specific ESG recommendations with international standards, and focus on Middle East, and African Nation."""
    import json
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    user_data_str = json.dumps(user_data, indent=2)

    # ESG frameworks for various organization types with international, Dubai, Saudi, and Africa focus
    prompts = {
        "Public Listed Company": [
            "Dubai Financial Market ESG Reporting Guide",
            "UAE Corporate Governance Rules",
            "Saudi Exchange ESG Disclosure Guidelines",
            "Africa Corporate Sustainability Standards",
            "Global Reporting Initiative (GRI)",
            "Task Force on Climate-related Financial Disclosures (TCFD)",
            "Sustainability Accounting Standards Board (SASB)",
            "UN Global Compact",
            "CDP (formerly Carbon Disclosure Project)",
            "International Sustainability Standards Board (ISSB)",
        ],
        "Financial Institution": [
            "Dubai Financial Services Authority (DFSA) Guidelines",
            "UAE Central Bank ESG Guidelines",
            "Saudi Arabian Monetary Authority (SAMA) ESG Guidelines",
            "Africa Responsible Investment Framework",
            "Principles for Responsible Banking (PRB)",
            "Equator Principles",
            "TCFD Framework",
            "UNEP FI Guidelines",
            "Islamic Finance ESG Framework",
            "IFC Performance Standards",
        ],
        "SME/Enterprise": [
            "Dubai SME ESG Toolkit",
            "UAE SME Council Guidelines",
            "Saudi Vision 2030 SME Sustainability Goals",
            "Africa SME Development ESG Guidelines",
            "Dubai Chamber Sustainability Network",
            "ISO 14001",
            "B Corp Standards",
            "UN Global Compact SME Guidelines",
            "GRI Standards for SMEs",
        ],
        "Government Agency": [
            "UAE Vision 2030",
            "Dubai Sustainable City Initiative",
            "Saudi Green Initiative",
            "Africa Agenda 2063",
            "United Nations Sustainable Development Goals (SDGs)",
            "UAE Government Excellence System",
            "Smart Dubai Framework",
            "GRI Public Sector Standards",
        ],
        "NGO": [
            "Global Reporting Initiative (GRI)",
            "AccountAbility AA1000 Series",
            "INGO Accountability Charter",
            "Dubai Cares Framework",
            "Saudi ESG Philanthropy Standards",
            "Africa Social Investment Framework",
            "UAE CSR Fund Guidelines",
            "Social Value International (SVI)",
        ],
        "Others": [
            "UN Global Compact",
            "ISO 26000",
            "Sustainability Development Goals (SDGs)",
            "UAE ESG Guidelines",
            "Dubai Sustainable Finance Framework",
            "Saudi Corporate Governance Regulations",
            "Africa ESG Reporting Toolkit",
            "ESG Disclosure Guidance for Companies Listed on ADX",
        ],
    }

    # Get organization types from user_data
    org_types = user_data.get("organization_types", [])
    if not org_types:
        org_types = ["Others"]  # Default to Others if no type is specified
    
    # Create a section for each selected organization type
    org_type_sections = []
    all_frameworks = []  # To track unique frameworks across all types
    
    for org_type in org_types:
        frameworks = prompts.get(org_type, prompts["Others"])

        for framework in frameworks:
            if framework not in all_frameworks:
                all_frameworks.append(framework)
        org_type_sections.append(f"""
Organization Type: {org_type}
Relevant Frameworks:
{chr(10).join('- ' + framework for framework in frameworks)}
""")

    # Create the full prompt with sections for each organization type
    full_prompt = f"""
As an ESG consultant specializing in international standards with expertise in Middle East, and Africa Nation frameworks, provide a comprehensive analysis for an organization with multiple classifications:

Organization Profile:
{user_data_str}

Financial Profile:
{finance_data}

This organization operates under multiple classifications:
{chr(10).join(org_type_sections)}

Please provide:
1. A detailed analysis of how each framework applies to this specific organization, with special attention to UAE/Dubai, Saudi Arabia, and Africa requirements
2. Areas of overlap between international and local frameworks that create synergies
3. Potential conflicts or challenges in implementing multiple framework requirements across jurisdictions

Write in narrative form (450 words) with headers and Numbering points (no bullet points), including:
- Provide a forward looking quote in 30 words highlighting the key aspects of this section and the strategic implications in layman terms with "".
- Supporting facts and figures from global, Middle East  and African markets
- Specific references for each organization type
- Cross-framework integration strategies considering local and international requirements
- Implementation recommendations aligned with Middle East vision 2030, and Africa Nation Agenda 2063

*Model Illustration*
-Create a summary table with a basic explanation based on the above (must be in table format)

Focus on practical implementation while acknowledging the complexity of managing multiple frameworks in an international context with regional compliance."""

    # Process the prompt with OpenAI's API
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting ESG analysis: {str(e)}"
def get_esg_analysis3(user_data, finance_data, api_key):
    """Get organization-specific ESG recommendations with international standards, and focus on Middle East, and African Nation."""
    import json
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    user_data_str = json.dumps(user_data, indent=2)

    # ESG frameworks for various organization types with international, Dubai, Saudi, and Africa focus
    prompts = {
        "Public Listed Company": [
            "Dubai Financial Market ESG Reporting Guide",
            "UAE Corporate Governance Rules",
            "Saudi Exchange ESG Disclosure Guidelines",
            "Africa Corporate Sustainability Standards",
            "Global Reporting Initiative (GRI)",
            "Task Force on Climate-related Financial Disclosures (TCFD)",
            "Sustainability Accounting Standards Board (SASB)",
            "UN Global Compact",
            "CDP (formerly Carbon Disclosure Project)",
            "International Sustainability Standards Board (ISSB)",
        ],
        "Financial Institution": [
            "Dubai Financial Services Authority (DFSA) Guidelines",
            "UAE Central Bank ESG Guidelines",
            "Saudi Arabian Monetary Authority (SAMA) ESG Guidelines",
            "Africa Responsible Investment Framework",
            "Principles for Responsible Banking (PRB)",
            "Equator Principles",
            "TCFD Framework",
            "UNEP FI Guidelines",
            "Islamic Finance ESG Framework",
            "IFC Performance Standards",
        ],
        "SME/Enterprise": [
            "Dubai SME ESG Toolkit",
            "UAE SME Council Guidelines",
            "Saudi Vision 2030 SME Sustainability Goals",
            "Africa SME Development ESG Guidelines",
            "Dubai Chamber Sustainability Network",
            "ISO 14001",
            "B Corp Standards",
            "UN Global Compact SME Guidelines",
            "GRI Standards for SMEs",
        ],
        "Government Agency": [
            "UAE Vision 2030",
            "Dubai Sustainable City Initiative",
            "Saudi Green Initiative",
            "Africa Agenda 2063",
            "United Nations Sustainable Development Goals (SDGs)",
            "UAE Government Excellence System",
            "Smart Dubai Framework",
            "GRI Public Sector Standards",
        ],
        "NGO": [
            "Global Reporting Initiative (GRI)",
            "AccountAbility AA1000 Series",
            "INGO Accountability Charter",
            "Dubai Cares Framework",
            "Saudi ESG Philanthropy Standards",
            "Africa Social Investment Framework",
            "UAE CSR Fund Guidelines",
            "Social Value International (SVI)",
        ],
        "Others": [
            "UN Global Compact",
            "ISO 26000",
            "Sustainability Development Goals (SDGs)",
            "UAE ESG Guidelines",
            "Dubai Sustainable Finance Framework",
            "Saudi Corporate Governance Regulations",
            "Africa ESG Reporting Toolkit",
            "ESG Disclosure Guidance for Companies Listed on ADX",
        ],
    }

    # Get organization types from user_data
    org_types = user_data.get("organization_types", [])
    if not org_types:
        org_types = ["Others"]  # Default to Others if no type is specified
    
    # Create a section for each selected organization type
    org_type_sections = []
    all_frameworks = []  # To track unique frameworks across all types
    
    for org_type in org_types:
        frameworks = prompts.get(org_type, prompts["Others"])

        for framework in frameworks:
            if framework not in all_frameworks:
                all_frameworks.append(framework)
        org_type_sections.append(f"""
Organization Type: {org_type}
Relevant Frameworks:
{chr(10).join('- ' + framework for framework in frameworks)}
""")

    # Create the full prompt with sections for each organization type
    full_prompt = f"""
As an ESG consultant specializing in international standards with expertise in Middle East, and Africa Nation frameworks, provide a comprehensive analysis for an organization with multiple classifications:

Organization Profile:
{user_data_str}

Financial Profile:
{finance_data}

This organization operates under multiple classifications:
{chr(10).join(org_type_sections)}

Please provide:

1. Recommendations for prioritizing and harmonizing framework implementation in the Middle East and African Nation contexts
2. Specific examples of how the organization can benefit from its multi-framework approach while maintaining compliance with regional regulations

Write in narrative form (450 words) with headers and Numbering points (no bullet points), including:
- Provide a forward looking quote in 30 words highlighting the key aspects of this section and the strategic implications in layman terms with "".
- Supporting facts and figures from global, Middle East  and African markets
- Specific references for each organization type
- Cross-framework integration strategies considering local and international requirements
- Implementation recommendations aligned with Middle East vision 2030, and Africa Nation Agenda 2063

*Model Illustration*
-Create a summary table with a basic explanation based on the above (must be in table format)

Focus on practical implementation while acknowledging the complexity of managing multiple frameworks in an international context with regional compliance."""

    # Process the prompt with OpenAI's API
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting ESG analysis: {str(e)}"

def generate_management_questions(analysis1, analysis2,analysis3, api_key):
    """Generate top 10 management issues/questions"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on the previous analyses:
    {analysis1}
    {analysis2}
    {analysis3}
    
    Generate a list of top 10 issues/questions that Management should address in numbering Points.
    Format as  650-words in narrative form with:
    - Clear headers for key areas
    - Bullet points identifying specific issues
    - Supporting facts and figures
    - Industry-specific references"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7  # Increased token limit
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating management questions: {str(e)}")
        return None

def generate_question_rationale(questions, analysis1, analysis2,analysis3, api_key):
    """Generate rationale for management questions"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on these management issues and previous analyses:
    {questions}
    {analysis1}
    {analysis2}
    {analysis3}
    
    Provide a 680-word (no numbering points)explanation of why each issue needs to be addressed, with:
    - Specific references to ESG guidelines and standards
    - Industry best practices
    - Supporting facts and figures
    - Framework citations

    *Model Illustration*
    -Create a summary table with a basic explanation based on the above(must be in table format)
    The content should be concise (around 600 words) with supporting facts and specific reference, with Model Illustration and outcomes presented clearly in a table.
"""

    

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating management questions: {str(e)}")
        return None

def generate_implementation_challenges(analysis1, analysis2,analysis3, questions, api_key):
    """Generate implementation challenges analysis"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on the previous analyses:
    {analysis1}
    {analysis2}
    {analysis3}
    {questions}
    
    Provide bullet points analysis of potential ESG implementation challenges covering:
    1. Human Capital Availability and Expertise
    2. Budgeting and Financial Resources
    3. Infrastructure
    4. Stakeholder Management
    5. Regulatory Compliance
    6. Other Challenges

    *Model Illustration*
    -Create a summary table with a basic explanation based on the above(must be in table format)

    The content should be concise (around 600 words) with supporting facts and specific reference, with Model Illustration and outcomes presented clearly in a table.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating challenges analysis: {str(e)}")
        return None
def generate_advisory_analysis(user_data, all_analyses, api_key):
    """Generate advisory plan and SROI model"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on all previous analyses:
    {user_data}
    {all_analyses}
    
     (480 words): Explain what and how ESG Advisory team can assist in numbering points, including:
    - Implementation support methods
    - Technical expertise areas
    - Training programs
    - Monitoring systems

    *Model Illustration*
    -Create a summary table with a basic explanation based on the above(must be in table format)
    
    Include supporting facts, figures, and statistical references."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating advisory and SROI analysis: {str(e)}")
        return None
def generate_sroi_analysis(user_data, all_analyses, api_key):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on all previous analyses:
    {user_data}
    {all_analyses}
    
*Task*: Create a Social Return on Investment (SROI) TABLE with the following components. The company is for arab banking:

1. *Calculation Methodology*:  
   - Explain SROI calculations in simple, narrative language.  
   
2. *Financial Projections*:  
 
-Create a table to display findings in a table for clarity.  


3. *Implementation Guidelines*:  
   - Provide step-by-step guidance in numbered points.  
   - Use clear, descriptive text without special characters or symbols.  

4. *Model Illustration*:  
   - Develop a realistic example of an SROI model based on hypothetical assumptions. 
   - Create a table to summarize the overall impact across these components(must be in table format).  

The content should be concise (around 600 words), with financial projections and outcomes presented clearly in a table."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating advisory and SROI analysis: {str(e)}")
        return None
    
def generate_summary(user_data, all_analyses, api_key):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    As an ESG consultant specializing in Malaysian standards and frameworks:
    Based on all previous analyses:
    {user_data}
    {all_analyses}
    
*Task*: Create a summary paragraph in narrative form in about 600 words based on the previous analysis and provide recommended actions.
-must be in paragraph form """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

def render_header():
    """Render application header"""
    col1, col2 = st.columns([3, 1])
    with col1:
        logo_path = "blank.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
    with col2:
        logo_path = "badea.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, width=250)
def get_nested_value(data, field):
    """Helper function to safely get nested dictionary values"""
    if isinstance(field, list):
        # Handle nested fields
        temp = data
        for key in field:
            if isinstance(temp, dict):
                temp = temp.get(key, "N/A")
            else:
                return "N/A"
        return temp
    else:
        # Handle single fields
        return data.get(field, "N/A")
import streamlit as st
import pandas as pd
import altair as alt

def calculate_esg_readiness_scores(esg_responses):
    """
    Calculate ESG readiness scores from questionnaire responses
    Returns overall and category-specific scores on a 1-5 scale
    """
    # [Previous scoring_map code remains the same]
    scoring_map = {
        "1. Have you started formal ESG initiatives within your organization?": {
            "No, we haven't started yet.": 1,
            "Yes, we've started basic efforts but lack a structured plan.": 2,
            "Yes, we have a formalized ESG framework in place.": 3,
            "Yes, we are actively implementing and reporting ESG practices.": 4,
            "Yes, practices are monitored, tracked to work towards our ESG goals.": 5
        },
        "2. What is your primary reason for considering ESG initiatives?": {
            "To regularise because of sanctions imposed by regulators":1,
            "To comply with regulations and avoid penalties.": 2,
            "To improve reputation and meet stakeholder demands.": 3,
            "To attract investors or access green funding.": 4,
            "To align with broader sustainability and ethical goals.": 5
        },
        "3. Do you have a team or individual responsible for ESG in your organization?": {
            "No, there is no one currently assigned to ESG matters.": 1,
            "Yes, but they are not exclusively focused on ESG.": 2,
            "Yes, we have a dedicated ESG team or officer.": 3,
            "Yes, and we also involve external advisors for support.": 4,
            "There is a framework with top-down board involvement.": 5
        },
        "4. Are you aware of the ESG standards relevant to your industry?": {
            "No, I am unfamiliar with industry-specific ESG standards.": 1,
            "I've heard of them but don't fully understand how to apply them.": 2,
            "Yes, I am somewhat familiar and have started researching.": 3,
            "Yes, and we have begun aligning our operations with these standards.": 4,
            "Have full frameworks for compliance with all required standards.": 5
        },
        "5. Do you currently measure your environmental or social impacts?": {
            "No, we have not started measuring impacts.": 1,
            "Yes, we measure basic indicators (e.g., waste, energy use).": 2,
            "Yes, we measure basic Scope1/Scope2 and less than 2 parameters S3 with no tracking system.": 3,
            "Yes, we track a range of metrics but need a better system.": 4,
            "Yes, we have comprehensive metrics with detailed reports.": 5
        },
        "6. What is your biggest challenge in starting or scaling ESG initiatives?": {
            "Lack of knowledge, awareness and expertise.": 1,
            "Insufficient budget and resources.": 2,
            "No ESG Culture": 3,
            "Difficulty aligning ESG goals with business priorities.": 4,
            "Regulatory complexity and compliance requirements.": 5
        },
        "7. Carbon Footprint/GHG Protocol": {
            "No carbon footprint calculations.": 1,
            "Scope 1/Scope 2 internally available - not published.": 2,
            "Scope 1/Scope 2 published - websites etc.": 3,
            "Working towards targets for carbon footprint reduction.": 4,
            "Aligned with international guidelines (under guidelines of GHG Protocol, SDG Goals etc).": 5
        },
        "8. Other parameters": {
            "No detailed parameter calculations.": 1,
            "Scope 1/Scope 2 internally available - not published.": 2,
            "Scope 1/Scope 2 published - websites etc.": 3,
            "Working towards targets for carbon footprint reduction.": 4,
            "Aligned with international guidelines (under guidelines of GHG Protocol, SDG Goals etc).": 5
        },
        "9. Social": {
            "No detailed parameter calculations.": 1,
            "Minimum compliance, penalized from regulatory bodies in past 3 years.": 2,
            "Compliant with local/international human rights/labour law compliance standards.": 3,
            "Compliant - no sanctions, detailed parameters (Diversity numbers, Employee participation, Inclusion policies published online).": 4,
            "As above, having received compliance recognition from regulatory bodies.": 5
        },
        "10. Governance": {
            "No ESG dedicated team.": 1,
            "Very basic governance.": 2,
            "Governance policies (ABC, Code of Conduct) published in website.": 3,
            "Very comprehensive policy with dedicated ESG head.": 4,
            "Governance aligned with international standard practices.": 5
        }
    }
    
    # Calculate scores
    scores = []
    category_scores = {
        'Strategic Readiness': [], # Questions 1-3
        'Understanding & Measurement': [], # Questions 4-6
        'Implementation & Reporting': [], # Questions 7-8
        'Social & Governance': [] # Questions 9-10
    }
    
    for question, answer in esg_responses.items():
        if question in scoring_map and answer in scoring_map[question]:
            score = scoring_map[question][answer]
            scores.append(score)
            
            # Add to appropriate category
            if question.startswith(('1.', '2.', '3.')):
                category_scores['Strategic Readiness'].append(score)
            elif question.startswith(('4.', '5.', '6.')):
                category_scores['Understanding & Measurement'].append(score)
            elif question.startswith(('7.', '8.')):
                category_scores['Implementation & Reporting'].append(score)
            elif question.startswith(('9.', '10.')):
                category_scores['Social & Governance'].append(score)
    
    # Calculate averages
    overall_score = sum(scores) / len(scores) if scores else 0
    category_averages = {
        category: sum(scores) / len(scores) if scores else 0
        for category, scores in category_scores.items()
    }

    # Calculate readiness level
    def get_readiness_level(score):
        if score < 1.5:
            return "Initial Stage"
        elif score < 2.5:
            return "Developing"
        elif score < 3.5:
            return "Established"
        elif score < 4.5:
            return "Advanced"
        else:
            return "Leading"
    
    readiness_level = get_readiness_level(overall_score)
    
    return {
        'overall_score': overall_score,
        'readiness_level': readiness_level,
        'category_scores': category_averages,
        'individual_scores': dict(zip(esg_responses.keys(), scores))
    }

def display_esg_readiness_scores(scores):
    """
    Display ESG readiness scores using Streamlit and Altair
    """
    # Create columns for the overall assessment dashboard
    st.markdown("### Overall ESG Assessment Dashboard")
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        st.metric(
            label="Overall Score",
            value=f"{scores['overall_score']:.2f}/5.0",
            delta=None
        )
    
    with metric_cols[1]:
        st.metric(
            label="Readiness Level",
            value=scores['readiness_level'],
            delta=None
        )
    
    with metric_cols[2]:
        # Calculate percentage score
        percentage = (scores['overall_score'] / 5) * 100
        st.metric(
            label="ESG Maturity",
            value=f"{percentage:.1f}%",
            delta=None
        )
    
    st.markdown("---")
    
    # Create two columns for charts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Original category chart
        chart_data = pd.DataFrame({
            'Category': list(scores['category_scores'].keys()),
            'Score': list(scores['category_scores'].values())
        })
        
        category_chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Category:N', title='Categories'),
            y=alt.Y('Score:Q', 
                   scale=alt.Scale(domain=[0, 5]), 
                   title='Score (1-5)'),
            color=alt.value('#1F77B4'),
            tooltip=['Category', 'Score']
        ).properties(
            title='Category Assessment Scores',
            height=400
        )
        
        st.altair_chart(category_chart, use_container_width=True)
    
    with col2:
        # Score interpretation
        st.markdown("### Score Interpretation")
        st.markdown("""
        - **1.0-1.5:** Initial Stage
        - **1.6-2.5:** Developing
        - **2.6-3.5:** Established
        - **3.6-4.5:** Advanced
        - **4.6-5.0:** Leading
        """)
    
    # Add detailed questionnaire dashboard
    st.markdown("### Detailed Question Analysis")
    
    # Prepare data for detailed question analysis
    question_data = []
    for question, score in scores['individual_scores'].items():
        # Extract question number and shorten question text
        q_num = question.split('.')[0]
        q_text = ' '.join(question.split()[1:])[:50] + "..." if len(' '.join(question.split()[1:])) > 50 else ' '.join(question.split()[1:])
        question_data.append({
            'Question Number': q_num,
            'Question': q_text,
            'Score': score
        })
    
    df_questions = pd.DataFrame(question_data)
    
    # # Create detailed question chart
    # question_chart = alt.Chart(df_questions).mark_bar().encode(
    #     x=alt.X('Question Number:N', title='Question'),
    #     y=alt.Y('Score:Q', scale=alt.Scale(domain=[0, 5]), title='Rating'),
    #     color=alt.value('#2B6CB0'),
    #     tooltip=['Question', 'Score']
    # ).properties(
    #     title='Question-wise Assessment Scores',
    #     height=300
    # )
    
    # st.altair_chart(question_chart, use_container_width=True)
    
    # Display detailed scores table
    st.markdown("### Detailed Scores")
    
    # Format detailed scores for display
    detailed_scores = pd.DataFrame({
        'Question': list(scores['individual_scores'].keys()),
        'Score': list(scores['individual_scores'].values())
    })
    detailed_scores['Score'] = detailed_scores['Score'].round(2)
    
    st.dataframe(
        detailed_scores,
        hide_index=True,
        column_config={
            "Question": st.column_config.TextColumn("Question"),
            "Score": st.column_config.NumberColumn(
                "Score",
                format="%.2f",
                min_value=1,
                max_value=5
            )
        }
    )
def main():
    st.set_page_config(page_title="ESG Starter's Kit", layout="wide")
    st.title("ESG Starter's Kit")
    render_header()

    with st.sidebar:
        api_key = st.text_input("Enter Secret Key:", type="password")
        if not api_key:
            st.warning("Please enter your Secret key to continue.")
            return
        
        # Add navigation in sidebar if analyses are available
        if 'analysis1' in st.session_state:
            st.markdown("### View Analyses")
            if st.button("Initial ESG Analysis"):
                st.session_state.show_analysis = 'analysis1'
            if 'analysis2' in st.session_state and st.button("Framework Analysis"):
                st.session_state.show_analysis = 'analysis2'
            if 'analysis3' in st.session_state and st.button("Framework Implementation"):
                st.session_state.show_analysis = 'analysis3'
            if 'management_questions' in st.session_state and st.button("Management Issues"):
                st.session_state.show_analysis = 'management_questions'
            if 'implementation_challenges' in st.session_state and st.button("Implementation Challenges"):
                st.session_state.show_analysis = 'implementation_challenges'
            if 'advisory' in st.session_state and st.button("Advisory Plan"):
                st.session_state.show_analysis = 'advisory'
            if 'sroi' in st.session_state and st.button("SROI Analysis"):
                st.session_state.show_analysis = 'sroi'

    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0

    # Define steps
    steps = [
        "Organization Profile",
        "Financial Check",
        "ESG Assessment",
        "Framework Selection",
        "Management Issues",
        "Implementation Challenges",
        "Advisory Plan",
        "Report Generation"
    ]

    # Show progress
    current = st.session_state.current_step
    progress_text = f"Step {current + 1} of {len(steps)}: {steps[current]}"
    st.progress((current)/(len(steps)-1), text=progress_text)

    # Show selected analysis if any
    if hasattr(st.session_state, 'show_analysis'):
        analysis_titles = {
            'analysis1': "Initial ESG Analysis",
            'analysis2': "Framework Analysis",
            'analysis3': "Framework Implementation",
            'management_questions': "Management Issues",
            'implementation_challenges': "Implementation Challenges",
            'advisory': "Advisory Plan",
            'sroi': "SROI Analysis"
        }
        
        with st.expander(f"View {analysis_titles[st.session_state.show_analysis]}", expanded=True):
            st.markdown(st.session_state[st.session_state.show_analysis])
        
        if st.button("Continue with Assessment"):
            delattr(st.session_state, 'show_analysis')
            st.rerun()
        return

    # Organization Profile (Step 0)
    if st.session_state.current_step == 0:
        st.write("## Organization Profile")
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name")
                mobile_number = st.text_input("Mobile Number")
            with col2:
                email = st.text_input("Email Address")
                organization_name = st.text_input("Organization Name")
            
            industry = st.selectbox("Industry", FIELDS_OF_INDUSTRY)
            if industry == "Others":
                other_industry = st.text_input("Please specify your industry")
            
            core_activities = st.text_area("Describe your organization's core activities")
            
            submit = st.form_submit_button("Continue to Financial Check")
            
            if submit:
                if not all([full_name, mobile_number, email, organization_name, industry, core_activities]):
                    st.error("Please fill in all required fields.")
                else:
                    st.session_state.user_data = {
                        "full_name": full_name,
                        "email": email,
                        "mobile_number": mobile_number,
                        "organization_name": organization_name,
                        "industry": other_industry if industry == "Others" else industry,
                        "core_activities": core_activities,
                        "date": datetime.datetime.now().strftime('%B %d, %Y')
                    }
                    st.session_state.current_step = 1
                    st.rerun()

    # Financial Check (Step 1)
    elif st.session_state.current_step == 1:
        show_success_states(1)
        
        st.write("## Financial Check")
        with st.form("financial_check_form"):
            tab1, tab2, tab3, tab4 = st.tabs([
                "General Information", 
                "Financial Readiness",
                "Market & Operations",
                "Impact Assessment"
            ])

            with tab1:
                st.subheader("1. General Information")
                country = st.selectbox("Where is the company located? *", COMPANY_LOCATIONS)
                project_name = st.text_input("Project/Business Name *")
                business_nature = st.selectbox("Nature of Business *", BUSINESS_NATURE)
                
                col1, col2 = st.columns(2)
                with col1:
                    project_cost = st.selectbox("Total Project Cost *", PROJECT_COST_RANGES)
                    financing_request = st.selectbox("Financing Request Amount *", PROJECT_COST_RANGES)
                with col2:
                    start_date = st.date_input("Project Start Date *")
                    end_date = st.date_input("Project End Date *")
                
                project_objectives = st.text_area("Project Objectives and Goals *")

            with tab2:
                st.subheader("2. Financial Readiness")
                col1, col2 = st.columns(2)
                with col1:
                    self_funding = st.selectbox("Self-funding Percentage *", SELF_FUNDING_RANGES)
                    financial_projection = st.radio("Financial Projection Available *", FINANCIAL_PROJECTION)
                with col2:
                    expected_revenue = st.selectbox("Expected Revenue *", REVENUE_RANGES)
                    break_even = st.selectbox("Break-even Period *", BREAK_EVEN_PERIODS)
                
                col3, col4 = st.columns(2)
                with col3:
                    other_debts = st.radio("Other Debts/Loans *", ["Yes", "No"])
                with col4:
                    contingency_plan = st.radio("Cost Overrun Contingency Plan *", ["Yes", "No"])

            with tab3:
                st.subheader("3. Market & Operations")
                col1, col2 = st.columns(2)
                with col1:
                    target_market = st.selectbox("Target Market *", ["Local", "Regional", "Global"])
                    market_demand = st.selectbox("Market Demand *", ["High", "Medium", "Low"])
                with col2:
                    market_study = st.radio("Market Study Conducted *", ["Yes", "No"])
                    existing_contracts = st.radio("Existing Customers/Contracts *", ["Yes", "No"])
                
                competitors = st.text_area("Key Competitors and Market Position *")

            with tab4:
                st.subheader("4. Impact Assessment")
                job_creation = st.selectbox("Job Creation Potential *", JOB_CREATION_RANGES)
                community_benefit = st.selectbox("Community Benefit Percentage *", COMMUNITY_BENEFIT_RANGES)
                local_economy = st.multiselect("Local Economy Impact *", LOCAL_ECONOMY_IMPACTS)
                sdg_alignment = st.multiselect("SDG Alignment *", SDG_OPTIONS)

            st.markdown("*Required fields are marked with an asterisk (*)")
            submit = st.form_submit_button("Continue to ESG Assessment")
            
            if submit:
                # Validate all required fields
                required_fields = {
                    "Country": country,
                    "Project Name": project_name,
                    "Business Nature": business_nature,
                    "Project Cost": project_cost,
                    "Financing Request": financing_request,
                    "Start Date": start_date,
                    "End Date": end_date,
                    "Project Objectives": project_objectives,
                    "Self Funding": self_funding,
                    "Financial Projection": financial_projection,
                    "Expected Revenue": expected_revenue,
                    "Break Even": break_even,
                    "Other Debts": other_debts,
                    "Contingency Plan": contingency_plan,
                    "Target Market": target_market,
                    "Market Demand": market_demand,
                    "Market Study": market_study,
                    "Existing Contracts": existing_contracts,
                    "Competitors": competitors,
                    "Job Creation": job_creation,
                    "Community Benefit": community_benefit
                }
                
                # Check for empty fields
                empty_fields = [field for field, value in required_fields.items() 
                                if not value or value == "" or 
                                (isinstance(value, str) and value.strip() == "")]
                
                # Check for empty multiselect fields
                if not local_economy:
                    empty_fields.append("Local Economy Impact")
                if not sdg_alignment:
                    empty_fields.append("SDG Alignment")
                
                if empty_fields:
                    st.error(f"Please fill in all required fields: {', '.join(empty_fields)}")
                else:
                    # Store the financial data
                    financial_data = {
                        "country": country,
                        "project_name": project_name,
                        "business_nature": business_nature,
                        "project_objectives": project_objectives,
                        "project_cost": project_cost,
                        "financing_request": financing_request,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "self_funding": self_funding,
                        "financial_projection": financial_projection,
                        "expected_revenue": expected_revenue,
                        "break_even": break_even,
                        "other_debts": other_debts,
                        "contingency_plan": contingency_plan,
                        "target_market": target_market,
                        "market_demand": market_demand,
                        "market_study": market_study,
                        "existing_contracts": existing_contracts,
                        "competitors": competitors,
                        "job_creation": job_creation,
                        "community_benefit": community_benefit,
                        "local_economy": local_economy,
                        "sdg_alignment": sdg_alignment
                    }
                    st.session_state.financial_check_responses = financial_data
                    st.session_state.current_step = 2
                    st.rerun()

    # ESG Assessment (Step 2)
    elif st.session_state.current_step == 2:
        show_success_states(2)
        
        with st.expander("View Financial Overview", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Project Cost", st.session_state.financial_check_responses['project_cost'])
            with col2:
                st.metric("Self Funding", st.session_state.financial_check_responses['self_funding'])
            with col3:
                st.metric("Expected Revenue", st.session_state.financial_check_responses['expected_revenue'])
            with col4:
                st.metric("Break Even", st.session_state.financial_check_responses['break_even'])
        
        st.write("## ESG Assessment")
        with st.form("esg_form"):
            st.subheader("ESG Readiness Assessment")
            esg_responses = {}
            
            categories = {
                "Strategic Readiness": list(ESG_READINESS_QUESTIONS.items())[:3],
                "Understanding & Measurement": list(ESG_READINESS_QUESTIONS.items())[3:6],
                "Implementation & Reporting": list(ESG_READINESS_QUESTIONS.items())[6:8],
                "Social & Governance": list(ESG_READINESS_QUESTIONS.items())[8:]
            }
            
            for category, questions in categories.items():
                st.write(f"### {category}")
                for question, options in questions:
                    response = st.radio(question, options, index=None)
                    if response:
                        esg_responses[question] = response
                st.markdown("---")
            
            submit = st.form_submit_button("Continue to Framework Selection")
            
            if submit:
                if len(esg_responses) != len(ESG_READINESS_QUESTIONS):
                    st.error("Please answer all ESG readiness questions.")
                else:
                    st.session_state.user_data["esg_responses"] = esg_responses
                    scores = calculate_esg_readiness_scores(esg_responses)
                    st.session_state.esg_scores = scores
                    
                    with st.spinner("Analyzing ESG readiness..."):
                        st.session_state.analysis1 = get_esg_analysis1(
                            {**st.session_state.user_data, 'esg_scores': scores}, 
                            api_key
                        )
                    st.session_state.current_step = 3
                    st.rerun()

    # Framework Selection (Step 3)
    elif st.session_state.current_step == 3:
        show_success_states(3)
        
        # Show ESG scores visualization
        st.write("### ESG Assessment Results")
        display_esg_readiness_scores(st.session_state.esg_scores)
        
        st.write("## Framework Selection")
        st.write("Select applicable frameworks based on your organization type:")
        
        selected_types = []
        custom_frameworks = ""
        
        for org_type in ORGANIZATION_TYPES:
            if st.checkbox(org_type, key=f"org_type_{org_type}"):
                selected_types.append(org_type)
                if org_type == "Others":
                    custom_frameworks = st.text_area(
                        "Specify your frameworks (one per line)",
                        help="Enter each framework on a new line"
                    )

        if st.button("Continue to Management Issues"):
            if not selected_types:
                st.error("Please select at least one organization type.")
            else:
                st.session_state.user_data["organization_types"] = selected_types
                if "Others" in selected_types and custom_frameworks:
                    st.session_state.user_data["other_frameworks"] = [
                        f.strip() for f in custom_frameworks.split('\n') if f.strip()
                    ]
                
                with st.spinner("Analyzing framework selection..."):
                    st.session_state.analysis2 = get_esg_analysis2(
                        st.session_state.user_data,
                        st.session_state.financial_check_responses,
                        api_key
                    )
                    st.session_state.analysis3 = get_esg_analysis3(
                        st.session_state.user_data,
                        st.session_state.financial_check_responses,
                        api_key
                    )
                st.session_state.current_step = 4
                st.rerun()

    # Management Issues (Step 4)
    elif st.session_state.current_step == 4:
        show_success_states(4)
        
        st.write("## Management Issues Analysis")
        with st.spinner("Analyzing management issues..."):
            st.session_state.management_questions = generate_management_questions(
                st.session_state.analysis1,
                st.session_state.analysis2,
                st.session_state.analysis3,
                api_key
            )
            
            # Show Management Issues Analysis
            st.markdown(st.session_state.management_questions)
        
        if st.button("Continue to Implementation Challenges"):
            st.session_state.current_step = 5
            st.rerun()

    # Implementation Challenges (Step 5)
    elif st.session_state.current_step == 5:
        show_success_states(5)
        
        st.write("## Implementation Challenges")
        with st.spinner("Analyzing implementation challenges..."):
            st.session_state.implementation_challenges = generate_implementation_challenges(
                st.session_state.analysis1,
                st.session_state.analysis2,
                st.session_state.analysis3,
                st.session_state.management_questions,
                api_key
            )
            
            # Show Implementation Challenges
            st.markdown(st.session_state.implementation_challenges)
        
        if st.button("Continue to Advisory Plan"):
            st.session_state.current_step = 6
            st.rerun()

    # Advisory Plan (Step 6)
    elif st.session_state.current_step == 6:
        show_success_states(6)
        
        st.write("## Advisory Plan and SROI Analysis")
        with st.spinner("Generating advisory plan and SROI analysis..."):
# Advisory Plan (Step 6) continued...
            all_analyses = {
                'analysis1': st.session_state.analysis1,
                'analysis2': st.session_state.analysis2,
                'analysis3': st.session_state.analysis3,
                'management_questions': st.session_state.management_questions,
                'implementation_challenges': st.session_state.implementation_challenges,
                'esg_scores': st.session_state.esg_scores
            }
            
            # Generate advisory plan
            st.session_state.advisory = generate_advisory_analysis(
                st.session_state.user_data,
                all_analyses,
                api_key
            )
            
            # Generate SROI analysis
            st.session_state.sroi = generate_sroi_analysis(
                st.session_state.user_data,
                all_analyses,
                api_key
            )
            
            # Generate executive summary
            st.session_state.summary = generate_summary(
                st.session_state.user_data,
                all_analyses,
                api_key
            )
            
            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["Advisory Plan", "SROI Analysis", "Executive Summary"])
            
            with tab1:
                st.markdown("### Advisory Plan")
                st.markdown(st.session_state.advisory)
            
            with tab2:
                st.markdown("### SROI Analysis")
                st.markdown(st.session_state.sroi)
            
            with tab3:
                st.markdown("### Executive Summary")
                st.markdown(st.session_state.summary)
        
        if st.button("Proceed to Report Generation"):
            st.session_state.current_step = 7
            st.rerun()

    # Report Generation (Step 7)
    elif st.session_state.current_step == 7:
        show_success_states(7)
        st.write("## Final Report Generation")
        
        # Create tabs for reviewing different sections
        tab1, tab2, tab3 = st.tabs(["Review Analysis", "Preview Reports", "Generate & Send"])
        
        with tab1:
            st.write("### Review All Analyses")
            
            analyses = {
                "Initial ESG Analysis": "analysis1",
                "Framework Analysis": "analysis2",
                "Framework Implementation": "analysis3",
                "Management Issues": "management_questions",
                "Implementation Challenges": "implementation_challenges",
                "Advisory Plan": "advisory",
                "SROI Analysis": "sroi",
                "Executive Summary": "summary"
            }
            
            for title, key in analyses.items():
                with st.expander(title, expanded=False):
                    if key in st.session_state:
                        st.markdown(st.session_state[key])
                    else:
                        st.warning(f"{title} not yet generated")
        
        with tab2:
            st.write("### Preview Report Sections")
            
            # Show organization profile
            with st.expander("Organization Profile", expanded=False):
                st.json(st.session_state.user_data)
            
            # Show financial check responses
            with st.expander("Financial Check", expanded=False):
                st.json(st.session_state.financial_check_responses)
            
            # Show ESG scores
            with st.expander("ESG Assessment Scores", expanded=False):
                display_esg_readiness_scores(st.session_state.esg_scores)
        
        with tab3:
            st.write("### Generate and Send Reports")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("#### Report Recipients")
                additional_email = st.text_input(
                    "Additional Email Recipients (comma-separated)",
                    help="Leave empty to send only to primary contact"
                )
            
            with col2:
                st.write("#### Report Options")
                include_summary = st.checkbox("Include Executive Summary", value=True)
                include_detailed = st.checkbox("Include Detailed Report", value=True)
                include_excel = st.checkbox("Include Excel Data", value=True)

            if st.button("📄 Generate and Email Reports", type="primary"):
                try:
                    with st.spinner("Generating and sending reports..."):
                        # Prepare data
                        esg_data = {
                            'analysis1': st.session_state.analysis1,
                            'analysis2': st.session_state.analysis2,
                            'analysis3': st.session_state.analysis3,
                            'management_questions': st.session_state.management_questions,
                            'implementation_challenges': st.session_state.implementation_challenges,
                            'advisory': st.session_state.advisory,
                            'sroi': st.session_state.sroi
                        }
                        
                        summary_data = {
                            'analysis1': st.session_state.analysis1,
                            'esg_scores': st.session_state.esg_scores,
                            'summary': st.session_state.summary
                        }
                        
                        personal_info = {
                            'name': st.session_state.user_data['organization_name'],
                            'industry': st.session_state.user_data['industry'],
                            'full_name': st.session_state.user_data['full_name'],
                            'mobile_number': st.session_state.user_data['mobile_number'],
                            'email': st.session_state.user_data['email'],
                            'date': st.session_state.user_data['date']
                        }
                        
                        # Generate reports based on selected options
                        attachments = []
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
                        
                        if include_detailed:
                            pdf_buffer = generate_pdf(esg_data, personal_info, [4, 7, 11, 15, 18, 21])
                            attachments.append((pdf_buffer, f"esg_assessment_{timestamp}.pdf", "application/pdf"))
                        
                        if include_summary:
                            pdf_buffer2 = generate_pdf_summary(summary_data, personal_info, [6, 7, 8, 11, 13, 15])
                            attachments.append((pdf_buffer2, f"esg_starterkit_{timestamp}.pdf", "application/pdf"))
                        
                        if include_excel:
                            excel_buffer = generate_excel_report(st.session_state.user_data)
                            attachments.append((excel_buffer, f"esg_input_data_{timestamp}.xlsx", 
                                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
                        
                        # Send email to primary recipient
                        email_sent = send_email_with_attachments(
                            receiver_email=personal_info['email'],
                            organization_name=personal_info['name'],
                            subject="ESG Assessment Report",
                            body=f"""Dear {personal_info['full_name']},

Thank you for using our ESG Assessment service. Please find attached your ESG Assessment Report package for {personal_info['name']}.

Report Generation Date: {personal_info['date']}

Best regards,
ESG Assessment Team""",
                            attachments=attachments
                        )
                        
                        # Send to additional recipients if specified
                        if additional_email:
                            additional_emails = [email.strip() for email in additional_email.split(',')]
                            for email in additional_emails:
                                send_email_with_attachments(
                                    receiver_email=email,
                                    organization_name=personal_info['name'],
                                    subject="ESG Assessment Report",
                                    body=f"""ESG Assessment Report for {personal_info['name']}

Report Generation Date: {personal_info['date']}

Best regards,
ESG Assessment Team""",
                                    attachments=attachments
                                )
                        
                        if email_sent:
                            st.success("Reports generated and sent successfully!")
                            
                            # Provide download buttons
                            st.write("### Download Reports")
                            cols = st.columns(len(attachments))
                            for i, (buffer, filename, mime_type) in enumerate(attachments):
                                with cols[i]:
                                    st.download_button(
                                        f"📥 Download {filename.split('_')[0].title()}",
                                        data=buffer,
                                        file_name=filename,
                                        mime=mime_type
                                    )
                        else:
                            st.error("Failed to send emails. Please try again or contact support.")
                            
                except Exception as e:
                    st.error(f"Error generating and sending reports: {str(e)}")
                    logging.error(f"Detailed error: {str(e)}", exc_info=True)
def show_success_states(current_step):
    """
    Display success messages for completed steps
    
    Args:
        current_step (int): The current step number in the process
    """
    # Map of steps to their success messages
    step_messages = {
        1: "Profile Completed",
        2: "Profile and Financial Check Completed",
        3: "Profile, Financial Check, and ESG Assessment Completed",
        4: "Profile, Financial Check, ESG Assessment, and Framework Selection Completed",
        5: "Profile, Financial Check, ESG Assessment, Framework Selection, and Management Issues Completed",
        6: "Profile, Financial Check, ESG Assessment, Framework Selection, Management Issues, and Implementation Challenges Completed",
        7: "All Previous Steps Completed"
    }
    
    # Display success messages for completed steps
    for step in range(1, current_step + 1):
        if step in step_messages:
            message = step_messages[step]
            
            # Create columns for better visual organization
            if step == current_step:
                # For the current step, show the message more prominently
                st.success(message)
            else:
                # For previous steps, show in a more compact format
                st.success(f"Step {step} Completed")
    
    # Add a separator after success messages
    if current_step > 0:
        st.markdown("---")
if __name__ == "__main__":
    main()
