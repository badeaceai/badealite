import streamlit as st
import PyPDF2
import json
import base64
from datetime import datetime
from openai import OpenAI
from typing import Dict, Any, List
import tiktoken
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from html import unescape
import os
import requests
from PIL import Image as PILImage
from typing import Union, Optional
import io

def process_multiple_images(image_files, client: OpenAI) -> str:
    """Process multiple image inputs and combine their descriptions for analysis."""
    try:
        combined_description = []
        
        for idx, image_file in enumerate(image_files, 1):
            # Read and encode image
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Get image description using GPT-4 Vision
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Describe image {idx} in detail, focusing on key business and strategic aspects. Include all relevant details, numbers, and observations that could be important for board-level analysis. If financial data exists, please include time references and periods of which they incur as part of the analysis"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            
            # Reset file pointer for future use
            image_file.seek(0)
            
            # Add image description to the combined list
            description = response.choices[0].message.content
            combined_description.append(f"Image {idx} Analysis:\n{description}\n")
        
        # Combine all descriptions with clear separation
        return "\n\n".join(combined_description)
    except Exception as e:
        st.error(f"Error processing images: {str(e)}")
        return ""

def process_input_content(input_type: str, uploaded_files, text_input: str, client: OpenAI) -> str:
    """Process any type of input and return text content for analysis."""
    try:
        if input_type == "PDF Document" and uploaded_files:
            return read_pdf(uploaded_files) or ""
        elif input_type == "Images" and uploaded_files:  # Note the plural "Images"
            try:
                # Display all uploaded images
                for image_file in uploaded_files:
                    image = PILImage.open(image_file)
                    st.image(image, caption=f"Uploaded Image: {image_file.name}", use_container_width=True)
                    image_file.seek(0)  # Reset file pointer after displaying
                
                # Process all images together
                return process_multiple_images(uploaded_files, client)
            except Exception as e:
                st.error(f"Error processing images: {str(e)}")
                return ""
        elif input_type == "Text Input" and text_input:
            return text_input
        return ""
    except Exception as e:
        st.error(f"Error processing input: {str(e)}")
        return ""
def process_image_input(image_file, client: OpenAI) -> str:
    """Process image input and convert to text description for analysis."""
    try:
        # Read and encode image
        image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Get image description using GPT-4 Vision
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image in detail, focusing on key business and strategic aspects. Include all relevant details, numbers, and observations that could be important for board-level analysis.if financial data exists, please include time references and periods of which they incur as part of the analysis"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096
        )
        
        # Reset file pointer for future use
        image_file.seek(0)
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return ""


def download_and_register_fonts():
    """Download and register required fonts"""
    font_urls = {
        'Lato-Regular': "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf",
        'Lato-Bold': "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf"
    }
    
    for font_name, url in font_urls.items():
        font_path = f"{font_name}.ttf"
        try:
            if not os.path.exists(font_path):
                response = requests.get(url)
                with open(font_path, 'wb') as f:
                    f.write(response.content)
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception as e:
            st.error(f"Error loading font {font_name}: {str(e)}")

def create_styles() -> Dict[str, ParagraphStyle]:
    """Create styles using reliable system fonts for Streamlit cloud environment"""
    styles = {
        'title': ParagraphStyle(
            'CustomTitle',
            fontName='Helvetica-Bold',  # Using standard Helvetica instead of Lato
            fontSize=16,
            spaceAfter=20,
            textColor=colors.black,
            leading=20
        ),
        'header': ParagraphStyle(
            'CustomHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=10,
            textColor=colors.black,
            leading=18
        ),
        'subheading': ParagraphStyle(
            'CustomSubheading',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.black,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        ),
        'content': ParagraphStyle(
            'CustomContent',
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.black,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        ),
        'metadata': ParagraphStyle(
            'CustomMetadata',
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.black,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        )
    }
    return styles
