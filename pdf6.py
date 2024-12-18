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




def process_table_content(content_text: str, styles: Dict) -> List[List[Any]]:
    """Process table content consistently regardless of format"""
    table_data = []
    try:
        # Split into lines and clean up
        lines = [line.strip() for line in content_text.split('\n') if line.strip()]
        
        # Find start of actual table content
        start_idx = 0
        for i, line in enumerate(lines):
            if '|' in line:
                start_idx = i
                break
        
        # Process only table lines
        table_lines = []
        for line in lines[start_idx:]:
            # Skip separator lines
            if any(sep in line for sep in ['|-', '-|', '---']):
                continue
            if '|' not in line:
                continue
                
            # Clean and split cells
            cells = line.split('|')
            # Remove empty cells from start/end that come from leading/trailing |
            cells = [cell.strip() for cell in cells if cell.strip()]
            
            if cells:  # Only process non-empty rows
                table_lines.append(cells)
        
        # Process table lines into formatted cells
        for i, row in enumerate(table_lines):
            formatted_row = []
            for cell in row:
                # Remove bold markers and clean text
                cell_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cell).strip()
                
                # Apply appropriate style
                if i == 0:  # Header row
                    formatted_cell = Paragraph(cell_text, styles['subheading'])
                else:  # Content rows
                    formatted_cell = Paragraph(cell_text, styles['content'])
                formatted_row.append(formatted_cell)
            
            if formatted_row:  # Only add non-empty rows
                table_data.append(formatted_row)
        
        # Ensure all rows have same number of columns
        if table_data:
            max_cols = max(len(row) for row in table_data)
            # Create empty cell with appropriate style
            for i, row in enumerate(table_data):
                while len(row) < max_cols:
                    style = styles['subheading'] if i == 0 else styles['content']
                    row.append(Paragraph('', style))
                    
    except Exception as e:
        st.error(f"Table processing error: {str(e)}")
        return []
    
    return table_data

