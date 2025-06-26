from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.loader import render_to_string
from django.conf import settings
import json
import csv
import io
from datetime import datetime, timedelta

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .models import Report, ReportCategory, ReportSchedule, ReportExport
from .services import ReportService
from .forms import ReportForm, ReportScheduleForm
from apps.accounts.models import Organization
from apps.farms.models import Farm


@login_required
def reports_dashboard(request):
    user_reports = Report.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    recent_exports = ReportExport.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    scheduled_reports = ReportSchedule.objects.filter(created_by=request.user, is_active=True)[:5]
    
    # Get report categories for quick access
    categories = ReportCategory.objects.filter(is_active=True)
    
    # Statistics
    stats = {
        'total_reports': Report.objects.filter(created_by=request.user).count(),
        'completed_reports': Report.objects.filter(created_by=request.user, status='completed').count(),
        'scheduled_reports': ReportSchedule.objects.filter(created_by=request.user, is_active=True).count(),
        'exports_this_month': ReportExport.objects.filter(
            created_by=request.user,
            created_at__month=timezone.now().month
        ).count()
    }
    
    context = {
        'user_reports': user_reports,
        'recent_exports': recent_exports,
        'scheduled_reports': scheduled_reports,
        'categories': categories,
        'stats': stats
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
def report_list(request):
    reports = Report.objects.filter(created_by=request.user)
    
    # Filtering
    category_id = request.GET.get('category')
    if category_id:
        reports = reports.filter(category_id=category_id)
    
    status = request.GET.get('status')
    if status:
        reports = reports.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        reports = reports.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(reports.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = ReportCategory.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_id,
        'current_status': status,
        'current_search': search
    }
    
    return render(request, 'reports/report_list.html', context)


@login_required
def create_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            
            # Set organization and farm based on user's role and access
            if request.user.is_superuser:
                # Superusers don't need organization constraint
                pass
            elif request.user.role == 'farm_owner':
                # Farm owners use their own organization if they have one
                if hasattr(request.user, 'profile') and request.user.profile.organization:
                    report.organization = request.user.profile.organization
            elif hasattr(request.user, 'profile') and request.user.profile.organization:
                # Organization members use their organization
                report.organization = request.user.profile.organization
            else:
                # Check if user is assigned to any farm as staff
                try:
                    from apps.farms.models import FarmStaff
                    staff = FarmStaff.objects.get(user=request.user, is_active=True)
                    if staff.farm.organization:
                        report.organization = staff.farm.organization
                except:
                    pass
            
            report.save()
            
            # Generate report asynchronously (in a real app, you'd use Celery)
            try:
                report.mark_as_generating()
                report_service = ReportService(report)
                data = report_service.generate_report_data()
                report.mark_as_completed(data)
                messages.success(request, 'Report generated successfully!')
            except Exception as e:
                report.mark_as_failed(str(e))
                messages.error(request, f'Report generation failed: {str(e)}')
            
            return redirect('reports:report_detail', report_id=report.id)
    else:
        form = ReportForm(user=request.user)
    
    context = {
        'form': form,
        'report_types': Report.REPORT_TYPES
    }
    
    return render(request, 'reports/create_report.html', context)


@login_required
def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    # Get available export formats for this report
    existing_exports = report.exports.all()
    available_formats = ReportExport.EXPORT_FORMATS
    
    context = {
        'report': report,
        'existing_exports': existing_exports,
        'available_formats': available_formats,
        'report_data': report.data if report.status == 'completed' else None
    }
    
    return render(request, 'reports/report_detail.html', context)


@login_required
@require_POST
def regenerate_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    try:
        report.mark_as_generating()
        report_service = ReportService(report)
        data = report_service.generate_report_data()
        report.mark_as_completed(data)
        messages.success(request, 'Report regenerated successfully!')
    except Exception as e:
        report.mark_as_failed(str(e))
        messages.error(request, f'Report regeneration failed: {str(e)}')
    
    return redirect('reports:report_detail', report_id=report.id)


@login_required
@require_POST
def delete_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    report.delete()
    messages.success(request, 'Report deleted successfully!')
    return redirect('reports:report_list')


@login_required
@require_POST
def export_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    export_format = request.POST.get('format')
    
    if export_format not in dict(ReportExport.EXPORT_FORMATS):
        messages.error(request, 'Invalid export format')
        return redirect('reports:report_detail', report_id=report.id)
    
    # Check if export already exists
    existing_export = report.exports.filter(export_format=export_format).first()
    if existing_export and existing_export.status == 'completed':
        return redirect('reports:download_export', export_id=existing_export.id)
    
    # Create new export
    export_obj = ReportExport.objects.create(
        report=report,
        export_format=export_format,
        created_by=request.user
    )
    
    try:
        # Generate export file with proper format handling
        file_path = f"exports/{report.id}_{export_format}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        if export_format == 'json':
            file_content = json.dumps(report.data, indent=2)
            file_path += '.json'
            content_type = 'application/json'
        elif export_format == 'csv':
            # Generate proper CSV from report data
            file_content = _generate_csv_content(report.data, report.report_type)
            file_path += '.csv'
            content_type = 'text/csv'
        elif export_format == 'excel':
            # Generate Excel format (placeholder - would need openpyxl)
            file_content = _generate_excel_content(report.data, report.report_type)
            file_path += '.xlsx'
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif export_format == 'pdf':
            # Generate PDF format (placeholder - would need reportlab)
            file_content = _generate_pdf_content(report.data, report.report_type, report)
            file_path += '.pdf'
            content_type = 'application/pdf'
        else:
            file_content = json.dumps(report.data, indent=2)
            file_path += '.json'
            content_type = 'application/json'
        
        # Store the content for download (in a real app, save to file storage)
        if isinstance(file_content, bytes):
            # For binary content like PDF, we need to handle it differently
            import base64
            export_obj.file_content = base64.b64encode(file_content).decode('utf-8')
            export_obj.content_type = content_type
            export_obj.mark_as_completed(file_path, len(file_content))
        else:
            # For text content like CSV, JSON
            export_obj.file_content = file_content
            export_obj.content_type = content_type
            export_obj.mark_as_completed(file_path, len(file_content.encode('utf-8')))
        
        messages.success(request, f'Report exported to {export_format.upper()} successfully!')
        return redirect('reports:download_export', export_id=export_obj.id)
        
    except Exception as e:
        export_obj.mark_as_failed(str(e))
        messages.error(request, f'Export failed: {str(e)}')
        return redirect('reports:report_detail', report_id=report.id)


@login_required
def download_export(request, export_id):
    export_obj = get_object_or_404(ReportExport, id=export_id, created_by=request.user)
    
    if export_obj.status != 'completed':
        messages.error(request, 'Export is not ready for download')
        return redirect('reports:report_detail', report_id=export_obj.report.id)
    
    # Serve the actual file content based on format
    file_content = getattr(export_obj, 'file_content', None)
    content_type = getattr(export_obj, 'content_type', 'application/json')
    
    if not file_content:
        # Fallback to JSON if no content stored
        file_content = json.dumps(export_obj.report.data, indent=2)
        content_type = 'application/json'
        filename = f"{export_obj.report.name}.json"
    else:
        # Determine filename based on format
        format_extensions = {
            'application/json': '.json',
            'text/csv': '.csv', 
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/pdf': '.pdf'
        }
        extension = format_extensions.get(content_type, '.json')
        filename = f"{export_obj.report.name}{extension}"
        
        # Handle binary content (PDF) that was base64 encoded
        if content_type == 'application/pdf':
            try:
                import base64
                file_content = base64.b64decode(file_content)
            except:
                # If decoding fails, treat as text
                pass
    
    response = HttpResponse(file_content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def financial_reports(request):
    financial_categories = ReportCategory.objects.filter(category_type='financial', is_active=True)
    recent_reports = Report.objects.filter(
        created_by=request.user,
        category__category_type='financial'
    ).order_by('-created_at')[:10]
    
    # Quick stats for financial reports
    stats = {
        'total_financial_reports': Report.objects.filter(
            created_by=request.user, category__category_type='financial'
        ).count(),
        'completed_this_month': Report.objects.filter(
            created_by=request.user,
            category__category_type='financial',
            status='completed',
            created_at__month=timezone.now().month
        ).count()
    }
    
    context = {
        'categories': financial_categories,
        'recent_reports': recent_reports,
        'stats': stats,
        'report_type': 'financial'
    }
    
    return render(request, 'reports/financial_reports.html', context)


@login_required
def production_reports(request):
    production_categories = ReportCategory.objects.filter(category_type='production', is_active=True)
    recent_reports = Report.objects.filter(
        created_by=request.user,
        category__category_type='production'
    ).order_by('-created_at')[:10]
    
    stats = {
        'total_production_reports': Report.objects.filter(
            created_by=request.user, category__category_type='production'
        ).count(),
        'completed_this_month': Report.objects.filter(
            created_by=request.user,
            category__category_type='production',
            status='completed',
            created_at__month=timezone.now().month
        ).count()
    }
    
    context = {
        'categories': production_categories,
        'recent_reports': recent_reports,
        'stats': stats,
        'report_type': 'production'
    }
    
    return render(request, 'reports/production_reports.html', context)


@login_required
def executive_dashboard(request):
    # Get key performance indicators
    kpi_data = {
        'total_farms': Farm.objects.filter(
            organization=getattr(request.user.profile, 'organization', None)
        ).count() if hasattr(request.user, 'profile') else 0,
        'active_reports': Report.objects.filter(created_by=request.user, status='completed').count(),
        'monthly_revenue': 0,  # Would be calculated from actual data
        'profit_margin': 0,    # Would be calculated from actual data
    }
    
    # Recent activity
    recent_reports = Report.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    
    context = {
        'kpi_data': kpi_data,
        'recent_reports': recent_reports
    }
    
    return render(request, 'reports/executive_dashboard.html', context)


@login_required
def report_api_data(request, report_id):
    """API endpoint to get report data for AJAX requests"""
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    if report.status != 'completed':
        return JsonResponse({
            'status': 'error',
            'message': 'Report is not completed yet'
        })
    
    return JsonResponse({
        'status': 'success',
        'data': report.data,
        'report_type': report.report_type,
        'generated_at': report.generated_at.isoformat() if report.generated_at else None
    })


# Report Scheduling Views
@login_required
def schedule_list(request):
    schedules = ReportSchedule.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'schedules': schedules
    }
    
    return render(request, 'reports/schedule_list.html', context)


@login_required
def create_schedule(request):
    if request.method == 'POST':
        form = ReportScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            
            if hasattr(request.user, 'profile') and request.user.profile.organization:
                schedule.organization = request.user.profile.organization
            
            schedule.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Report schedule created successfully!')
            return redirect('reports:schedule_list')
    else:
        form = ReportScheduleForm(user=request.user)
    
    context = {
        'form': form
    }
    
    return render(request, 'reports/create_schedule.html', context)


# Helper functions for export format generation
def _generate_csv_content(data, report_type):
    """Generate CSV content from report data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type in ['budget_vs_actual', 'profit_loss', 'cost_analysis', 'cash_flow', 'financial_summary']:
        # Financial reports CSV
        writer.writerow(['Report Type', 'Financial Report'])
        writer.writerow(['Generated At', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])  # Empty row
        
        if 'summary' in data:
            writer.writerow(['Summary'])
            for key, value in data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])
        
        if 'budget_details' in data:
            writer.writerow(['Budget Details'])
            writer.writerow(['Budget Name', 'Budgeted Income', 'Actual Income', 'Budgeted Expenses', 'Actual Expenses', 'Variance'])
            for detail in data['budget_details']:
                writer.writerow([
                    detail.get('budget_name', ''),
                    detail.get('budgeted_income', 0),
                    detail.get('actual_income', 0),
                    detail.get('budgeted_expenses', 0),
                    detail.get('actual_expenses', 0),
                    detail.get('variance', 0)
                ])
    
    elif report_type in ['yield_analysis', 'crop_performance']:
        # Production reports CSV  
        writer.writerow(['Report Type', 'Production Report'])
        writer.writerow(['Generated At', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        if 'yield_by_crop' in data:
            writer.writerow(['Yield by Crop'])
            writer.writerow(['Crop Name', 'Average Yield', 'Total Yield', 'Record Count'])
            for crop in data['yield_by_crop']:
                writer.writerow([
                    crop.get('crop_name', ''),
                    crop.get('average_yield', 0),
                    crop.get('total_yield', 0),
                    crop.get('record_count', 0)
                ])
    
    else:
        # Generic CSV format
        writer.writerow(['Report Data'])
        writer.writerow(['Generated At', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list) and v and isinstance(v[0], dict):
                    # Handle list of dictionaries
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flattened = flatten_dict(data)
        for key, value in flattened.items():
            writer.writerow([key.replace('_', ' ').title(), value])
    
    return output.getvalue()


def _generate_excel_content(data, report_type):
    """Generate Excel content from report data (placeholder)"""
    # This would require openpyxl library
    # For now, return CSV-like content as text
    return f"Excel format not yet implemented. Report Type: {report_type}\nData: {json.dumps(data, indent=2)}"


def _generate_pdf_content(data, report_type, report):
    """Generate PDF content from report data using ReportLab"""
    if not REPORTLAB_AVAILABLE:
        # Fallback to text if ReportLab is not available
        content = f"""
        Report: {report.name}
        Type: {report.get_report_type_display()}
        Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        Period: {report.date_from} to {report.date_to}
        
        Data Summary:
        {json.dumps(data, indent=2)}
        
        Note: ReportLab not available. Install with: pip install reportlab
        """
        return content.encode('utf-8')
    
    # Create PDF using ReportLab
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                               topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#007bff')
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#007bff')
        )
        
        # Build story (content)
        story = []
        
        # Title
        story.append(Paragraph(report.name, title_style))
        story.append(Paragraph(report.get_report_type_display(), styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Report info
        info_data = [
            ['Report Period:', f"{report.date_from} to {report.date_to}"],
            ['Generated:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Farm:', report.farm.name if report.farm else 'All farms'],
        ]
        if report.description:
            info_data.append(['Description:', report.description])
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Add content based on report type
        if report_type in ['budget_vs_actual', 'profit_loss', 'cost_analysis', 'cash_flow', 'financial_summary']:
            story.extend(_build_financial_pdf_content(data, styles, heading_style))
        elif report_type in ['yield_analysis', 'crop_performance', 'seasonal_comparison', 'block_efficiency', 'farmer_performance']:
            story.extend(_build_production_pdf_content(data, styles, heading_style))
        else:
            # Generic content
            story.append(Paragraph("Report Data", heading_style))
            story.append(Paragraph(json.dumps(data, indent=2), styles['Code']))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        # Fallback to simple text if PDF generation fails
        error_content = f"""
        PDF Generation Error: {str(e)}
        
        Report: {report.name}
        Type: {report.get_report_type_display()}
        Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        Period: {report.date_from} to {report.date_to}
        
        Data:
        {json.dumps(data, indent=2)}
        """
        return error_content.encode('utf-8')


def _build_financial_pdf_content(data, styles, heading_style):
    """Build PDF content for financial reports"""
    story = []
    
    # Summary section
    if 'summary' in data:
        story.append(Paragraph("Summary", heading_style))
        summary_data = []
        for key, value in data['summary'].items():
            label = key.replace('_', ' ').title()
            if any(term in key.lower() for term in ['amount', 'revenue', 'expense', 'profit', 'cost', 'variance']):
                formatted_value = f"${value:,.2f}"
            elif any(term in key.lower() for term in ['percentage', 'margin']):
                formatted_value = f"{value:.1f}%"
            else:
                formatted_value = str(value)
            summary_data.append([label, formatted_value])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
    
    # Budget details
    if 'budget_details' in data and data['budget_details']:
        story.append(Paragraph("Budget Analysis", heading_style))
        budget_data = [['Budget', 'Budgeted Income', 'Actual Income', 'Budgeted Expenses', 'Actual Expenses', 'Variance']]
        for detail in data['budget_details']:
            budget_data.append([
                detail.get('budget_name', ''),
                f"${detail.get('budgeted_income', 0):,.2f}",
                f"${detail.get('actual_income', 0):,.2f}",
                f"${detail.get('budgeted_expenses', 0):,.2f}",
                f"${detail.get('actual_expenses', 0):,.2f}",
                f"${detail.get('variance', 0):,.2f}"
            ])
        
        budget_table = Table(budget_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        story.append(budget_table)
        story.append(Spacer(1, 20))
    
    return story


def _build_production_pdf_content(data, styles, heading_style):
    """Build PDF content for production reports"""
    story = []
    
    # Summary section
    if 'summary' in data:
        story.append(Paragraph("Production Summary", heading_style))
        summary_data = []
        for key, value in data['summary'].items():
            label = key.replace('_', ' ').title()
            if 'yield' in key.lower() or 'production' in key.lower():
                formatted_value = f"{value:,.2f} kg"
            elif 'variance' in key.lower():
                formatted_value = f"{value:.1f}%"
            else:
                formatted_value = str(value)
            summary_data.append([label, formatted_value])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
    
    # Yield by crop
    if 'yield_by_crop' in data and data['yield_by_crop']:
        story.append(Paragraph("Yield by Crop", heading_style))
        crop_data = [['Crop', 'Average Yield (kg)', 'Total Yield (kg)', 'Records']]
        for crop in data['yield_by_crop']:
            crop_data.append([
                crop.get('crop_name', ''),
                f"{crop.get('average_yield', 0):,.2f}",
                f"{crop.get('total_yield', 0):,.2f}",
                str(crop.get('record_count', 0))
            ])
        
        crop_table = Table(crop_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        crop_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        story.append(crop_table)
        story.append(Spacer(1, 20))
    
    return story