def create_styled_pdf_report(result: Dict[str, Any], analysis_type: str) -> bytes:
    """Create a styled PDF report with proper table handling"""
    buffer = BytesIO()
    
    try:
        # Download and register fonts
        download_and_register_fonts()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=25*mm,
            leftMargin=25*mm,
            topMargin=25*mm,
            bottomMargin=25*mm
        )
        
        # Get styles
        styles = create_styles()
        
        # Initialize elements list
        elements = []
        
        # Add logo if available
        try:
            logo_path = "badea.jpeg"
            if os.path.exists(logo_path):
                img = Image(logo_path, width=220, height=40)
                elements.append(img)
                elements.append(Spacer(1, 20))
        except:
            pass
        REPORT_TITLES = {
            'whats_happening': 'Situational Analysis',
            'what_could_happen': 'Scenario Insight Summary',
            'why_this_happens': 'Possible Causes',
            'what_should_board_consider': 'Strategic Implications & Board Recommendations',
            # Include variations without underscores and with spaces
            'whats happening': 'Situational Analysis',
            'what could happen': 'Scenario Insight Summary',
            'why this happens': 'Possible Causes',
            'what should board consider': 'Strategic Implications & Board Recommendations',
            # Include variations without spaces
            'whatshappening': 'Situational Analysis',
            'whatcouldhappen': 'Scenario Insight Summary',
            'whythishappens': 'Possible Causes',
            'whatshouldboardconsider': 'Strategic Implications & Board Recommendations'
        }
        elements.append(Spacer(1, 20))
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=colors.gray,
            alignment=1,  # Center alignment
            leading=10
        )
        disclaimer_text = (
            "Disclaimer: This analysis is provided for informational purposes only and "
            "should not be considered as financial, legal, or investment advice. "
            "The content is generated using artificial intelligence and may require verification. "
            "Users should exercise their own judgment and consult appropriate professionals "
            "before making any decisions based on this information. "
            "© BADEA © CEAI All rights reserved."
        )
        
        # Then modify the title section to use this mapping
        title_text = REPORT_TITLES.get(analysis_type, f"Analysis Report: {analysis_type.replace('_', ' ').title()}")
        # Add title
        # title_text = f"Board Analysis Report: {analysis_type.replace('_', ' ').title()}"
        elements.append(Paragraph(title_text, styles['title']))

        # Add metadata
        metadata_text = f"Generated on: {result.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}"
        elements.append(Paragraph(metadata_text, styles['metadata']))
        elements.append(Spacer(1, 20))
        
        # Process content
        analysis_text = result.get('analysis', '')
        if analysis_text:
            # Split content into sections
            sections = re.split(r'(?:\*\*|#)\s*(.*?)(?:\*\*|$)', analysis_text)
            
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                    
                if i % 2 == 0:  # Content
                    elements.extend(process_content_section(section, styles))
                else:  # Header
                    elements.append(Spacer(1, 12))
                    elements.append(Paragraph(section.strip(), styles['header']))
                    elements.append(Spacer(1, 8))

        elements.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return b''
    finally:
        buffer.close()
def create_formatted_table(table_data: List[List[Any]], styles: Dict) -> Table:
    """Create formatted table with proper width calculations and error handling"""
    if not table_data or len(table_data) < 2:  # Need at least header and one data row
        return None

    try:
        # Validate table structure
        num_cols = len(table_data[0])
        if num_cols == 0:
            st.error("Invalid table structure: no columns found")
            return None

        # Calculate available width
        available_width = A4[0] - (2 * 25*mm)  # Total width minus margins

        # Calculate column widths - ensure minimum column width
        min_col_width = 30*mm  # minimum width per column
        default_col_width = max(min_col_width, available_width / num_cols)
        col_widths = [default_col_width] * num_cols

        # Adjust widths if they exceed page width
        total_width = sum(col_widths)
        if total_width > available_width:
            ratio = available_width / total_width
            col_widths = [width * ratio for width in col_widths]

        # Create table with calculated widths
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Define table style
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9F9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            
            # Content styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Spacing
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Alternate row colors
            *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F8F9F9' if i % 2 else '#FFFFFF'))
              for i in range(1, len(table_data))]
        ]))
        
        return table

    except Exception as e:
        st.error(f"Table creation error: {str(e)}")
        return None

def process_table_content(content_text: str, styles: Dict) -> List[List[Any]]:
    """Process table content with enhanced validation"""
    table_data = []
    try:
        # Split into lines and clean up
        lines = [line.strip() for line in content_text.split('\n') if line.strip()]
        
        # Validate minimum table structure
        if len(lines) < 3:  # Need header, separator, and at least one data row
            return []
            
        # Process header first to establish column count
        header_line = lines[0]
        if '|' not in header_line:
            return []
            
        # Extract and validate header cells
        header_cells = [cell.strip() for cell in header_line.split('|') if cell.strip()]
        if not header_cells:
            return []
            
        # Create header row
        header_row = [Paragraph(cell, styles['subheading']) for cell in header_cells]
        table_data.append(header_row)
        
        # Find separator line
        separator_found = False
        data_start = 1
        for i, line in enumerate(lines[1:], 1):
            if all(c in '|-: ' for c in line):
                separator_found = True
                data_start = i + 1
                break
                
        if not separator_found:
            return []
            
        # Process data rows
        for line in lines[data_start:]:
            if '|' not in line:
                continue
                
            # Extract and clean cells
            cells = [cell.strip() for cell in line.split('|') if cell]
            if not cells:
                continue
                
            # Format cells
            row_data = []
            for cell in cells:
                # Clean cell content
                clean_cell = re.sub(r'\*\*(.*?)\*\*', r'\1', cell)
                clean_cell = re.sub(r'\*(.*?)\*', r'\1', clean_cell)
                clean_cell = clean_cell.strip()
                
                if clean_cell:
                    row_data.append(Paragraph(clean_cell, styles['content']))
                else:
                    row_data.append(Paragraph('-', styles['content']))
            
            # Ensure row has same number of columns as header
            while len(row_data) < len(header_cells):
                row_data.append(Paragraph('-', styles['content']))
            row_data = row_data[:len(header_cells)]  # Trim excess columns
            
            table_data.append(row_data)
        
        # Final validation
        if len(table_data) < 2:  # Need at least one data row
            return []
            
        return table_data

    except Exception as e:
        st.error(f"Table processing error: {str(e)}")
        return []
