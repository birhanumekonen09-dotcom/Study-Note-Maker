import os
import fitz  # PyMuPDF
import streamlit as st
import xml.sax.saxutils
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configure Streamlit page layout
st.set_page_config(page_title="Smart Study Note Generator", page_icon="📚", layout="wide")

def extract_content_from_pdf(uploaded_file, max_file_size_mb=100):
    """
    Validates file size, reads up to 100MB, and extracts text block-by-block 
    along with its precise page number, escaping special XML characters.
    """
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_file_size_mb:
        st.error(f"File size ({file_size_mb:.2f}MB) exceeds the 100MB limit.")
        return None

    extracted_data = []
    
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():
                paragraphs = text.split('\n\n')
                for p in paragraphs:
                    cleaned_p = p.strip().replace('\n', ' ')
                    if len(cleaned_p) > 40:
                        # Escape special characters (&, <, >) to prevent ReportLab XML parser crashes
                        safe_text = xml.sax.saxutils.escape(cleaned_p)
                        extracted_data.append({
                            "page": page_num,
                            "content": safe_text
                        })
                        
    return extracted_data

def generate_styled_notes_pdf(notes_data, output_filename="Structured_Study_Notes.pdf"):
    """
    Compiles extracted text into a designed PDF note sheet 
    complete with visual infographic callout blocks and page references.
    """
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748")
    )
    
    page_badge_style = ParagraphStyle(
        'PageBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1
    )

    story = []
    
    story.append(Paragraph("📖 Master Study Notes & Core Insights", title_style))
    story.append(Paragraph("Auto-generated summary extracted directly from uploaded materials with source tracking.", body_style))
    story.append(Spacer(1, 15))
    
    for idx, item in enumerate(notes_data[:40], start=1):
        page_text = f"P. {item['page']}"
        badge_p = Paragraph(page_text, page_badge_style)
        content_p = Paragraph(f"<b>Core Point #{idx}:</b> {item['content'][:300]}...", body_style)
        
        callout_table = Table([[badge_p, content_p]], colWidths=[65, 435])
        callout_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#3182CE")),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#EDF2F7")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ]))
        
        story.append(callout_table)
        story.append(Spacer(1, 8))

    doc.build(story)
    return output_filename

# --- Streamlit UI Design ---
st.title("📚 Automated Smart Study Notes Generator")
st.markdown("Upload any book, textbook, or PDF (up to **100MB**). The engine will extract key concepts, organize them into visual infographic blocks with exact page numbers, and supply a direct download path.")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    st.info(f"File uploaded successfully: **{uploaded_file.name}** ({uploaded_file.size / (1024*1024):.2f} MB)")
    
    if st.button("🚀 Generate Decorated Notes"):
        with st.spinner("Extracting text blocks and compiling structured infographic notes..."):
            extracted = extract_content_from_pdf(uploaded_file, max_file_size_mb=100)
            
            if extracted:
                output_pdf_path = generate_styled_notes_pdf(extracted)
                st.success("Notes generated successfully!")
                
                with open(output_pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download Structured Notes (PDF)",
                        data=pdf_file,
                        file_name=f"Notes_{uploaded_file.name}",
                        mime="application/pdf"
                    )
