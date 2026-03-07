"""
Visual Benefits Summary PDF Generator
Creates a professional PDF with charts, graphs, and detailed AI-CA benefits summary
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.widgets.markers import makeMarker
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional, List


class BenefitsPDFGenerator:
    """Generates visual Benefits Summary PDF with charts and graphs"""
    
    def __init__(self):
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.primary_color = colors.HexColor('#2563eb')
        self.success_color = colors.HexColor('#059669')
        self.warning_color = colors.HexColor('#d97706')
        self.danger_color = colors.HexColor('#dc2626')
        self.gray_color = colors.HexColor('#6b7280')
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='BenefitsMainTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1e40af'),
            alignment=1,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='BenefitsSectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f2937'),
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='BenefitsSubHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#374151'),
            spaceBefore=8,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='BenefitsBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='BenefitsCenterText',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.HexColor('#6b7280')
        ))
        
        self.styles.add(ParagraphStyle(
            name='BenefitsHighlightText',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#059669'),
            alignment=1,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='BenefitsSmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9ca3af')
        ))
    
    def _format_currency(self, amount: float) -> str:
        """Format amount in Indian number format"""
        if amount >= 10000000:
            return f"Rs.{amount/10000000:.2f} Cr"
        elif amount >= 100000:
            return f"Rs.{amount/100000:.2f} L"
        else:
            return f"Rs.{amount:,.0f}".replace(',', ',')
    
    def _create_bar_chart(self, data: List[tuple], title: str, width: int = 400, height: int = 200) -> Drawing:
        """Create a horizontal bar chart"""
        drawing = Drawing(width, height)
        
        chart = VerticalBarChart()
        chart.x = 60
        chart.y = 40
        chart.height = height - 80
        chart.width = width - 120
        
        values = [item[1] for item in data]
        labels = [item[0] for item in data]
        
        chart.data = [values]
        chart.categoryAxis.categoryNames = labels
        chart.categoryAxis.labels.fontName = 'Helvetica'
        chart.categoryAxis.labels.fontSize = 9
        chart.categoryAxis.labels.angle = 0
        
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(values) * 1.2 if values else 100
        chart.valueAxis.labels.fontName = 'Helvetica'
        chart.valueAxis.labels.fontSize = 8
        
        chart.bars[0].fillColor = self.primary_color
        chart.barWidth = 30
        chart.groupSpacing = 10
        
        drawing.add(chart)
        
        # Add title
        drawing.add(String(width/2, height-15, title, 
                          fontSize=11, fontName='Helvetica-Bold', 
                          fillColor=colors.HexColor('#1f2937'), textAnchor='middle'))
        
        return drawing
    
    def _create_comparison_chart(self, old_regime_tax: float, new_regime_tax: float, 
                                  width: int = 450, height: int = 180) -> Drawing:
        """Create a tax regime comparison bar chart"""
        drawing = Drawing(width, height)
        
        # Background
        drawing.add(Rect(0, 0, width, height, fillColor=colors.HexColor('#f9fafb'), 
                        strokeColor=colors.HexColor('#e5e7eb'), strokeWidth=1))
        
        # Title
        drawing.add(String(width/2, height-20, 'Tax Regime Comparison', 
                          fontSize=14, fontName='Helvetica-Bold', 
                          fillColor=colors.HexColor('#1f2937'), textAnchor='middle'))
        
        max_tax = max(old_regime_tax, new_regime_tax) or 1
        bar_max_width = width - 180
        
        # Old Regime Bar
        old_bar_width = (old_regime_tax / max_tax) * bar_max_width if max_tax > 0 else 0
        drawing.add(Rect(120, height-65, old_bar_width, 25, 
                        fillColor=colors.HexColor('#fbbf24'), strokeWidth=0))
        drawing.add(String(10, height-55, 'Old Regime:', fontSize=10, 
                          fontName='Helvetica-Bold', fillColor=colors.HexColor('#374151')))
        drawing.add(String(width-10, height-55, self._format_currency(old_regime_tax), 
                          fontSize=10, fontName='Helvetica-Bold', 
                          fillColor=colors.HexColor('#374151'), textAnchor='end'))
        
        # New Regime Bar
        new_bar_width = (new_regime_tax / max_tax) * bar_max_width if max_tax > 0 else 0
        drawing.add(Rect(120, height-105, new_bar_width, 25, 
                        fillColor=colors.HexColor('#3b82f6'), strokeWidth=0))
        drawing.add(String(10, height-95, 'New Regime:', fontSize=10, 
                          fontName='Helvetica-Bold', fillColor=colors.HexColor('#374151')))
        drawing.add(String(width-10, height-95, self._format_currency(new_regime_tax), 
                          fontSize=10, fontName='Helvetica-Bold', 
                          fillColor=colors.HexColor('#374151'), textAnchor='end'))
        
        # Savings indicator
        savings = abs(old_regime_tax - new_regime_tax)
        better_regime = "New Regime" if new_regime_tax < old_regime_tax else "Old Regime"
        drawing.add(Line(10, height-130, width-10, height-130, 
                        strokeColor=colors.HexColor('#e5e7eb'), strokeWidth=1))
        drawing.add(String(width/2, height-155, f'Savings with {better_regime}: {self._format_currency(savings)}', 
                          fontSize=12, fontName='Helvetica-Bold', 
                          fillColor=self.success_color, textAnchor='middle'))
        
        return drawing
    
    def _create_pie_chart(self, data: Dict[str, float], title: str, 
                          width: int = 300, height: int = 200) -> Drawing:
        """Create a pie chart for deduction breakdown"""
        drawing = Drawing(width, height)
        
        if not data or all(v == 0 for v in data.values()):
            drawing.add(String(width/2, height/2, 'No data available', 
                              fontSize=12, fillColor=self.gray_color, textAnchor='middle'))
            return drawing
        
        pie = Pie()
        pie.x = 50
        pie.y = 30
        pie.width = 100
        pie.height = 100
        
        # Filter out zero values
        filtered_data = {k: v for k, v in data.items() if v > 0}
        
        pie.data = list(filtered_data.values())
        pie.labels = list(filtered_data.keys())
        
        # Colors
        pie_colors = [
            colors.HexColor('#3b82f6'),
            colors.HexColor('#059669'),
            colors.HexColor('#f59e0b'),
            colors.HexColor('#ef4444'),
            colors.HexColor('#8b5cf6'),
            colors.HexColor('#ec4899'),
        ]
        
        for i, slice in enumerate(pie.slices):
            slice.fillColor = pie_colors[i % len(pie_colors)]
            slice.strokeWidth = 0.5
            slice.strokeColor = colors.white
        
        drawing.add(pie)
        
        # Title
        drawing.add(String(width/2, height-15, title, 
                          fontSize=11, fontName='Helvetica-Bold', 
                          fillColor=colors.HexColor('#1f2937'), textAnchor='middle'))
        
        # Legend
        legend_x = 170
        legend_y = height - 50
        for i, (label, value) in enumerate(filtered_data.items()):
            if i >= 5:  # Max 5 items in legend
                break
            y_pos = legend_y - (i * 18)
            drawing.add(Rect(legend_x, y_pos, 10, 10, 
                            fillColor=pie_colors[i % len(pie_colors)], strokeWidth=0))
            short_label = label[:15] + '...' if len(label) > 15 else label
            drawing.add(String(legend_x + 15, y_pos + 2, 
                              f'{short_label}: {self._format_currency(value)}', 
                              fontSize=8, fillColor=colors.HexColor('#4b5563')))
        
        return drawing
    
    def _create_stats_grid(self, stats: Dict[str, Any]) -> Table:
        """Create a visual stats grid"""
        data = [
            [
                self._create_stat_box("Total Income", self._format_currency(stats.get('gross_income', 0)), '#3b82f6'),
                self._create_stat_box("Total Tax", self._format_currency(stats.get('total_tax', 0)), '#ef4444'),
                self._create_stat_box("TDS Deducted", self._format_currency(stats.get('tds_deducted', 0)), '#f59e0b'),
            ],
            [
                self._create_stat_box("Documents", str(stats.get('documents_verified', 0)), '#8b5cf6'),
                self._create_stat_box("Regime", stats.get('recommended_regime', 'N/A'), '#059669'),
                self._create_stat_box(
                    "Refund/Payable",
                    self._format_currency(abs(stats.get('net_payable_refund', 0))),
                    '#059669' if stats.get('net_payable_refund', 0) >= 0 else '#ef4444'
                ),
            ]
        ]
        
        table = Table(data, colWidths=[170, 170, 170])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        return table
    
    def _create_stat_box(self, label: str, value: str, color: str) -> Table:
        """Create individual stat box"""
        data = [
            [Paragraph(f'{label}', self.styles['BenefitsCenterText'])],
            [Paragraph(f'<b>{value}</b>', ParagraphStyle('StatValue', parent=self.styles['Normal'], fontSize=14, alignment=1, textColor=colors.HexColor(color), fontName='Helvetica-Bold'))],
        ]
        
        box = Table(data, colWidths=[160])
        box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        return box
    
    def _create_benefit_item(self, icon: str, title: str, description: str, 
                             value: str, color: str) -> Table:
        """Create a benefit item row"""
        title_style = ParagraphStyle('BenefitTitle', parent=self.styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
        desc_style = ParagraphStyle('BenefitDesc', parent=self.styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'))
        value_style = ParagraphStyle('BenefitValue', parent=self.styles['Normal'], fontSize=11, alignment=2, textColor=colors.HexColor(color), fontName='Helvetica-Bold')
        icon_style = ParagraphStyle('BenefitIcon', parent=self.styles['Normal'], fontSize=14, textColor=colors.HexColor(color), fontName='Helvetica-Bold')
        
        data = [[
            Paragraph(icon, icon_style),
            Paragraph(f'{title}<br/>{description}', title_style),
            Paragraph(value, value_style)
        ]]
        
        table = Table(data, colWidths=[35, 330, 125])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        return table
    
    def generate_pdf(self, 
                    stats: Dict[str, Any],
                    computation: Optional[Dict[str, Any]] = None,
                    suggestions: Optional[Dict[str, Any]] = None,
                    user_name: str = "User") -> bytes:
        """Generate the complete Benefits Summary PDF"""
        
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        story = []
        
        # Title Section
        story.append(Paragraph("AI-CA Benefits Summary", self.styles['BenefitsMainTitle']))
        story.append(Paragraph(
            f"Generated for {user_name} | Financial Year: {stats.get('financial_year', 'N/A')}", 
            self.styles['BenefitsCenterText']
        ))
        story.append(Paragraph(
            f"Report Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
            self.styles['BenefitsCenterText']
        ))
        story.append(Spacer(1, 20))
        
        # Total Savings Highlight
        total_savings = 0
        if computation:
            total_savings += computation.get('tax_savings', 0)
        if suggestions:
            total_savings += suggestions.get('potential_savings', 0)
        
        savings_title_style = ParagraphStyle('SavingsTitle', parent=self.styles['Normal'], fontSize=12, alignment=1, textColor=colors.white)
        savings_value_style = ParagraphStyle('SavingsValue', parent=self.styles['Normal'], fontSize=28, alignment=1, textColor=colors.white, fontName='Helvetica-Bold')
        
        savings_box = Table([[
            Paragraph('Total Tax Savings with AI-CA', savings_title_style),
        ], [
            Paragraph(self._format_currency(total_savings), savings_value_style),
        ]], colWidths=[510])
        
        savings_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.success_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(savings_box)
        story.append(Spacer(1, 20))
        
        # Dashboard Statistics Section
        story.append(Paragraph("Your Financial Overview", self.styles['BenefitsSectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 10))
        story.append(self._create_stats_grid(stats))
        story.append(Spacer(1, 25))
        
        # Tax Regime Comparison (if computation exists)
        if computation:
            story.append(Paragraph("Tax Regime Analysis", self.styles['BenefitsSectionHeader']))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
            story.append(Spacer(1, 10))
            
            comparison_chart = self._create_comparison_chart(
                computation.get('old_regime_total_tax', 0),
                computation.get('new_regime_total_tax', 0)
            )
            story.append(comparison_chart)
            story.append(Spacer(1, 15))
            story.append(PageBreak())
            # Recommendation box
            rec_text = computation.get('recommendation_reason', 'No recommendation available')
            # Replace ₹ with Rs. since Helvetica doesn't support Unicode rupee symbol
            rec_text = rec_text.replace('₹', 'Rs.')
            rec_title_style = ParagraphStyle('RecTitle', parent=self.styles['Normal'], fontSize=11, fontName='Helvetica-Bold')
            rec_body_style = ParagraphStyle('RecBody', parent=self.styles['Normal'], fontSize=9, textColor=colors.HexColor('#374151'))
            
            rec_box = Table([[
                Paragraph(f'AI Recommendation: {computation.get("recommended_regime", "N/A")}', rec_title_style)
            ], [
                Paragraph(rec_text, rec_body_style)
            ]], colWidths=[510])
            
            rec_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecfdf5')),
                ('BOX', (0, 0), (-1, -1), 2, self.success_color),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(rec_box)
            story.append(Spacer(1, 20))
        
        # Investment Suggestions Section
        if suggestions and suggestions.get('suggestions'):
            story.append(Paragraph("AI Investment Suggestions", self.styles['BenefitsSectionHeader']))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
            story.append(Spacer(1, 10))
            
            # Potential savings highlight
            potential_savings = suggestions.get('potential_savings', 0)
            if potential_savings > 0:
                ps_text_style = ParagraphStyle('PSText', parent=self.styles['Normal'], fontSize=10, textColor=colors.HexColor('#1f2937'), alignment=1)
                ps_value_style = ParagraphStyle('PSValue', parent=self.styles['Normal'], fontSize=20, textColor=colors.HexColor('#059669'), fontName='Helvetica-Bold', alignment=1)
                
                ps_box = Table([[
                    Paragraph('Following these suggestions can save you an additional', ps_text_style),
                ], [
                    Paragraph(self._format_currency(potential_savings), ps_value_style),
                ]], colWidths=[510])
                
                ps_box.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bbf7d0')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(ps_box)
                story.append(Spacer(1, 15))
            
            # Individual suggestions
            sug_num_style = ParagraphStyle('SugNum', parent=self.styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'))
            sug_title_style = ParagraphStyle('SugTitle', parent=self.styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
            sug_desc_style = ParagraphStyle('SugDesc', parent=self.styles['Normal'], fontSize=9, textColor=colors.HexColor('#4b5563'))
            sug_savings_style = ParagraphStyle('SugSavings', parent=self.styles['Normal'], fontSize=8, textColor=colors.HexColor('#059669'))
            
            for i, suggestion in enumerate(suggestions.get('suggestions', [])[:5]):
                # Build suggestion content as separate paragraphs in nested table
                sug_content = Table([
                    [Paragraph(suggestion.get('section', 'Investment'), sug_title_style)],
                    [Paragraph(suggestion.get('suggestion', ''), sug_desc_style)],
                    [Paragraph(f'Potential Savings: {self._format_currency(suggestion.get("savings", 0))}', sug_savings_style)]
                ], colWidths=[470])
                sug_content.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
                
                sug_data = [[
                    Paragraph(f'{i+1}.', sug_num_style),
                    sug_content,
                ]]
                
                sug_table = Table(sug_data, colWidths=[30, 480])
                sug_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(sug_table)
                story.append(Spacer(1, 5))
            
            story.append(Spacer(1, 15))
        
        # Deduction Summary (if available)
        if suggestions and suggestions.get('deduction_summary'):
            deduction_summary = suggestions.get('deduction_summary', {})
            if deduction_summary:
                story.append(Paragraph("Deduction Utilization", self.styles['BenefitsSectionHeader']))
                story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
                story.append(Spacer(1, 10))
                
                # Create deduction table
                ded_data = [['Section', 'Claimed', 'Maximum Limit', 'Utilization']]
                
                for section, details in deduction_summary.items():
                    if isinstance(details, dict):
                        claimed = details.get('claimed', 0)
                        limit = details.get('limit', 0)
                        utilization = (claimed / limit * 100) if limit > 0 else 0
                        ded_data.append([
                            section,
                            self._format_currency(claimed),
                            self._format_currency(limit),
                            f"{utilization:.0f}%"
                        ])
                
                if len(ded_data) > 1:
                    ded_table = Table(ded_data, colWidths=[120, 120, 120, 100])
                    ded_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    story.append(ded_table)
                    story.append(Spacer(1, 25))
        
        # AI-CA Features Summary - wrapped in KeepTogether to prevent page split
        features_section = []
        features_section.append(Paragraph("AI-CA Features Used", self.styles['BenefitsSectionHeader']))
        features_section.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        features_section.append(Spacer(1, 10))
        
        features = [
            ("[Y]" if stats.get('documents_verified', 0) > 0 else "[-]", 
             "Document Verification", "Automated PAN and name matching", 
             f"{stats.get('documents_verified', 0)} verified", "#8b5cf6"),
            ("[Y]" if stats.get('documents_verified', 0) > 0 else "[-]", 
             "AI Data Extraction", "Intelligent parsing of Form 16, 26AS, AIS", 
             "Automated", "#3b82f6"),
            ("[Y]" if stats.get('tax_computed', False) else "[-]", 
             "Tax Calculation", "Both regime calculations with comparison", 
             "Completed" if stats.get('tax_computed') else "Pending", "#059669"),
            ("[Y]" if computation else "[-]", 
             "Regime Recommendation", "AI-powered analysis for optimal regime", 
             computation.get('recommended_regime', 'N/A') if computation else "N/A", "#f59e0b"),
            ("[Y]" if suggestions else "[-]", 
             "Investment Suggestions", "Personalized tax-saving recommendations", 
             f"{len(suggestions.get('suggestions', []))} tips" if suggestions else "N/A", "#ec4899"),
        ]
        
        for icon, title, desc, value, color in features:
            features_section.append(self._create_benefit_item(icon, title, desc, value, color))
            features_section.append(Spacer(1, 5))
        
        # Keep all features on same page
        story.append(KeepTogether(features_section))
        story.append(Spacer(1, 25))
        
        # Footer
        footer_style = ParagraphStyle('FooterText', parent=self.styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'), alignment=1)
        copyright_style = ParagraphStyle('CopyrightText', parent=self.styles['Normal'], fontSize=8, textColor=colors.HexColor('#9ca3af'), alignment=1)
        
        footer_text = "This report is generated by AI-CA (AI-Powered Virtual Chartered Accountant) for informational purposes only. Please consult a certified tax professional for official tax filing guidance."
        
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 10))
        story.append(Paragraph(footer_text, footer_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f'{datetime.now().year} AI-CA | All Rights Reserved', copyright_style))
        
        doc.build(story)
        
        return self.buffer.getvalue()


def generate_benefits_report(
    stats: Dict[str, Any],
    computation: Optional[Dict[str, Any]] = None,
    suggestions: Optional[Dict[str, Any]] = None,
    user_name: str = "User"
) -> bytes:
    """
    Main function to generate Benefits Summary PDF
    
    Args:
        stats: Dashboard statistics dict
        computation: Tax computation dict (optional)
        suggestions: Investment suggestions dict (optional)
        user_name: Name of the user
        
    Returns:
        PDF bytes
    """
    generator = BenefitsPDFGenerator()
    return generator.generate_pdf(stats, computation, suggestions, user_name)