def process_content_section(section: str, styles: Dict) -> List[Any]:
    """Process content sections with improved table handling"""
    elements = []
    content_text = section.strip()
    
    # Better table detection
    table_marker = bool(
        '|' in content_text and 
        '\n' in content_text and
        any(line.strip().startswith('|') for line in content_text.split('\n'))
    )
    
    if table_marker:
        try:
            # Add spacing before table
            elements.append(Spacer(1, 12))
            
            # Process table
            table_data = process_table_content(content_text, styles)
            if table_data:
                table = create_formatted_table(table_data, styles)
                if table:
                    elements.append(table)
                    # Add spacing after table
                    elements.append(Spacer(1, 12))
                else:
                    # Fallback to text if table creation fails
                    elements.append(Paragraph(unescape(content_text), styles['content']))
            else:
                # Fallback to text if table processing fails
                elements.append(Paragraph(unescape(content_text), styles['content']))
                
        except Exception as e:
            st.error(f"Error processing table section: {str(e)}")
            elements.append(Paragraph(unescape(content_text), styles['content']))
    else:
        # Process regular text content
        paragraphs = [p.strip() for p in content_text.split('\n') if p.strip()]
        for para in paragraphs:
            # Clean and format paragraph
            para = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
            elements.append(Paragraph(unescape(para), styles['content']))
            elements.append(Spacer(1, 8))
    
    return elements


def display_results():
    """Display only the latest analysis result with its download button"""
    if st.session_state.results and len(st.session_state.results) > 0:
        # Get the most recent result
        result = st.session_state.results[-1]
        
        # Create columns for the result display and download button
        col1, col2 = st.columns([5, 1])
        
        with col1:
            def split_words(text):
                """Split joined words using common patterns"""
                # First handle numbers with 'million'
                text = re.sub(r'(\d+\.?\d*)million', r'\1 million', text)
                
                # Split text into words
                words = re.findall(r'[A-Za-z]+|[0-9]+(?:\.[0-9]+)?|[^A-Za-z0-9\s]|\s+', text)
                
                result = []
                current_word = ""
                
                for word in words:
                    # Skip spaces and punctuation
                    if word.isspace() or not any(c.isalnum() for c in word):
                        if current_word:
                            result.append(current_word)
                            current_word = ""
                        result.append(word)
                        continue
                    
                    # Process word character by character
                    for i, char in enumerate(word):
                        if i == 0:
                            current_word = char
                            continue
                            
                        prev_char = word[i-1]
                        
                        # Conditions for splitting
                        split_conditions = [
                            prev_char.islower() and char.isupper(),  # camelCase
                            prev_char.isnumeric() and char.isalpha(),  # number to letter
                            prev_char.isalpha() and char.isnumeric(),  # letter to number
                            prev_char.islower() and char.isupper(),    # lowercaseUppercase
                        ]
                        
                        if any(split_conditions):
                            result.append(current_word)
                            current_word = char
                        else:
                            current_word += char
                    
                    if current_word:
                        result.append(current_word)
                        current_word = ""
                
                # Join with appropriate spacing
                cleaned = ''
                for i, item in enumerate(result):
                    if i > 0 and item.isalnum() and result[i-1].isalnum():
                        cleaned += ' '
                    cleaned += item
                
                return cleaned
            
            # Process text line by line
            lines = result['analysis'].split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Skip table lines
                if '|' in line:
                    cleaned_lines.append(line)
                    continue
                
                # Clean text
                cleaned_line = split_words(line)
                cleaned_lines.append(cleaned_line)
            
            # Join lines back together
            analysis_content = '\n'.join(cleaned_lines)
            
            # Convert markdown bold to HTML
            analysis_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', analysis_content)
            
            # Get the appropriate title for the analysis type
            REPORT_TITLES = {
                'whats_happening': 'Situational Analysis',
                'what_could_happen': 'Scenario Insight Summary',
                'why_this_happens': 'Possible Causes',
                'what_should_board_consider': 'Strategic Implications & Board Recommendations'
            }
            
            analysis_title = REPORT_TITLES.get(result['analysis_type'], 'Analysis Report')
            
            st.markdown(f"""
                <div class="analysis-result">
                    <div class="result-header">{analysis_title}</div>
                    <div class="result-metadata">Generated on: {result.get('timestamp', 'N/A')}</div>
                    <div class="result-content">{analysis_content}</div>
                </div>
            """, unsafe_allow_html=True)
            disclaimer_text = """
                <div class="disclaimer">
                    <strong>Disclaimer:</strong>Disclaimer: This analysis is provided for informational purposes only and should not be considered as financial, legal, or investment advice. The content is generated using artificial intelligence and may require verification. Users should exercise their own judgment and consult appropriate professionals before making any decisions based on this information. © BADEA © CEAI, All rights reserved.
                </div>
            """
            
            st.markdown(disclaimer_text, unsafe_allow_html=True)
        
        with col2:
            pdf_bytes = create_styled_pdf_report(result, result['analysis_type'])
            if pdf_bytes:
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"board_analysis_{analysis_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{result.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))}"
                )
