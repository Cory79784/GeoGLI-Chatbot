"""
Export conversation to PDF functionality
"""
import os
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors
import textwrap
from datetime import datetime

from app.database import db

router = APIRouter()


@router.get("/export/{session_id}")
def export_conversation(session_id: str):
    """
    Export conversation to PDF
    
    Args:
        session_id: Session identifier
        
    Returns:
        PDF file response
    """
    try:
        # Get conversation from database
        messages = db.get_conversation(session_id)
        
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Custom styles
        user_style = ParagraphStyle(
            'UserStyle',
            parent=normal_style,
            textColor=colors.blue,
            leftIndent=20,
            fontName='Helvetica-Bold'
        )
        
        assistant_style = ParagraphStyle(
            'AssistantStyle', 
            parent=normal_style,
            textColor=colors.darkgreen,
            leftIndent=20
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("UNCCD GeoGLI Chatbot Conversation", title_style))
        story.append(Spacer(1, 12))
        
        # Session info
        story.append(Paragraph(f"Session ID: {session_id}", heading_style))
        story.append(Paragraph(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 12))
        
        # Messages
        for message in messages:
            role = message['role']
            content = message['content']
            timestamp = message['created_at']
            
            # Role header
            role_text = f"{role.upper()} ({timestamp})"
            story.append(Paragraph(role_text, heading_style))
            
            # Message content
            # Wrap long lines and escape HTML
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if role == 'user':
                story.append(Paragraph(content, user_style))
            else:
                story.append(Paragraph(content, assistant_style))
            
            story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        # Return file response
        return FileResponse(
            temp_file.name,
            filename=f"conversation_{session_id}.pdf",
            media_type="application/pdf",
            background=_cleanup_temp_file(temp_file.name)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


def _cleanup_temp_file(file_path: str):
    """Background task to cleanup temporary file"""
    def cleanup():
        try:
            os.unlink(file_path)
        except:
            pass
    return cleanup

