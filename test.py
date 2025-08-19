import json
import os
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white, darkblue, lightgrey
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap
from datetime import datetime
import urllib.request
import tempfile

class ExamPDFRenderer:
    def __init__(self):
        self.colors = {
            'primary': HexColor('#2E86AB'),      # Blue
            'secondary': HexColor('#A23B72'),    # Purple
            'accent': HexColor('#F18F01'),       # Orange
            'success': HexColor('#C73E1D'),      # Red
            'text': HexColor('#2D3748'),         # Dark gray
            'light_bg': HexColor('#F7FAFC'),     # Light gray
            'border': HexColor('#E2E8F0')        # Border gray
        }
        
        # Đăng ký font hỗ trợ tiếng Việt
        self.setup_vietnamese_fonts()
        
    def setup_vietnamese_fonts(self):
        """Thiết lập font hỗ trợ tiếng Việt"""
        try:
            # Thử sử dụng font DejaVu Sans (thường có sẵn)
            # Nếu không có, sẽ fallback về font mặc định
            
            # Font paths phổ biến trên các hệ điều hành
            font_paths = [
                # Windows
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf',
                # macOS
                '/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Arial.ttf',
                # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            ]
            
            font_registered = False
            
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        # Đăng ký font regular
                        pdfmetrics.registerFont(TTFont('Vietnamese', font_path))
                        
                        # Thử tìm font bold
                        bold_path = font_path.replace('.ttf', 'b.ttf').replace('Regular', 'Bold')
                        if os.path.exists(bold_path):
                            pdfmetrics.registerFont(TTFont('Vietnamese-Bold', bold_path))
                        else:
                            # Fallback: sử dụng font regular cho bold
                            pdfmetrics.registerFont(TTFont('Vietnamese-Bold', font_path))
                        
                        font_registered = True
                        print(f"✅ Đã đăng ký font: {font_path}")
                        break
                except Exception as e:
                    continue
            
            if not font_registered:
                print("⚠️  Không tìm thấy font Unicode, sử dụng font mặc định")
                # Fallback: sử dụng font mặc định của ReportLab
                self.font_name = 'Helvetica'
                self.font_bold = 'Helvetica-Bold'
            else:
                self.font_name = 'Vietnamese'
                self.font_bold = 'Vietnamese-Bold'
                
        except Exception as e:
            print(f"⚠️  Lỗi khi thiết lập font: {e}")
            self.font_name = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'
        
    def setup_styles(self):
        """Thiết lập các style cho document"""
        styles = getSampleStyleSheet()
        
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.colors['primary'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=self.font_bold
        )
        
        # Question header style
        self.question_header_style = ParagraphStyle(
            'QuestionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=white,
            spaceAfter=10,  # Giảm spacing
            spaceBefore=15,  # Giảm spacing
            alignment=TA_LEFT,
            fontName=self.font_bold,
            backColor=self.colors['primary'],
            leftIndent=10,
            rightIndent=10,
            topPadding=6,  # Giảm padding
            bottomPadding=6
        )
        
        # Question text style
        self.question_style = ParagraphStyle(
            'QuestionText',
            parent=styles['Normal'],
            fontSize=12,
            textColor=self.colors['text'],
            spaceAfter=12,  # Giảm spacing
            spaceBefore=8,   # Giảm spacing
            alignment=TA_JUSTIFY,
            fontName=self.font_name,
            leftIndent=15,
            rightIndent=15,
            leading=15
        )
        
        # Option style
        self.option_style = ParagraphStyle(
            'OptionText',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.colors['text'],
            spaceAfter=6,  # Giảm spacing
            alignment=TA_LEFT,
            fontName=self.font_name,
            leftIndent=25,
            leading=13
        )
        
        # Correct answer style
        self.correct_answer_style = ParagraphStyle(
            'CorrectAnswer',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.colors['success'],
            spaceAfter=6,  # Giảm spacing
            alignment=TA_LEFT,
            fontName=self.font_bold,
            leftIndent=25,
            leading=13
        )
        
        # Answer label style
        self.answer_label_style = ParagraphStyle(
            'AnswerLabel',
            parent=styles['Normal'],
            fontSize=12,
            textColor=self.colors['accent'],
            spaceAfter=12,  # Tăng spacing để không đè lên explanation
            spaceBefore=15,  # Tăng spacing từ options
            alignment=TA_LEFT,
            fontName=self.font_bold,
            leftIndent=15
        )
        
        # Explanation style
        self.explanation_style = ParagraphStyle(
            'ExplanationText',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.colors['text'],
            spaceAfter=20,  # Tăng spacing sau explanation
            spaceBefore=5,  # Thêm spacing trước explanation
            alignment=TA_JUSTIFY,
            fontName=self.font_name,
            leftIndent=15,
            rightIndent=15,
            leading=15,  # Tăng line height cho dễ đọc
            backColor=self.colors['light_bg'],
            borderColor=self.colors['border'],
            borderWidth=1,
            borderPadding=10  # Tăng lại padding
        )

    def create_header_footer(self, canvas, doc):
        """Tạo header và footer cho tất cả các trang"""
        canvas.saveState()
        
        # Header
        canvas.setFillColor(self.colors['primary'])
        canvas.rect(0, A4[1] - 60, A4[0], 60, fill=1)
        
        canvas.setFillColor(white)
        canvas.setFont(self.font_bold, 16)
        # Tính toán để center text
        text = "BÀI KIỂM TRA QUẢN LÝ DỰ ÁN"
        text_width = canvas.stringWidth(text, self.font_bold, 16)
        canvas.drawString((A4[0] - text_width) / 2, A4[1] - 35, text)
        
        # Footer
        canvas.setFillColor(self.colors['text'])
        canvas.setFont(self.font_name, 10)
        canvas.drawString(30, 30, f"Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        # Tính toán để right-align text
        page_text = f"Trang {doc.page}"
        page_text_width = canvas.stringWidth(page_text, self.font_name, 10)
        canvas.drawString(A4[0] - 30 - page_text_width, 30, page_text)
        
        # Decorative line
        canvas.setStrokeColor(self.colors['accent'])
        canvas.setLineWidth(2)
        canvas.line(30, 50, A4[0] - 30, 50)
        
        canvas.restoreState()

    def wrap_text(self, text, width=80):
        """Chia text thành nhiều dòng nếu quá dài"""
        return textwrap.fill(text, width=width)

    def render_question(self, question_data, question_num):
        """Render một câu hỏi thành các elements"""
        elements = []
        
        # Question header với số thứ tự
        header_text = f"Câu hỏi {question_num}"
        elements.append(Paragraph(header_text, self.question_header_style))
        
        # Question text
        question_text = question_data['question']
        elements.append(Paragraph(question_text, self.question_style))
        
        # Options - thêm spacer nhỏ trước đáp án
        for option in question_data['options']:
            option_letter = option.split('.')[0]  # Lấy A, B, C, D
            option_text = option.split('.', 1)[1].strip()  # Lấy nội dung sau dấu chấm
            
            # Highlight correct answer
            if option_letter == question_data['answer']:
                styled_option = f"<b>{option_letter}.</b> {option_text} ✓"
                elements.append(Paragraph(styled_option, self.correct_answer_style))
            else:
                styled_option = f"{option_letter}. {option_text}"
                elements.append(Paragraph(styled_option, self.option_style))
        
        # Thêm spacer sau options, trước đáp án
        elements.append(Spacer(1, 10))
        
        # Answer label
        elements.append(Paragraph(f"<b>Đáp án đúng: {question_data['answer']}</b>", self.answer_label_style))
        
        # Thêm một spacer nhỏ giữa đáp án và giải thích
        elements.append(Spacer(1, 5))
        
        # Explanation
        explanation_text = f"<b>Giải thích:</b><br/>{question_data['explanation']}"
        elements.append(Paragraph(explanation_text, self.explanation_style))
        
        # Add spacing between questions
        elements.append(Spacer(1, 25))  # Tăng spacing giữa các câu hỏi
        
        return elements

    def create_cover_page(self):
        """Tạo trang bìa đẹp mắt"""
        elements = []
        
        # Large title
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            fontSize=28,
            textColor=self.colors['primary'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=self.font_bold
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontSize=16,
            textColor=self.colors['secondary'],
            spaceAfter=50,
            alignment=TA_CENTER,
            fontName=self.font_name
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            fontSize=12,
            textColor=self.colors['text'],
            spaceAfter=15,
            alignment=TA_CENTER,
            fontName=self.font_name
        )
        
        # Add some space from top
        elements.append(Spacer(1, 100))
        
        # Main title
        elements.append(Paragraph("BÀI KIỂM TRA", cover_title_style))
        elements.append(Paragraph("QUẢN LÝ DỰ ÁN", cover_title_style))
        
        # Subtitle
        elements.append(Paragraph("Tập hợp câu hỏi và đáp án chi tiết", subtitle_style))
        
        # Info box
        info_data = [
            ["Tổng số câu hỏi:", "10 câu"],
            ["Thời gian:", "Không giới hạn"],
            ["Dạng bài:", "Trắc nghiệm"],
            ["Ngày tạo:", datetime.now().strftime('%d/%m/%Y')]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['light_bg']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, -1), self.font_bold),
            ('FONTNAME', (1, 0), (1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [white, self.colors['light_bg']]),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['border']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(Spacer(1, 50))
        elements.append(info_table)
        elements.append(PageBreak())
        
        return elements

    def render_to_pdf(self, json_file_path, output_pdf_path="exam_questions.pdf"):
        """Render JSON file thành PDF"""
        
        # Load JSON data
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                exam_data = json.load(f)
        except FileNotFoundError:
            print(f"Không tìm thấy file: {json_file_path}")
            return False
        except json.JSONDecodeError:
            print(f"File JSON không hợp lệ: {json_file_path}")
            return False
        
        # Setup styles
        self.setup_styles()
        
        # Create document with custom page template
        class CustomDocTemplate(BaseDocTemplate):
            def __init__(self, filename, **kwargs):
                super().__init__(filename, **kwargs)
                
        doc = CustomDocTemplate(
            output_pdf_path,
            pagesize=A4,
            topMargin=80,
            bottomMargin=70,
            leftMargin=40,
            rightMargin=40,
            # Cho phép content flow tự nhiên hơn
            allowSplitting=1
        )
        
        # Create frame and page template
        frame = Frame(
            40, 70, A4[0] - 80, A4[1] - 150,
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0
        )
        
        template = PageTemplate(id='normal', frames=frame, onPage=self.create_header_footer)
        doc.addPageTemplates([template])
        
        # Build content
        story = []
        
        # Add cover page
        story.extend(self.create_cover_page())
        
        # Add questions
        questions = exam_data.get('questions', [])
        for i, question in enumerate(questions, 1):
            story.extend(self.render_question(question, i))
            
            # Chỉ thêm page break khi thực sự cần thiết (sau mỗi 3 câu hỏi)
            # Bỏ page break tự động để text flow tự nhiên hơn
        
        # Build PDF
        try:
            doc.build(story)
            print(f"✅ PDF đã được tạo thành công: {output_pdf_path}")
            print(f"📄 Tổng số câu hỏi: {len(questions)}")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo PDF: {str(e)}")
            return False

def main():
    """Hàm chính để chạy chương trình"""
    renderer = ExamPDFRenderer()
    
    # Input và output file paths
    json_file = "/home/vuiem/KLTN/test/outputs/exam.json"  # Đường dẫn file JSON
    pdf_file = "exam_questions_beautiful.pdf"  # Đường dẫn file PDF output
    
    # Render JSON to PDF
    success = renderer.render_to_pdf(json_file, pdf_file)
    
    if success:
        print(f"\n🎉 Hoàn thành! File PDF đã được tạo tại: {pdf_file}")
        print("📋 PDF bao gồm:")
        print("   • Trang bìa đẹp mắt với thông tin tổng quan")
        print("   • 10 câu hỏi trắc nghiệm với format chuyên nghiệp")
        print("   • Đáp án được highlight màu sắc")
        print("   • Giải thích chi tiết cho từng câu")
        print("   • Header/footer với thông tin bổ sung")
    else:
        print("\n❌ Có lỗi xảy ra trong quá trình tạo PDF!")

if __name__ == "__main__":
    main()