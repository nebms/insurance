"""
PDF quote generation using ReportLab.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import Quote


class PDFQuoteGenerator:
    """Generate PDF quotes."""

    def __init__(self, output_dir: str = "data/pdfs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles."""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=12,
            spaceBefore=12
        )

    def _add_single_pivot_equipment(self, story, quote):
        """Add single pivot equipment summary to PDF."""
        story.append(Paragraph("Equipment Coverage Summary", self.heading_style))

        equipment_data = [
            ['Description', 'Amount'],
            ['Pivot Equipment', f'${quote.pivot_amount:,.2f}'],
            ['Ancillary Equipment', f'${quote.ancillary_amount:,.2f}'],
            ['Submersible Pump/Panel', f'${quote.submersible_pump_amount:,.2f}'],
            ['Total Coverage', f'${quote.pivot_amount + quote.ancillary_amount + quote.submersible_pump_amount:,.2f}']
        ]

        equipment_table = Table(equipment_data, colWidths=[4*inch, 2*inch])
        equipment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 3), (-1, 3), 2, colors.HexColor('#1e3a8a')),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ]))
        story.append(equipment_table)
        story.append(Spacer(1, 0.25*inch))

    def _add_multi_pivot_equipment(self, story, quote):
        """Add multi-pivot itemized equipment list to PDF."""
        story.append(Paragraph(f"Equipment Items ({len(quote.line_items)} items)", self.heading_style))

        # Build equipment items table
        deductible_map = {1: '$500', 2: '$1,000', 3: '$2,500', 4: '$5,000'}

        equipment_data = [
            ['#', 'Pivot Amount', 'Age', 'Type', 'Deductible', 'Premium']
        ]

        total_pivot = 0
        total_ancillary = 0
        total_premium = 0

        for item in quote.line_items:
            # Calculate totals
            total_pivot += item.pivot_amount
            total_ancillary += item.ancillary_amount or 0
            total_premium += item.line_total_premium or 0

            # Equipment type
            type_parts = []
            if item.is_towable:
                type_parts.append("Towable")
            else:
                type_parts.append("Standard")
            if item.is_corner_or_long:
                type_parts.append("C/L")
            type_str = ", ".join(type_parts)

            # Add row
            equipment_data.append([
                str(item.line_number),
                f'${item.pivot_amount:,.0f}',
                f'{item.equipment_age_years}y',
                type_str,
                deductible_map.get(item.pivot_deductible_code, 'N/A'),
                f'${item.line_total_premium:,.2f}'
            ])

        # Add total row
        equipment_data.append([
            '', '', '', '', 'TOTAL:', f'${total_premium:,.2f}'
        ])

        equipment_table = Table(equipment_data, colWidths=[0.4*inch, 1.2*inch, 0.6*inch, 1.5*inch, 1*inch, 1.3*inch])
        equipment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -2), 1, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1e3a8a')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('SPAN', (0, -1), (4, -1)),
            ('ALIGN', (0, -1), (4, -1), 'RIGHT'),
        ]))
        story.append(equipment_table)
        story.append(Spacer(1, 0.25*inch))

        # Add coverage summary
        summary_data = [
            ['Total Pivot Coverage:', f'${total_pivot:,.2f}'],
            ['Total Ancillary Coverage:', f'${total_ancillary:,.2f}'],
            ['Combined Coverage:', f'${total_pivot + total_ancillary:,.2f}']
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.25*inch))

    def generate_quote_pdf(self, quote: Quote, customer_name: str = "") -> str:
        """
        Generate PDF for quote.

        Args:
            quote: Quote object
            customer_name: Customer name (optional)

        Returns:
            Path to generated PDF file
        """
        # Create filename
        filename = f"Quote_{quote.quote_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = self.output_dir / filename

        # Create document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Build content
        story = []

        # Header
        story.append(Paragraph("IRRIGATION EQUIPMENT", self.title_style))
        story.append(Paragraph("Insurance Quote", self.styles['Heading2']))
        story.append(Spacer(1, 0.25*inch))

        # Quote info
        quote_info_data = [
            ['Quote Number:', quote.quote_number, 'Date:', quote.quote_date],
            ['Customer:', customer_name or 'N/A', 'Agent:', quote.agent_name or 'N/A']
        ]

        quote_info_table = Table(quote_info_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 2*inch])
        quote_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(quote_info_table)
        story.append(Spacer(1, 0.25*inch))

        # Check if multi-pivot quote
        is_multi_pivot = quote.has_multiple_items()

        if is_multi_pivot:
            # Multi-pivot: Show itemized equipment list
            self._add_multi_pivot_equipment(story, quote)
        else:
            # Single pivot: Show traditional equipment summary
            self._add_single_pivot_equipment(story, quote)

        # Coverage Details
        story.append(Paragraph("Coverage Details", self.heading_style))

        if is_multi_pivot:
            # Multi-pivot: simplified coverage details
            coverage_data = [
                ['Location:', quote.state_code],
                ['Term:', f'{quote.term_months} months'],
                ['Number of Equipment Items:', str(len(quote.line_items))]
            ]

            coverage_table = Table(coverage_data, colWidths=[2.5*inch, 3.5*inch])
            coverage_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(coverage_table)
            story.append(Spacer(1, 0.25*inch))

            # Premium Summary (simple for multi-pivot)
            story.append(Paragraph("Premium Summary", self.heading_style))

            premium_data = [
                ['Description', 'Amount'],
                ['Total Annual Premium', f'${quote.total_premium:,.2f}']
            ]

            premium_table = Table(premium_data, colWidths=[4*inch, 2*inch])
            premium_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f3f4f6')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 12),
            ]))
            story.append(premium_table)
            story.append(Spacer(1, 0.25*inch))

        else:
            # Single pivot: detailed coverage and premium breakdown
            deductible_map = {1: '$500', 2: '$1,000', 3: '$2,500', 4: '$5,000'}
            pivot_ded = deductible_map.get(quote.pivot_deductible_code, 'N/A')
            anc_ded = deductible_map.get(quote.ancillary_deductible_code, 'N/A')

            coverage_data = [
                ['Location:', quote.state_code],
                ['Equipment Age:', f'{quote.equipment_age_years} years' + (' (New)' if quote.equipment_age_years == 0 else '')],
                ['Equipment Type:', 'Towable' if quote.is_towable else 'Standard'],
                ['Term:', f'{quote.term_months} months'],
                ['Pivot Deductible:', pivot_ded],
                ['Ancillary Deductible:', anc_ded],
                ['M&E Endorsement:', 'Yes (Pivot Only)' if quote.has_me_endorsement else 'No'],
            ]

            coverage_table = Table(coverage_data, colWidths=[2.5*inch, 3.5*inch])
            coverage_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(coverage_table)
            story.append(Spacer(1, 0.25*inch))

            # Premium Breakdown
            story.append(Paragraph("Premium Breakdown", self.heading_style))

            premium_data = [
                ['', 'Rate', 'Annual Premium'],
                ['Pivot Insurance', f'{quote.pivot_rate:.2f}%' if quote.pivot_rate else 'N/A',
                 f'${quote.pivot_premium:,.2f}' if quote.pivot_premium else '$0.00'],
                ['Ancillary Insurance', f'{quote.ancillary_rate:.2f}%' if quote.ancillary_rate else 'N/A',
                 f'${quote.ancillary_premium:,.2f}' if quote.ancillary_premium else '$0.00'],
                ['Additional Charges', '',
                 f'${quote.submersible_charge:,.2f}' if quote.submersible_charge else '$0.00'],
                ['TOTAL ANNUAL PREMIUM', '',
                 f'${quote.total_premium:,.2f}' if quote.total_premium else '$0.00']
            ]

            premium_table = Table(premium_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            premium_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('LINEABOVE', (0, 4), (-1, 4), 2, colors.HexColor('#1e3a8a')),
                ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#f3f4f6')),
                ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 4), (-1, 4), 12),
            ]))
            story.append(premium_table)
            story.append(Spacer(1, 0.25*inch))

        # Alternative Deductible Scenarios (only for single pivot)
        if not is_multi_pivot and (quote.alt1_premium is not None or quote.alt2_premium is not None):
            deductible_map = {1: '$500', 2: '$1,000', 3: '$2,500', 4: '$5,000'}
            pivot_ded = deductible_map.get(quote.pivot_deductible_code, 'N/A')
            story.append(Paragraph("Alternative Deductible Options", self.heading_style))

            # Build comparison table
            alt_data = [
                ['Option', 'Deductible', 'Rate', 'Annual Premium']
            ]

            # Selected option (current)
            alt_data.append([
                'Selected',
                pivot_ded,
                f'{quote.pivot_rate:.2f}%' if quote.pivot_rate else 'N/A',
                f'${quote.total_premium:,.2f}' if quote.total_premium else '$0.00'
            ])

            # Alternative 1
            if quote.alt1_premium is not None:
                alt1_ded = deductible_map.get(quote.alt1_deductible, 'N/A')
                alt_data.append([
                    'Option 2',
                    alt1_ded,
                    f'{quote.alt1_rate:.2f}%' if quote.alt1_rate else 'N/A',
                    f'${quote.alt1_premium:,.2f}'
                ])

            # Alternative 2
            if quote.alt2_premium is not None:
                alt2_ded = deductible_map.get(quote.alt2_deductible, 'N/A')
                alt_data.append([
                    'Option 3',
                    alt2_ded,
                    f'{quote.alt2_rate:.2f}%' if quote.alt2_rate else 'N/A',
                    f'${quote.alt2_premium:,.2f}'
                ])

            alt_table = Table(alt_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2*inch])
            alt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f9fafb')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ]))
            story.append(alt_table)

            # Add explanation note
            note_style = ParagraphStyle(
                'Note',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#6b7280'),
                spaceAfter=6,
                spaceBefore=6
            )
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                "<i>Note: Alternative options show pivot insurance premiums only. "
                "Ancillary and additional charges remain the same across all options.</i>",
                note_style
            ))
            story.append(Spacer(1, 0.3*inch))

        # Footer
        footer_text = [
            "• This quote is valid for 30 days from the date above.",
            "• Coverage subject to underwriting approval and policy terms.",
            "• For questions or to accept this quote, please contact your agent.",
        ]

        for text in footer_text:
            story.append(Paragraph(text, self.styles['Normal']))

        # Build PDF
        doc.build(story)

        return str(filepath)


# Test function
if __name__ == "__main__":
    from models.quote import Quote
    from datetime import date

    # Create test quote
    test_quote = Quote(
        id=1,
        quote_number="Q-00001",
        quote_date=str(date.today()),
        agent_name="Test Agent",
        pivot_amount=100000,
        ancillary_amount=0,
        submersible_pump_amount=0,
        equipment_age_years=0,
        is_towable=0,
        is_corner_or_long=0,
        has_me_endorsement=1,
        pivot_deductible_code=3,
        ancillary_deductible_code=2,
        term_months=12,
        state_code="OK",
        pivot_rate=1.95,
        ancillary_rate=1.95,
        pivot_premium=1950.00,
        ancillary_premium=0,
        submersible_charge=0,
        total_premium=1950.00
    )

    # Generate PDF
    generator = PDFQuoteGenerator()
    pdf_path = generator.generate_quote_pdf(test_quote, "Test Customer")
    print(f"✓ PDF generated: {pdf_path}")