# Initialize session state for storing results
if 'results' not in st.session_state:
    st.session_state.results = []

# Page configuration
st.set_page_config(
    page_title="BADEA Dr",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with A4 styling
# Replace the existing CSS section with this enhanced version
st.markdown("""
    <style>
    /* Import Lato font */
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&display=swap');
    
    /* Theme colors and base styles */
    :root {
        --primary-color: #2563eb;
        --secondary-color: #1e3a8a;
        --background-color: #f1f5f9;
        --surface-color: #ffffff;
        --text-color: black;
        --border-color: #e2e8f0;
        --spacing-unit: 1rem;
        --font-family: 'Lato', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global styles */
    .stApp {
        background: var(--background-color);
        font-family: var(--font-family);
        color: var(--text-color);
    }
    
    /* Header */
    .header {
        background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Input container */
    .input-container {
        background: var(--surface-color);
        padding: 2.3rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Button container */
    .button-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 1rem;
        font-weight: 500;
        width: 100%;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* A4 Paper styling */
    .analysis-result {
        background: var(--surface-color);
        width: 210mm;
        margin: 2rem auto;
        padding: 25mm;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        font-size: 11pt;
        line-height: 1.6;
        box-sizing: border-box;
        color: black !important;
    }
    
    /* Result header styling */
    .result-header {
        color: var(--primary-color) !important;
        font-size: 18pt;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--border-color);
        word-wrap: break-word;
    }
    
    /* Metadata styling */
    .result-metadata {
        color: #64748b !important;
        font-size: 9pt;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Content styling */
    .result-content {
        text-align: justify;
        margin-top: 1.5rem;
        font-weight: 400;
        color: black !important;
    }
    
    /* Table styling */
    .result-content table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.5rem 0;
        font-size: 10pt;
        color: black !important;
    }
    
    .result-content table th,
    .result-content table td {
        border: 1px solid var(--border-color);
        padding: 0.75rem;
        text-align: left;
        color: black !important;
    }
    
    .result-content table th {
        background-color: #f8fafc;
        font-weight: 600;
    }
    
    /* List styling */
    .result-content ul,
    .result-content ol {
        margin: 1rem 0;
        padding-left: 1.5rem;
        color: black !important;
    }
    
    .result-content li {
        margin-bottom: 0.5rem;
        color: black !important;
    }
    
    /* Section headers within content */
    .result-content h1,
    .result-content h2,
    .result-content h3 {
        color: var(--primary-color);
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        line-height: 1.4;
    }
    
    .result-content h1 { font-size: 16pt; }
    .result-content h2 { font-size: 14pt; }
    .result-content h3 { font-size: 12pt; }
    
    /* Paragraph spacing */
    .result-content p {
        margin-bottom: 1rem;
        line-height: 1.6;
        color: black !important;
    }
    
    /* Number and currency formatting */
    .result-content .number,
    .result-content .currency {
        font-family: 'Lato', monospace;
        white-space: nowrap;
        color: black !important;
    }
    
    /* Hide Streamlit components */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .analysis-result {
            width: 95%;
            padding: 15mm;
            margin: 1rem auto;
        }
        
        .result-header {
            font-size: 16pt;
        }
        
        .result-content {
            font-size: 10pt;
        }
    }
    
    /* Text color fixes */
    .stMarkdown, .stText, .stTextInput, .stTextArea, p {
        color: black !important;
    }
    
    .custom-text-color {
        color: black !important;
    }
    
    .element-container, .stMarkdown, p, .stText {
        color: black !important;
    }
    
    /* Radio button text color fix */
    .stRadio > div {
        color: black !important;
    }
    
    /* Info message text color */
    .stAlert > div {
        color: black !important;
    }
    
    /* Submit button styling */
    .stButton button[kind="formSubmit"] {
        background: linear-gradient(135deg, #2563eb, #1e3a8a);
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        width: 100%;
        margin-top: 1rem;
        transition: all 0.2s;
    }
    
    .stButton button[kind="formSubmit"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    /* Disclaimer styling */
    .disclaimer {
        background-color: #f8f9fa;
        border-left: 4px solid #2563eb;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #1e293b !important;
        line-height: 1.5;
    }

    .pdf-disclaimer {
        font-size: 8pt;
        color: #64748b;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
        padding-top: 1rem;
        font-style: italic;
    }
    }
    </style>
""", unsafe_allow_html=True)

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def chunk_text(text: str, max_chunk_tokens: int = 6000) -> List[str]:
    """Split text into chunks that respect token limits."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for token in tokens:
        if current_length < max_chunk_tokens:
            current_chunk.append(token)
            current_length += 1
        else:
            chunks.append(encoding.decode(current_chunk))
            current_chunk = [token]
            current_length = 1
            
    if current_chunk:
        chunks.append(encoding.decode(current_chunk))
    
    return chunks

def summarize_chunks(chunks: List[str], client: OpenAI) -> str:
    """Summarize multiple chunks of text into a condensed version."""
    summaries = []
    
    for i, chunk in enumerate(chunks):
        try:
            st.info(f"Summarizing chunk {i+1} of {len(chunks)}...")
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Summarize the following text while preserving key facts, figures, and insights:For each point and section, make sure you provide in depth statistics, supporting facts, figures to support each assertion, as well as quoting the sources from where the data is obtained. From the data provided, contextualise and synthesize with the analysis."},
                    {"role": "user", "content": chunk}
                ],
                max_tokens=1000
            )
            summaries.append(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Error summarizing chunk: {str(e)}")
            continue
    
    combined_summary = " ".join(summaries)
    if count_tokens(combined_summary) > 6000:
        return summarize_chunks([combined_summary], client)
    
    return combined_summary

def read_pdf(pdf_file):
    """Read and extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def configure_openai() -> bool:
    """Configure  Secret Key"""
    with st.sidebar:
        st.markdown("### 🔑 User ID")
        api_key = st.text_input("Enter User ID", type="password")
        if api_key:
            st.session_state['client'] = OpenAI(api_key=api_key)
            return True
        return False

def create_professional_system_prompt() -> str:
    """Creates a standardized system prompt for consistent professional formatting."""
    return (
        "You are a seasoned board advisor providing comprehensive strategic analysis. Explain and expressed from the perspective of board directors "
        "Follow these strict formatting rules: "
        "1. Use markdown bold for all section headers and key findings\n"
        "2. Numbers and Currency: "
        "   Write all currency values consistently, such as 'USD 75 million' or '$75 million'. "
        "   Always use spaces between numbers and units (e.g., '75 million'). "
        "   Present all numbers as numerals with proper formatting (e.g., '289 million'). "
        "   CRITICAL: Never join numbers with words (write '55.64 million' NOT '55.64million')\n"
        "3. Text Formatting: "
        "   Use standard paragraph formatting with clear spacing. "
        "   Avoid italics, special characters, or unusual formatting. "
        "   No ### at the start of the header or subheader"
        "   No special characters or fancy formatting. "
        "   Maintain consistent font and style throughout. "
        "   CRITICAL: Never join words together - always use spaces between words.\n"
        "   Examples of correct formatting:"
        "   - 'targets city development' NOT 'targetscitydevelopment'"
        "   - 'credit loan for a regional bank' NOT 'creditloanforaregionalbank'"
        "   - 'from BADEA's loan' NOT 'fromBADEA'sloan'\n"
        "4. Section Headers: "
        "   Use bold markdown for headers. "
        "   Keep header formatting consistent throughout the document. "
        "5. Lists and Tables: "
        "   Use simple, clean formatting for any lists. "
        "   Create tables with clear organization and consistent spacing. "
        "6. Professional Language: "
        "   Use formal, board-appropriate language. "
        "   Maintain consistent tone throughout. "
        "   Present data clearly and professionally."
        "7. Do not generate footnotes or citations at the bottom of the analysis\n"
        "8. Reference sources directly within the text when needed\n"
        "9. Special Formatting Rules:"
        "   - Always add spaces after numbers (e.g., '40 million' NOT '40million')"
        "   - Always separate SDG references with spaces (e.g., 'SDG 11' NOT 'SDG11')"
        "   - Use spaces around parentheses (e.g., ' (SDG 9) ' NOT '(SDG9)')"
        "   - Never use camelCase or joined words"
        "   - Always maintain proper word spacing throughout the document\n"
        "10. Quality Control:"
        "    - Review output to ensure no words are incorrectly joined"
        "    - Verify proper spacing between all numbers and words"
        "    - Ensure consistent formatting throughout the document"
    )
def clean_text_anomalies(text: str) -> str:
    """Clean up text anomalies by adding proper spacing while preserving formatting"""
    if not text:
        return text
    
    def clean_segment(text: str) -> str:
        # Fix split words ending with 'ing'
        text = re.sub(r'(\w+)\s+ing\b', r'\1ing', text)
        
        # Fix number + "million/billion/trillion" without space
        text = re.sub(r'(\d+\.?\d*)(million|billion|trillion)', r'\1 \2', text)
        
        # Add space between parentheses and text
        text = re.sub(r'(\w|\))\(', r'\1 (', text)
        text = re.sub(r'\)([a-zA-Z])', r') \1', text)
        
        # Fix joined words after "and"
        text = re.sub(r'\)and([A-Z])', r') and \1', text)
        
        # Add spaces between lowercase followed by uppercase (camelCase)
        text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)
        
        # Add spaces between an uppercase letter followed by lowercase (if not start of word)
        text = re.sub(r'(?<!^)(?<![\s.])([A-Z][a-z])', r' \1', text)
        
        # Fix multiple uppercase letters
        text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
        
        # Fix spaces around punctuation
        text = re.sub(r'\s*([.,])\s*', r'\1 ', text)
        
        # Add space after numbers followed by words
        text = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', text)
        
        # Add space between word and number
        text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    # Process text line by line
    lines = []
    for line in text.split('\n'):
        # Skip lines that appear to be tables
        if '|' in line or line.strip().startswith('-'):
            lines.append(line)
            continue
            
        # Clean each line
        cleaned_line = clean_segment(line)
        lines.append(cleaned_line)
    
    return '\n'.join(lines)

