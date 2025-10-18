#!/usr/bin/env python3
"""
PDF Generator for eCourts Cause List Downloader
Generates PDF files from scraped cause list data
"""

import os
import logging
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class PDFGenerator:
    """Generate PDF files from cause list data"""

    def __init__(self):
        """Initialize PDF generator"""
        self.setup_styles()
        logging.info("PDF Generator initialized")

    def setup_styles(self):
        """Setup PDF styles"""
        self.styles = getSampleStyleSheet()

        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20
        )

        self.normal_style = self.styles['Normal']

    def generate_pdf(self, cause_list_data, filename):
        """Generate PDF from cause list data"""
        try:
            # Ensure downloads directory exists
            os.makedirs('downloads', exist_ok=True)

            # Full path for PDF
            pdf_path = os.path.join('downloads', filename)

            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            elements = []

            # Title
            title = f"Cause List - {cause_list_data.get('judge', 'Unknown Judge')}"
            elements.append(Paragraph(title, self.title_style))
            elements.append(Spacer(1, 12))

            # Metadata
            metadata = [
                f"Date: {cause_list_data.get('date', 'N/A')}",
                f"Case Type: {cause_list_data.get('case_type', 'N/A')}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]

            for meta in metadata:
                elements.append(Paragraph(meta, self.normal_style))
                elements.append(Spacer(1, 6))

            elements.append(Spacer(1, 20))

            # Cases table
            cases = cause_list_data.get('cases', [])
            if cases:
                elements.append(Paragraph("Case Details:", self.heading_style))
                elements.append(Spacer(1, 12))

                # Table data
                table_data = [['S.No', 'Case Number', 'Case Title', 'Advocate', 'Purpose', 'Stage']]

                for case in cases:
                    row = [
                        case.get('serial_number', ''),
                        case.get('case_number', ''),
                        case.get('case_title', ''),
                        case.get('advocate', ''),
                        case.get('purpose', ''),
                        case.get('stage', '')
                    ]
                    table_data.append(row)

                # Create table
                table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 2*inch, 1.5*inch, 1.5*inch, 1*inch])

                # Table style
                table_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ])

                table.setStyle(table_style)
                elements.append(table)

                # Summary
                elements.append(Spacer(1, 20))
                summary = f"Total Cases: {len(cases)}"
                elements.append(Paragraph(summary, self.normal_style))

            else:
                elements.append(Paragraph("No cases found for this cause list.", self.normal_style))

            # Build PDF
            doc.build(elements)

            logging.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path

        except Exception as e:
            logging.error(f"Error generating PDF: {e}")
            raise Exception(f"PDF generation failed: {e}")

class BulkPDFGenerator:
    """Generate bulk PDFs for multiple cause lists"""

    def __init__(self):
        """Initialize bulk PDF generator"""
        self.pdf_generator = PDFGenerator()
        logging.info("Bulk PDF Generator initialized")

    def generate_bulk_pdfs(self, cause_lists_data):
        """Generate multiple PDFs from bulk data"""
        generated_files = []

        for cause_list in cause_lists_data:
            try:
                # Generate filename
                judge_name = cause_list.get('judge', 'Unknown').replace(' ', '_').replace('/', '_')
                date = cause_list.get('date', 'Unknown').replace('/', '-')
                case_type = cause_list.get('case_type', 'Unknown')

                filename = f"causelist_{judge_name}_{case_type}_{date}.pdf"

                # Generate PDF
                pdf_path = self.pdf_generator.generate_pdf(cause_list, filename)
                generated_files.append(pdf_path)

            except Exception as e:
                logging.error(f"Failed to generate PDF for {cause_list.get('judge', 'Unknown')}: {e}")

        return generated_files

    def create_combined_pdf(self, cause_lists_data, combined_filename):
        """Create a single combined PDF with all cause lists"""
        try:
            # Ensure downloads directory exists
            os.makedirs('downloads', exist_ok=True)

            # Full path for combined PDF
            pdf_path = os.path.join('downloads', combined_filename)

            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            elements = []

            # Title
            title = "Combined Cause Lists"
            elements.append(Paragraph(title, self.pdf_generator.title_style))
            elements.append(Spacer(1, 12))

            # Generation info
            info = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elements.append(Paragraph(info, self.pdf_generator.normal_style))
            elements.append(Spacer(1, 20))

            total_cases = 0

            # Add each cause list
            for cause_list in cause_lists_data:
                # Section header
                section_title = f"Cause List - {cause_list.get('judge', 'Unknown Judge')}"
                elements.append(Paragraph(section_title, self.pdf_generator.heading_style))
                elements.append(Spacer(1, 6))

                # Metadata
                metadata = [
                    f"Date: {cause_list.get('date', 'N/A')}",
                    f"Case Type: {cause_list.get('case_type', 'N/A')}"
                ]

                for meta in metadata:
                    elements.append(Paragraph(meta, self.pdf_generator.normal_style))
                    elements.append(Spacer(1, 3))

                elements.append(Spacer(1, 12))

                # Cases table
                cases = cause_list.get('cases', [])
                if cases:
                    table_data = [['S.No', 'Case Number', 'Case Title', 'Advocate', 'Purpose', 'Stage']]

                    for case in cases:
                        row = [
                            case.get('serial_number', ''),
                            case.get('case_number', ''),
                            case.get('case_title', ''),
                            case.get('advocate', ''),
                            case.get('purpose', ''),
                            case.get('stage', '')
                        ]
                        table_data.append(row)

                    # Create table
                    table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 2*inch, 1.5*inch, 1.5*inch, 1*inch])

                    table_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ])

                    table.setStyle(table_style)
                    elements.append(table)

                    total_cases += len(cases)

                else:
                    elements.append(Paragraph("No cases found.", self.pdf_generator.normal_style))

                # Page break between cause lists
                elements.append(PageBreak())

            # Summary page
            elements.append(Paragraph("Summary", self.pdf_generator.heading_style))
            elements.append(Spacer(1, 12))

            summary_data = [
                f"Total Cause Lists: {len(cause_lists_data)}",
                f"Total Cases: {total_cases}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]

            for summary in summary_data:
                elements.append(Paragraph(summary, self.pdf_generator.normal_style))
                elements.append(Spacer(1, 6))

            # Build combined PDF
            doc.build(elements)

            logging.info(f"Combined PDF generated successfully: {pdf_path}")
            return pdf_path

        except Exception as e:
            logging.error(f"Error generating combined PDF: {e}")
            raise Exception(f"Combined PDF generation failed: {e}")