def create_formatted_table(table_data: List[List[Any]], styles: Dict) -> Table:
    """Create consistently formatted table"""
    if not table_data:
        return None

    # Calculate column widths
    available_width = A4[0] - (50*mm)  # Total width minus margins
    num_cols = len(table_data[0])
    col_widths = [available_width / num_cols] * num_cols
    
    # Create table
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Define consistent style
    table.setStyle(TableStyle([
        # Consistent header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Lato-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        
        # Consistent content styling
        ('FONTNAME', (0, 1), (-1, -1), 'Lato'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        
        # Consistent spacing
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        
        # Grid and alignment
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    return table

def process_content_section(section: str, styles: Dict) -> List[Any]:
    """Process content sections with consistent table handling"""
    elements = []
    content_text = section.strip()
    
    # Check for table content
    if '|' in content_text and content_text.count('\n') > 1:
        try:
            # Process table
            table_data = process_table_content(content_text, styles)
            if table_data:
                elements.append(Spacer(1, 12))
                table = create_formatted_table(table_data, styles)
                if table:
                    elements.append(table)
                elements.append(Spacer(1, 12))
            else:
                elements.append(Paragraph(unescape(content_text), styles['content']))
        except Exception as e:
            st.error(f"Error processing table: {str(e)}")
            elements.append(Paragraph(unescape(content_text), styles['content']))
    else:
        # Handle non-table content
        paragraphs = [p.strip() for p in content_text.split('\n') if p.strip()]
        for para in paragraphs:
            para = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
            elements.append(Paragraph(unescape(para), styles['content']))
            elements.append(Spacer(1, 8))
    
    return elements

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
            logo_path = "badea.jpg"
            if os.path.exists(logo_path):
                img = Image(logo_path, width=220, height=40)
                elements.append(img)
                elements.append(Spacer(1, 20))
        except:
            pass
        REPORT_TITLES = {
            'whats_happening': 'Situation Analysis',
            'what_could_happen': 'Scenario Insight Summary',
            'why_this_happens': 'Possible Causes',
            'what_should_board_consider': 'Strategic Implications & Board Recommendations',
            # Include variations without underscores and with spaces
            'whats happening': 'Situation Analysis',
            'what could happen': 'Scenario Insight Summary',
            'why this happens': 'Possible Causes',
            'what should board consider': 'Strategic Implications & Board Recommendations',
            # Include variations without spaces
            'whatshappening': 'Situation Analysis',
            'whatcouldhappen': 'Scenario Insight Summary',
            'whythishappens': 'Possible Causes',
            'whatshouldboardconsider': 'Strategic Implications & Board Recommendations'
        }

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
        
        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return b''
    finally:
        buffer.close()
def create_styles() -> Dict[str, ParagraphStyle]:
    """Create complete set of styles including table-specific styles"""
    styles = {
        'title': ParagraphStyle(
            'CustomTitle',
            fontName='Lato-Bold',
            fontSize=16,
            spaceAfter=20,
            textColor=colors.black,
            leading=20
        ),
        'header': ParagraphStyle(
            'CustomHeader',
            fontName='Lato-Bold',
            fontSize=14,
            spaceAfter=10,
            textColor=colors.black,
            leading=18
        ),
        'subheading': ParagraphStyle(
            'CustomSubheading',
            fontName='Lato-Bold',
            fontSize=10,
            textColor=colors.black,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        ),
        'content': ParagraphStyle(
            'CustomContent',
            fontName='Lato',
            fontSize=10,
            textColor=colors.black,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        ),
        'metadata': ParagraphStyle(
            'CustomMetadata',
            fontName='Lato',
            fontSize=9,
            textColor=colors.black,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        )
    }
    return styles

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
                'whats_happening': 'Situation Analysis',
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
        --text-color: #1e293b;
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
        color: white;
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
    }
    
    /* Result header styling */
    .result-header {
        color: var(--primary-color);
        font-size: 18pt;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--border-color);
        word-wrap: break-word;
    }
    
    /* Metadata styling */
    .result-metadata {
        color: #64748b;
        font-size: 9pt;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Content styling */
    .result-content {
        text-align: justify;
        margin-top: 1.5rem;
        font-weight: 400;
    }
    
    /* Table styling */
    .result-content table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.5rem 0;
        font-size: 10pt;
    }
    
    .result-content table th,
    .result-content table td {
        border: 1px solid var(--border-color);
        padding: 0.75rem;
        text-align: left;
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
    }
    
    .result-content li {
        margin-bottom: 0.5rem;
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
    }
    
    /* Number and currency formatting */
    .result-content .number,
    .result-content .currency {
        font-family: 'Lato', monospace;
        white-space: nowrap;
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
    .custom-text-color {
    color: #1e293b !important;
    }

    .stMarkdown {
        color: #1e293b !important;
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
        st.markdown("### 🔑 APP Configuration")
        api_key = st.text_input("Enter Secret Key", type="password")
        if api_key:
            st.session_state['client'] = OpenAI(api_key=api_key)
            return True
        return False

def create_professional_system_prompt() -> str:
    """Creates a standardized system prompt for consistent professional formatting."""
    return (
        "You are a seasoned board advisor providing comprehensive strategic analysis. "
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
        "Explain the top 5 key observational trends about the data provided, "
        "from a Board of Directors' Perspective.\n\n"
        "Requirements:\n"
        "1. Total Analysis Length: 1300 words\n"
        "2. For each trend, provide:\n"
        "   - Supporting facts, figures and examples\n"
        "   - Clear explanation of why the Board should be concerned\n"
        "3. Focus only on trend analysis - no solutions, root causes or diagnosis\n"
        "4. Create a summary table of key findings in a table format\n"
        "Note: For each point and section (except for the table part), make sure you provide in depth statistics, supporting facts, figures to support each assertion, as well as quoting the sources from where the data is obtained. From the data provided, contextualise and synthesize with the analysis.\n"
        "5. Develop a conceptual model showing based on the info above in a long paragraph: 300 words "
    )
    return analyze_with_retry(text, "whats_happening", prompt)

def analyze_why_this_happens(text: str) -> Dict[str, Any]:
    """Analyze root causes based on trends."""
    prompt = (
        "Based on the trends uncovered in the data provided, explain 5 reasons "
        "possible root causes and implications.\n\n"
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
            st.image("badea.jpg", width=800)
        except:
            st.warning("Please add badea.jpg to your project directory")
        st.markdown("""
            </div>
        """, unsafe_allow_html=True)

    # Configure OpenAI
    if not configure_openai():
        st.warning("⚠️ Enter Secret key in sidebar to continue")
        return

    # Main content area
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        input_type = st.radio("Select input type:", ["PDF Document", "Text Input"], horizontal=True)
        
        if input_type == "PDF Document":
            uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
            doc_content = read_pdf(uploaded_file) if uploaded_file else None
        else:
            doc_content = st.text_area("Enter text for analysis", height=200)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
            st.markdown('<div class="button-container">', unsafe_allow_html=True)
            if doc_content:
                if st.button("What's happening?"):
                    st.session_state.results = []  # Clear previous results
                    analyze_whats_happening(doc_content)
                
                if st.button("Why this happens?"):
                    st.session_state.results = []  # Clear previous results
                    analyze_why_this_happens(doc_content)
                
                if st.button("What could happen?"):
                    st.session_state.results = []  # Clear previous results
                    analyze_what_could_happen(doc_content)
                
                if st.button("What should the Board consider?"):
                    st.session_state.results = []  # Clear previous results
                    analyze_board_considerations(doc_content)
            else:
                st.info("Please provide input to enable analysis")
            st.markdown('</div>', unsafe_allow_html=True)

    # Display results with PDF download options
    display_results()

    # Add download functionality for all results
    if st.session_state.results:
        st.sidebar.markdown("### 💾 Download Results")
        
        # Prepare download data
        download_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analyses": st.session_state.results
        }
        
        # JSON download
        json_data = json.dumps(download_data, indent=2)
        b64_json = base64.b64encode(json_data.encode()).decode()
        st.sidebar.download_button(
            label="Download JSON",
            file_name="boardlytics_analysis.json",
            mime="application/json",
            data=b64_json,
        )
        
        # Clear results button
        if st.sidebar.button("Clear All Results"):
            st.session_state.results = []
            st.experimental_rerun()

if __name__ == "__main__":
    main()