def analyze_with_retry(text: str, analysis_type: str, prompt: str) -> Dict[str, Any]:
    try:
        client = st.session_state['client']
        total_tokens = count_tokens(text)
        
        if total_tokens > 6000:
            st.info("Input text is long, performing automatic summarization...")
            chunks = chunk_text(text)
            text = summarize_chunks(chunks, client)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": create_professional_system_prompt()},
                {"role": "user", "content": prompt + f"\n\nData for analysis: {text}"}
            ]
        )
        
        analysis_text = response.choices[0].message.content
        
        try:
            cleaned_analysis = clean_text_anomalies(analysis_text)
        except Exception as e:
            st.warning(f"Text cleaning encountered an error: {str(e)}. Using original text.")
            cleaned_analysis = analysis_text
        
        result = {
            "analysis_type": analysis_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis": cleaned_analysis
        }
        
        st.session_state.results.append(result)
        return result
        
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return None
def analyze_whats_happening(text: str) -> Dict[str, Any]:
    """Analyze current trends from Board perspective."""
    prompt = (
        "You are a globally recognized financial consultant, sought after for your expertise in providing in-depth, actionable, and strategic financial analyses tailored to senior executives and stakeholders. Leveraging your extensive experience and the data provided, perform a *comprehensive financial health evaluation and advisory* for the company in question. Your analysis must incorporate advanced financial modeling, credit rating assessments comparable to S&P and Moody's methodologies, and an evaluation of working capital needs and debt repayment capacity. Focus on delivering insights that drive informed, strategic decision-making.\n\n"
        "1. Financial Health Analysis with Credit Rating. 900 words.\n"
        "Evaluate the company’s financial health using key financial metrics, such as:\n"
        "   - Liquidity Ratios (Current Ratio, Quick Ratio)\n"
        "   - Profitability Ratios (Net Profit Margin, ROE, ROA)\n"
        "   - Solvency Ratios (Debt-to-Equity, Interest Coverage Ratio)\n"
        "   - Efficiency Ratios (Receivables Turnover, Inventory Turnover)\n"
        "Develop a credit rating assessment similar to S&P and Moody's by analyzing:\n"
        "   - Business risk: Industry outlook, market positioning, revenue diversification, and operational efficiency.\n"
        "   - Financial risk: Leverage, profitability trends, liquidity, and cash flow adequacy.\n"
        "   - Assign an estimated credit rating (e.g., BBB, A, AA) with supporting rationale tied to these factors.\n"
        "Provide insights into the company’s capacity to meet its financial obligations, particularly focusing on its ability to maintain a favorable rating amid external and internal risks.\n"
        "2. Working Capital Needs and Debt Repayment Capacity Analysis\n"
        "Calculate and evaluate the company’s working capital requirements*, including:\n"
        "   - Current working capital position (Current Assets – Current Liabilities).\n"
        "   - Projected working capital needs based on historical trends, revenue growth forecasts, and operational cycles.\n"
        "Assess the company’s capacity to service debt obligations, including:\n"
        "   - Available cash flow relative to upcoming debt maturities.\n"
        "   - Free Cash Flow (FCF) projections for short-term liquidity.\n"
        "   - Net debt position and interest coverage ratio.\n"
        "Discuss the sufficiency of current liquidity to meet both operational and financial obligations, with an emphasis on strategies to optimize working capital and debt servicing efficiency.\n"
        "3. Key Risks Analysis Across Time Horizons 800 words.\n"
        "Identify and assess risks using financial, operational, and market data:\n"
        "   - Short term (<1 year):* Risks like cash flow volatility, debt repayment pressures, and market disruptions.\n"
        "   - Medium term (1–3 years):* Challenges such as refinancing risks, operational scalability, and changing competitive dynamics.\n"
        "   - Long term (>3 years):* Strategic risks like technology disruption, regulatory shifts, and macroeconomic changes.\n"
        "Provide a clear linkage between risks and the company’s financial health, credit rating, and capacity to meet future obligations.\n"
        "4. Financial Predictions with Supporting Data. 900 words.\n"
        "Forecast the company’s financial performance for the next three years, detailing:\n"
        "   - Revenue growth, profitability trends, and expected changes in operating margins.\n"
        "   - Projected credit rating trajectory based on forecasted metrics.\n"
        "   - Working capital and cash flow projections tied to debt repayment schedules.\n"
        "Use time-referenced insights to offer a clear rationale behind each prediction:\n"
        "   - Best-case, base-case, and worst-case scenarios, including their respective probabilities.\n"
        "Provide actionable insights into how these predictions align with the company’s financial strategy and operational goals."
        "5. Recommended Measures (Action-Oriented and Time-Specific).\n"
        "Propose a comprehensive set of measures to:\n"
        "   - Enhance liquidity and optimize working capital (e.g., faster receivables collection, inventory management improvements).\n"
        "   - Improve creditworthiness by reducing leverage and increasing interest coverage ratios.\n"
        "   - Strengthen financial performance to achieve or maintain a favorable credit rating.\n"
        "Include SPECIFIC TIMELINES for implementation (short, medium, long term) and expected financial outcomes (e.g., reduced debt-to-equity ratio, improved FCF).\n"
        "6. Advisory Modules with Titles and Abstracts.\n"
        "Develop detailed advisory modules tailored to the company’s needs, including titles and abstracts:\n"
        "Example Modules:\n"
        "Module 1: "Optimizing Working Capital: A Path to Enhanced Liquidity\n"
        "Abstract: This module focuses on optimizing cash flows through efficient receivables, payables, and inventory management. It includes a step-by-step approach to reducing working capital needs by 10–15% within one year, improving liquidity and supporting debt repayment capacity.\n"
        "Module 2: "Achieving Investment-Grade Credit Ratings: A Strategic Blueprint\n"
        "Abstract: This module provides a roadmap to achieving or maintaining an investment-grade credit rating by enhancing profitability, reducing leverage, and improving operational efficiency. The plan includes specific ratio targets, timelines, and resource requirements.\n"
        "Module 3: "Debt Management and Refinancing Strategies for Long-Term Stability\n"
        "Abstract: This module helps the company assess its current debt portfolio, identify refinancing opportunities, and develop a long-term strategy to manage interest obligations and maturities. It includes projections of debt servicing costs under various scenarios."
    )
    return analyze_with_retry(text, "whats_happening", prompt)

def analyze_why_this_happens(text: str) -> Dict[str, Any]:
    """Analyze root causes based on trends."""
    prompt = (
        "Based on the trends uncovered in the data provided, explain 5 reasons "
        "possible root causes and implications.\n\n"
        "if financial data exists, please include time references and periods of which they incur as part of the analysis\n"
        "Requirements:\n"
        "1. Total Analysis Length: 1300 words\n"
        "2. For each root cause:\n"
        "   - Supporting facts, figures and examples\n"
        "   - Explanation of which aspects should concern the Board and why\n"
        "3. Focus on supportable trend analysis only - no solutions required\n"
        "4. Create a summary table of key findings in a table format\n"
        "Note: For each point and section (except for the table part), make sure you provide in depth statistics, supporting facts, figures to support each assertion, as well as quoting the sources from where the data is obtained. From the data provided, contextualise and synthesize with the analysis.\n"
        "5. Present the information as a conceptual model in a framework format in a long paragraph:300 words. "
    )
    return analyze_with_retry(text, "why_this_happens", prompt)

def analyze_what_could_happen(text: str) -> Dict[str, Any]:
    """Analyze potential scenarios based on trends and root causes."""
    prompt = (
        "Based on the trends and consideration of the possible root causes from "
        "the data provided, explain possible scenarios.\n\n"
        "if financial data exists, please include time references and periods of which they incur as part of the analysis\n"
        "Requirements:\n"
        "1. Scenario Analysis (1800 words total):\n"
        "   - Worst case scenario (600 words)\n"
        "   - Base case scenario (600 words)\n"
        "   - Best case scenario (600 words)\n"
        "2. Additional Analysis (1300 words):\n"
        "   - Likelihood assessment for each scenario\n"
        "   - Explanation of why each scenario might occur\n"
        "3. Create a summary table of key findings in a table format\n"
        "Note: For each point and section (except for the table part), make sure you provide in depth statistics, supporting facts, figures to support each assertion, as well as quoting the sources from where the data is obtained. From the data provided, contextualise and synthesize with the analysis.\n"
        "4. Develop a framework table USING A TABLE  to visualize the relationships in this narrative"
    )
    return analyze_with_retry(text, "what_could_happen", prompt)

def analyze_board_considerations(text: str) -> Dict[str, Any]:
    """Analyze what the Board should consider based on all analyses."""
    prompt = (
        "Based on the trends, diagnosis, outlook and from the data provided, "
        "explain possible scenarios.\n\n"
        "if financial data exists, please include time references and periods of which they incur as part of the analysis\n"
        "Requirements:\n"
        "1. Total Analysis Length: 1300 words\n"
        "2. Analysis should cover:\n"
        "   - Strategic implications\n"
        "   - Risk considerations\n"
        "   - Governance aspects\n"
        "   - Recommended actions\n"
        "3. Create a summary table of key findings in a table format\n"
        "Note: For each point and section(except for the table part), make sure you provide in depth statistics, supporting facts, figures to support each assertion, as well as quoting the sources from where the data is obtained. From the data provided, contextualise and synthesize with the analysis.\n"
        "4. Present the information as a conceptual mode in a framework format"
        "5. Explain the conceptual framework with forward looking advice to the Board in a long paragraph: 300 words"
    )
    return analyze_with_retry(text, "what_should_board_consider", prompt)
def main():
    # Header
    header_left, header_right = st.columns([3, 2])

    # Combined GIF and title
    with header_left:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 0;">
                <img src="https://cdn.dribbble.com/users/42048/screenshots/8350927/robotintro_dribble.gif" 
                    alt="Robot" width="160" height="160" 
                    style="object-fit: contain; mix-blend-mode: multiply;">
                <div style='background: linear-gradient(135deg, #1e3a8a, #2563eb); 
                            padding: 0.8rem 1.5rem; 
                            border-radius: 12px; 
                            display: inline-block;
                            margin-left: -10px;'>
                    <h1 style='margin:0; font-size: 2.2rem; color: white; font-weight: 700;'>
                        Badea Board Foresight
                    </h1>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Badea logo
    with header_right:
        st.markdown("""
            <div style="margin-top: 20px;">
        """, unsafe_allow_html=True)
        try:
            st.image("badea.jpeg", width=800)
        except:
            st.warning("Please add badea.jpeg to your project directory")
        st.markdown("""
            </div>
        """, unsafe_allow_html=True)

    # Configure OpenAI
    if not configure_openai():
        st.warning("⚠️ Enter User ID in sidebar to continue")
        return

    # Main content area
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        input_type = st.radio("Select input type:", ["PDF Document", "Text Input", "Images"], horizontal=True)
        
        # Initialize content in session state
        if 'processed_content' not in st.session_state:
            st.session_state.processed_content = None
        
        # Handle different input types
        if input_type == "PDF Document":
            uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
            if uploaded_file:
                st.session_state.processed_content = process_input_content(input_type, uploaded_file, "", st.session_state['client'])
        elif input_type == "Images":
            uploaded_files = st.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
            if uploaded_files:
                st.session_state.processed_content = process_input_content(input_type, uploaded_files, "", st.session_state['client'])
        else:
            with st.form(key='text_input_form'):
                text_input = st.text_area("Enter text for analysis", height=200)
                submit_text = st.form_submit_button("Submit Text")
                if submit_text and text_input.strip():
                    st.session_state.processed_content = process_input_content(input_type, None, text_input, st.session_state['client'])
        
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        if st.session_state.processed_content:
            if st.button("What's happening?"):
                st.session_state.results = []
                analyze_whats_happening(st.session_state.processed_content)
            
            if st.button("Why this happens?"):
                st.session_state.results = []
                analyze_why_this_happens(st.session_state.processed_content)
            
            if st.button("What could happen?"):
                st.session_state.results = []
                analyze_what_could_happen(st.session_state.processed_content)
            
            if st.button("What should the Board consider?"):
                st.session_state.results = []
                analyze_board_considerations(st.session_state.processed_content)
        else:
            st.info("Please provide input and submit to enable analysis")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Display results with PDF download options
    display_results()

    # Add download functionality for all results
    if st.session_state.results:
        st.sidebar.markdown("### Menu")
        
        # Clear results button
        if st.sidebar.button("Click to return"):
            st.session_state.results = []
            st.rerun()

if __name__ == "__main__":
    main()
