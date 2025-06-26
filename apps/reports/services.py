from django.db.models import Sum, Avg, Count, Q, F, Value, Case, When
from django.db.models.functions import TruncMonth, TruncWeek, Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from apps.budget.models import Budget, BudgetItem, IncomeItem, ExpenseItem
from apps.farms.models import Farm, Crop, Block, FarmerRecord, FieldTask
from apps.calendar.models import Activity, ActivityLog
from apps.inventory.models import Supply, StockMovement, Equipment, MaintenanceRecord
from apps.marketplace.models import Transaction, Product
from apps.accounts.models import Organization


class ReportService:
    def __init__(self, report_instance):
        self.report = report_instance
        self.date_from = report_instance.date_from
        self.date_to = report_instance.date_to
        self.filters = report_instance.filters or {}
        self.organization = report_instance.organization
        self.farm = report_instance.farm

    def generate_report_data(self):
        report_type = self.report.report_type
        
        if report_type in ['budget_vs_actual', 'profit_loss', 'cost_analysis', 'cash_flow', 'financial_summary']:
            return self._generate_financial_report()
        elif report_type in ['yield_analysis', 'crop_performance', 'seasonal_comparison', 'block_efficiency', 'farmer_performance']:
            return self._generate_production_report()
        elif report_type in ['activity_completion', 'task_management', 'equipment_utilization', 'inventory_report', 'staff_productivity']:
            return self._generate_operational_report()
        elif report_type in ['sales_performance', 'market_analysis', 'transaction_report', 'customer_analysis']:
            return self._generate_marketplace_report()
        elif report_type in ['executive_dashboard', 'kpi_scorecard', 'organization_overview']:
            return self._generate_executive_report()
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def _generate_financial_report(self):
        base_queryset = self._get_base_budget_queryset()
        
        if self.report.report_type == 'budget_vs_actual':
            return self._budget_vs_actual_analysis(base_queryset)
        elif self.report.report_type == 'profit_loss':
            return self._profit_loss_statement(base_queryset)
        elif self.report.report_type == 'cost_analysis':
            return self._cost_analysis_report(base_queryset)
        elif self.report.report_type == 'cash_flow':
            return self._cash_flow_report(base_queryset)
        elif self.report.report_type == 'financial_summary':
            return self._financial_summary_report(base_queryset)

    def _budget_vs_actual_analysis(self, base_queryset):
        budgets = base_queryset.prefetch_related('budget_items', 'income_items', 'expense_items')
        
        analysis_data = {
            'summary': {
                'total_budgets': budgets.count(),
                'budget_variance': Decimal('0'),
                'actual_vs_budget_percentage': 0
            },
            'budget_details': [],
            'variance_analysis': [],
            'monthly_breakdown': []
        }
        
        total_budgeted = Decimal('0')
        total_actual = Decimal('0')
        
        for budget in budgets:
            # Calculate budgeted amounts
            budgeted_income = budget.income_items.aggregate(
                total=Coalesce(Sum('amount'), Value(0))
            )['total']
            budgeted_expenses = budget.expense_items.aggregate(
                total=Coalesce(Sum('amount'), Value(0))
            )['total']
            budgeted_net = budgeted_income - budgeted_expenses
            
            # Calculate actual amounts (this would need to be implemented based on actual transaction records)
            actual_income = budget.income_items.filter(
                actual_amount__isnull=False
            ).aggregate(
                total=Coalesce(Sum('actual_amount'), Value(0))
            )['total']
            
            actual_expenses = budget.expense_items.filter(
                actual_amount__isnull=False
            ).aggregate(
                total=Coalesce(Sum('actual_amount'), Value(0))
            )['total']
            
            actual_net = actual_income - actual_expenses
            variance = actual_net - budgeted_net
            variance_percentage = (variance / budgeted_net * 100) if budgeted_net != 0 else 0
            
            budget_detail = {
                'budget_id': str(budget.id),
                'budget_name': budget.name,
                'period': f"{budget.start_date} to {budget.end_date}",
                'budgeted_income': float(budgeted_income),
                'actual_income': float(actual_income),
                'budgeted_expenses': float(budgeted_expenses),
                'actual_expenses': float(actual_expenses),
                'budgeted_net': float(budgeted_net),
                'actual_net': float(actual_net),
                'variance': float(variance),
                'variance_percentage': float(variance_percentage),
                'farm_name': budget.farm.name if budget.farm else None,
                'crop_name': budget.crop.name if budget.crop else None
            }
            
            analysis_data['budget_details'].append(budget_detail)
            total_budgeted += budgeted_net
            total_actual += actual_net
        
        # Overall summary
        total_variance = total_actual - total_budgeted
        analysis_data['summary']['budget_variance'] = float(total_variance)
        analysis_data['summary']['actual_vs_budget_percentage'] = float(
            (total_actual / total_budgeted * 100) if total_budgeted != 0 else 0
        )
        analysis_data['summary']['total_budgeted'] = float(total_budgeted)
        analysis_data['summary']['total_actual'] = float(total_actual)
        
        return analysis_data

    def _profit_loss_statement(self, base_queryset):
        budgets = base_queryset.prefetch_related('income_items', 'expense_items')
        
        pl_data = {
            'period': f"{self.date_from} to {self.date_to}",
            'revenue': {
                'total_revenue': 0,
                'revenue_breakdown': []
            },
            'expenses': {
                'total_expenses': 0,
                'expense_breakdown': []
            },
            'profitability': {
                'gross_profit': 0,
                'net_profit': 0,
                'profit_margin': 0
            },
            'monthly_breakdown': []
        }
        
        total_revenue = Decimal('0')
        total_expenses = Decimal('0')
        
        # Revenue analysis
        revenue_by_category = {}
        expense_by_category = {}
        
        for budget in budgets:
            for income_item in budget.income_items.all():
                category = income_item.category.name if income_item.category else 'Other'
                amount = income_item.actual_amount or income_item.amount
                if category not in revenue_by_category:
                    revenue_by_category[category] = Decimal('0')
                revenue_by_category[category] += amount
                total_revenue += amount
            
            for expense_item in budget.expense_items.all():
                category = expense_item.category.name if expense_item.category else 'Other'
                amount = expense_item.actual_amount or expense_item.amount
                if category not in expense_by_category:
                    expense_by_category[category] = Decimal('0')
                expense_by_category[category] += amount
                total_expenses += amount
        
        # Format revenue breakdown
        for category, amount in revenue_by_category.items():
            pl_data['revenue']['revenue_breakdown'].append({
                'category': category,
                'amount': float(amount),
                'percentage': float((amount / total_revenue * 100) if total_revenue > 0 else 0)
            })
        
        # Format expense breakdown
        for category, amount in expense_by_category.items():
            pl_data['expenses']['expense_breakdown'].append({
                'category': category,
                'amount': float(amount),
                'percentage': float((amount / total_expenses * 100) if total_expenses > 0 else 0)
            })
        
        # Calculate profitability metrics
        gross_profit = total_revenue - total_expenses
        pl_data['revenue']['total_revenue'] = float(total_revenue)
        pl_data['expenses']['total_expenses'] = float(total_expenses)
        pl_data['profitability']['gross_profit'] = float(gross_profit)
        pl_data['profitability']['net_profit'] = float(gross_profit)  # Simplified for now
        pl_data['profitability']['profit_margin'] = float(
            (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        )
        
        return pl_data

    def _cost_analysis_report(self, base_queryset):
        budgets = base_queryset.prefetch_related('expense_items')
        
        cost_data = {
            'summary': {
                'total_costs': 0,
                'cost_per_hectare': 0,
                'average_cost_per_budget': 0
            },
            'cost_breakdown': [],
            'cost_by_farm': [],
            'cost_by_crop': [],
            'cost_trends': []
        }
        
        total_costs = Decimal('0')
        total_hectares = Decimal('0')
        cost_by_category = {}
        cost_by_farm = {}
        cost_by_crop = {}
        
        for budget in budgets:
            budget_total = Decimal('0')
            
            for expense_item in budget.expense_items.all():
                amount = expense_item.actual_amount or expense_item.amount
                category = expense_item.category.name if expense_item.category else 'Other'
                
                # By category
                if category not in cost_by_category:
                    cost_by_category[category] = Decimal('0')
                cost_by_category[category] += amount
                
                # By farm
                if budget.farm:
                    farm_name = budget.farm.name
                    if farm_name not in cost_by_farm:
                        cost_by_farm[farm_name] = Decimal('0')
                    cost_by_farm[farm_name] += amount
                
                # By crop
                if budget.crop:
                    crop_name = budget.crop.name
                    if crop_name not in cost_by_crop:
                        cost_by_crop[crop_name] = Decimal('0')
                    cost_by_crop[crop_name] += amount
                
                budget_total += amount
                total_costs += amount
            
            # Calculate hectares if available
            if budget.farm:
                farm_hectares = budget.farm.blocks.aggregate(
                    total=Coalesce(Sum('size'), Value(0))
                )['total']
                total_hectares += farm_hectares or 0
        
        # Format cost breakdown
        for category, amount in cost_by_category.items():
            cost_data['cost_breakdown'].append({
                'category': category,
                'amount': float(amount),
                'percentage': float((amount / total_costs * 100) if total_costs > 0 else 0)
            })
        
        # Format cost by farm
        for farm, amount in cost_by_farm.items():
            cost_data['cost_by_farm'].append({
                'farm_name': farm,
                'amount': float(amount),
                'percentage': float((amount / total_costs * 100) if total_costs > 0 else 0)
            })
        
        # Format cost by crop
        for crop, amount in cost_by_crop.items():
            cost_data['cost_by_crop'].append({
                'crop_name': crop,
                'amount': float(amount),
                'percentage': float((amount / total_costs * 100) if total_costs > 0 else 0)
            })
        
        # Summary calculations
        cost_data['summary']['total_costs'] = float(total_costs)
        cost_data['summary']['cost_per_hectare'] = float(
            (total_costs / total_hectares) if total_hectares > 0 else 0
        )
        cost_data['summary']['average_cost_per_budget'] = float(
            (total_costs / budgets.count()) if budgets.count() > 0 else 0
        )
        
        return cost_data

    def _cash_flow_report(self, base_queryset):
        budgets = base_queryset.prefetch_related('income_items', 'expense_items')
        
        cash_flow_data = {
            'summary': {
                'opening_balance': 0,
                'total_inflows': 0,
                'total_outflows': 0,
                'net_cash_flow': 0,
                'closing_balance': 0
            },
            'monthly_cash_flow': [],
            'cash_flow_breakdown': {
                'inflows': [],
                'outflows': []
            }
        }
        
        total_inflows = Decimal('0')
        total_outflows = Decimal('0')
        
        # Aggregate cash flows
        inflow_categories = {}
        outflow_categories = {}
        
        for budget in budgets:
            for income_item in budget.income_items.all():
                amount = income_item.actual_amount or income_item.amount
                category = income_item.category.name if income_item.category else 'Other'
                if category not in inflow_categories:
                    inflow_categories[category] = Decimal('0')
                inflow_categories[category] += amount
                total_inflows += amount
            
            for expense_item in budget.expense_items.all():
                amount = expense_item.actual_amount or expense_item.amount
                category = expense_item.category.name if expense_item.category else 'Other'
                if category not in outflow_categories:
                    outflow_categories[category] = Decimal('0')
                outflow_categories[category] += amount
                total_outflows += amount
        
        # Format inflows
        for category, amount in inflow_categories.items():
            cash_flow_data['cash_flow_breakdown']['inflows'].append({
                'category': category,
                'amount': float(amount)
            })
        
        # Format outflows
        for category, amount in outflow_categories.items():
            cash_flow_data['cash_flow_breakdown']['outflows'].append({
                'category': category,
                'amount': float(amount)
            })
        
        # Summary
        net_cash_flow = total_inflows - total_outflows
        cash_flow_data['summary']['total_inflows'] = float(total_inflows)
        cash_flow_data['summary']['total_outflows'] = float(total_outflows)
        cash_flow_data['summary']['net_cash_flow'] = float(net_cash_flow)
        
        return cash_flow_data

    def _financial_summary_report(self, base_queryset):
        # Combine key metrics from other financial reports
        budget_analysis = self._budget_vs_actual_analysis(base_queryset)
        pl_statement = self._profit_loss_statement(base_queryset)
        cost_analysis = self._cost_analysis_report(base_queryset)
        cash_flow = self._cash_flow_report(base_queryset)
        
        summary_data = {
            'key_metrics': {
                'total_revenue': pl_statement['revenue']['total_revenue'],
                'total_expenses': pl_statement['expenses']['total_expenses'],
                'net_profit': pl_statement['profitability']['net_profit'],
                'profit_margin': pl_statement['profitability']['profit_margin'],
                'budget_variance': budget_analysis['summary']['budget_variance'],
                'cost_per_hectare': cost_analysis['summary']['cost_per_hectare'],
                'net_cash_flow': cash_flow['summary']['net_cash_flow']
            },
            'performance_indicators': {
                'budget_accuracy': abs(budget_analysis['summary']['actual_vs_budget_percentage']),
                'profitability_trend': 'positive' if pl_statement['profitability']['net_profit'] > 0 else 'negative',
                'cash_flow_status': 'positive' if cash_flow['summary']['net_cash_flow'] > 0 else 'negative'
            },
            'recommendations': self._generate_financial_recommendations(
                budget_analysis, pl_statement, cost_analysis, cash_flow
            )
        }
        
        return summary_data

    def _generate_financial_recommendations(self, budget_analysis, pl_statement, cost_analysis, cash_flow):
        recommendations = []
        
        # Budget variance recommendations
        if abs(budget_analysis['summary']['budget_variance']) > 10000:  # Threshold
            recommendations.append({
                'type': 'budget_variance',
                'priority': 'high',
                'message': 'Significant budget variance detected. Review budget planning process.'
            })
        
        # Profitability recommendations
        if pl_statement['profitability']['profit_margin'] < 10:  # Less than 10% margin
            recommendations.append({
                'type': 'profitability',
                'priority': 'medium',
                'message': 'Low profit margin. Consider cost optimization or revenue enhancement.'
            })
        
        # Cash flow recommendations
        if cash_flow['summary']['net_cash_flow'] < 0:
            recommendations.append({
                'type': 'cash_flow',
                'priority': 'high',
                'message': 'Negative cash flow. Review payment schedules and expense timing.'
            })
        
        return recommendations

    def _get_base_budget_queryset(self):
        queryset = Budget.objects.filter(
            start_date__gte=self.date_from,
            end_date__lte=self.date_to
        )
        
        # Apply user-based filtering
        user = getattr(self.report, 'created_by', None)
        if user:
            if user.is_superuser:
                # Superusers can see all budgets - no filtering applied
                pass
            elif hasattr(user, 'role') and user.role == 'farm_owner':
                # Farm owners see their own farms' budgets
                queryset = queryset.filter(farm__owner=user)
            elif self.organization:
                # Organization members see organization budgets
                queryset = queryset.filter(organization=self.organization)
            elif self.farm:
                # Specific farm filtering
                queryset = queryset.filter(farm=self.farm)
            else:
                # Check if user is assigned to any farm as staff
                try:
                    from apps.farms.models import FarmStaff
                    staff = FarmStaff.objects.get(user=user, is_active=True)
                    queryset = queryset.filter(farm=staff.farm)
                except:
                    queryset = queryset.none()
        
        # Apply farm-specific filtering if specified
        if self.farm:
            queryset = queryset.filter(farm=self.farm)
        
        # Apply additional filters
        if 'crop_id' in self.filters:
            queryset = queryset.filter(crop_id=self.filters['crop_id'])
        
        if 'budget_category' in self.filters:
            queryset = queryset.filter(budget_items__category__name=self.filters['budget_category'])
        
        return queryset.distinct()

    # Production Reports will be implemented next
    def _generate_production_report(self):
        if self.report.report_type == 'yield_analysis':
            return self._yield_analysis_report()
        elif self.report.report_type == 'crop_performance':
            return self._crop_performance_report()
        elif self.report.report_type == 'seasonal_comparison':
            return self._seasonal_comparison_report()
        elif self.report.report_type == 'block_efficiency':
            return self._block_efficiency_report()
        elif self.report.report_type == 'farmer_performance':
            return self._farmer_performance_report()

    def _yield_analysis_report(self):
        farmer_records = self._get_base_farmer_records_queryset()
        
        yield_data = {
            'summary': {
                'total_records': farmer_records.count(),
                'average_yield': 0,
                'total_production': 0,
                'yield_variance': 0
            },
            'yield_by_crop': [],
            'yield_by_block': [],
            'yield_trends': [],
            'performance_metrics': []
        }
        
        # Calculate yield metrics
        yield_stats = farmer_records.aggregate(
            avg_yield=Avg('actual_yield'),
            total_production=Sum('actual_yield'),
            avg_expected=Avg('expected_yield')
        )
        
        yield_data['summary']['average_yield'] = float(yield_stats['avg_yield'] or 0)
        yield_data['summary']['total_production'] = float(yield_stats['total_production'] or 0)
        
        # Yield variance (actual vs expected)
        if yield_stats['avg_expected']:
            yield_variance = ((yield_stats['avg_yield'] or 0) - yield_stats['avg_expected']) / yield_stats['avg_expected'] * 100
            yield_data['summary']['yield_variance'] = float(yield_variance)
        
        # Yield by crop
        crop_yields = farmer_records.values('crop__name').annotate(
            avg_yield=Avg('actual_yield'),
            total_yield=Sum('actual_yield'),
            record_count=Count('id')
        ).order_by('-avg_yield')
        
        for crop_data in crop_yields:
            yield_data['yield_by_crop'].append({
                'crop_name': crop_data['crop__name'],
                'average_yield': float(crop_data['avg_yield'] or 0),
                'total_yield': float(crop_data['total_yield'] or 0),
                'record_count': crop_data['record_count']
            })
        
        return yield_data

    def _get_base_farmer_records_queryset(self):
        queryset = FarmerRecord.objects.filter(
            harvest_date__gte=self.date_from,
            harvest_date__lte=self.date_to
        )
        
        # Apply user-based filtering
        user = getattr(self.report, 'created_by', None)
        if user:
            if user.is_superuser:
                # Superusers can see all farmer records - no filtering applied
                pass
            elif hasattr(user, 'role') and user.role == 'farm_owner':
                # Farm owners see their own farms' records
                queryset = queryset.filter(farm__owner=user)
            elif self.organization:
                # Organization members see organization records
                queryset = queryset.filter(farm__organization=self.organization)
            elif self.farm:
                # Specific farm filtering
                queryset = queryset.filter(farm=self.farm)
            else:
                # Check if user is assigned to any farm as staff
                try:
                    from apps.farms.models import FarmStaff
                    staff = FarmStaff.objects.get(user=user, is_active=True)
                    queryset = queryset.filter(farm=staff.farm)
                except:
                    queryset = queryset.none()
        
        # Apply farm-specific filtering if specified
        if self.farm:
            queryset = queryset.filter(farm=self.farm)
        
        return queryset

    def _crop_performance_report(self):
        farmer_records = self._get_base_farmer_records_queryset()
        
        performance_data = {
            'summary': {
                'total_crops': farmer_records.values('crop').distinct().count(),
                'average_performance': 0,
                'best_performing_crop': None,
                'performance_trends': []
            },
            'crop_metrics': [],
            'quality_indicators': [],
            'profitability_analysis': []
        }
        
        # Performance by crop
        crop_performance = farmer_records.values('crop__name').annotate(
            avg_yield=Avg('actual_yield'),
            avg_expected=Avg('expected_yield'),
            total_records=Count('id'),
            performance_ratio=Case(
                When(expected_yield__gt=0, then=F('actual_yield') / F('expected_yield')),
                default=Value(0)
            )
        ).order_by('-avg_yield')
        
        for crop_data in crop_performance:
            performance_data['crop_metrics'].append({
                'crop_name': crop_data['crop__name'],
                'average_yield': float(crop_data['avg_yield'] or 0),
                'expected_yield': float(crop_data['avg_expected'] or 0),
                'performance_ratio': float(crop_data['performance_ratio'] or 0),
                'record_count': crop_data['total_records']
            })
        
        return performance_data

    def _seasonal_comparison_report(self):
        farmer_records = self._get_base_farmer_records_queryset()
        
        seasonal_data = {
            'summary': {
                'seasons_compared': 0,
                'yield_variance': 0,
                'best_season': None
            },
            'season_comparisons': [],
            'monthly_trends': []
        }
        
        # Group by month for seasonal analysis
        monthly_yields = farmer_records.annotate(
            month=TruncMonth('harvest_date')
        ).values('month').annotate(
            avg_yield=Avg('actual_yield'),
            total_yield=Sum('actual_yield'),
            record_count=Count('id')
        ).order_by('month')
        
        for month_data in monthly_yields:
            seasonal_data['monthly_trends'].append({
                'month': month_data['month'].strftime('%Y-%m'),
                'average_yield': float(month_data['avg_yield'] or 0),
                'total_yield': float(month_data['total_yield'] or 0),
                'record_count': month_data['record_count']
            })
        
        return seasonal_data

    def _block_efficiency_report(self):
        farmer_records = self._get_base_farmer_records_queryset()
        
        efficiency_data = {
            'summary': {
                'total_blocks': 0,
                'average_efficiency': 0,
                'most_efficient_block': None
            },
            'block_performance': [],
            'efficiency_metrics': []
        }
        
        # Block performance analysis
        block_performance = farmer_records.values('block__name', 'block__size').annotate(
            avg_yield=Avg('actual_yield'),
            total_yield=Sum('actual_yield'),
            yield_per_hectare=F('total_yield') / F('block__size'),
            record_count=Count('id')
        ).order_by('-yield_per_hectare')
        
        for block_data in block_performance:
            efficiency_data['block_performance'].append({
                'block_name': block_data['block__name'],
                'block_size': float(block_data['block__size'] or 0),
                'average_yield': float(block_data['avg_yield'] or 0),
                'total_yield': float(block_data['total_yield'] or 0),
                'yield_per_hectare': float(block_data['yield_per_hectare'] or 0),
                'record_count': block_data['record_count']
            })
        
        return efficiency_data

    def _farmer_performance_report(self):
        farmer_records = self._get_base_farmer_records_queryset()
        
        farmer_data = {
            'summary': {
                'total_farmers': farmer_records.values('farmer').distinct().count(),
                'average_yield': 0,
                'top_performer': None
            },
            'farmer_rankings': [],
            'performance_distribution': []
        }
        
        # Farmer performance analysis
        farmer_performance = farmer_records.values('farmer__username', 'farmer__first_name', 'farmer__last_name').annotate(
            avg_yield=Avg('actual_yield'),
            total_yield=Sum('actual_yield'),
            record_count=Count('id')
        ).order_by('-avg_yield')
        
        for farmer in farmer_performance:
            farmer_data['farmer_rankings'].append({
                'farmer_name': f"{farmer['farmer__first_name']} {farmer['farmer__last_name']}".strip() or farmer['farmer__username'],
                'average_yield': float(farmer['avg_yield'] or 0),
                'total_yield': float(farmer['total_yield'] or 0),
                'record_count': farmer['record_count']
            })
        
        return farmer_data

    # Operational Reports Implementation
    def _generate_operational_report(self):
        if self.report.report_type == 'activity_completion':
            return self._activity_completion_report()
        elif self.report.report_type == 'task_management':
            return self._task_management_report()
        elif self.report.report_type == 'equipment_utilization':
            return self._equipment_utilization_report()
        elif self.report.report_type == 'inventory_report':
            return self._inventory_status_report()
        elif self.report.report_type == 'staff_productivity':
            return self._staff_productivity_report()

    def _activity_completion_report(self):
        activities = Activity.objects.filter(
            planned_date__gte=self.date_from,
            planned_date__lte=self.date_to
        )
        
        if self.organization:
            activities = activities.filter(calendar__farm__organization=self.organization)
        
        if self.farm:
            activities = activities.filter(calendar__farm=self.farm)
        
        activity_data = {
            'summary': {
                'total_activities': activities.count(),
                'completed_activities': activities.filter(status='completed').count(),
                'completion_rate': 0
            },
            'completion_by_type': [],
            'monthly_completion': []
        }
        
        # Calculate completion rate
        total = activity_data['summary']['total_activities']
        completed = activity_data['summary']['completed_activities']
        activity_data['summary']['completion_rate'] = (completed / total * 100) if total > 0 else 0
        
        # Completion by activity type
        completion_by_type = activities.values('activity_type').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed'))
        )
        
        for activity_type in completion_by_type:
            completion_rate = (activity_type['completed'] / activity_type['total'] * 100) if activity_type['total'] > 0 else 0
            activity_data['completion_by_type'].append({
                'activity_type': activity_type['activity_type'],
                'total': activity_type['total'],
                'completed': activity_type['completed'],
                'completion_rate': completion_rate
            })
        
        return activity_data

    def _equipment_utilization_report(self):
        equipment = Equipment.objects.all()
        
        if self.organization:
            equipment = equipment.filter(organization=self.organization)
        
        utilization_data = {
            'summary': {
                'total_equipment': equipment.count(),
                'active_equipment': equipment.filter(status='active').count(),
                'utilization_rate': 0
            },
            'equipment_status': [],
            'maintenance_schedule': []
        }
        
        # Equipment status breakdown
        status_breakdown = equipment.values('status').annotate(count=Count('id'))
        for status in status_breakdown:
            utilization_data['equipment_status'].append({
                'status': status['status'],
                'count': status['count']
            })
        
        # Recent maintenance records
        maintenance_records = MaintenanceRecord.objects.filter(
            date__gte=self.date_from,
            date__lte=self.date_to,
            equipment__in=equipment
        ).select_related('equipment')
        
        for record in maintenance_records[:10]:  # Limit to recent 10
            utilization_data['maintenance_schedule'].append({
                'equipment_name': record.equipment.name,
                'maintenance_type': record.maintenance_type,
                'date': record.date.strftime('%Y-%m-%d'),
                'cost': float(record.cost) if record.cost else 0
            })
        
        return utilization_data

    def _inventory_status_report(self):
        supplies = Supply.objects.all()
        stock_movements = StockMovement.objects.filter(
            date__gte=self.date_from,
            date__lte=self.date_to
        )
        
        if self.organization:
            supplies = supplies.filter(organization=self.organization)
            stock_movements = stock_movements.filter(supply__organization=self.organization)
        
        inventory_data = {
            'summary': {
                'total_supplies': supplies.count(),
                'low_stock_items': supplies.filter(current_stock__lte=F('minimum_stock')).count(),
                'total_movements': stock_movements.count()
            },
            'stock_levels': [],
            'recent_movements': []
        }
        
        # Stock levels by category
        stock_by_category = supplies.values('category__name').annotate(
            total_items=Count('id'),
            total_value=Sum(F('current_stock') * F('unit_price'))
        )
        
        for category in stock_by_category:
            inventory_data['stock_levels'].append({
                'category': category['category__name'],
                'total_items': category['total_items'],
                'total_value': float(category['total_value'] or 0)
            })
        
        return inventory_data

    def _task_management_report(self):
        tasks = FieldTask.objects.filter(
            date__gte=self.date_from,
            date__lte=self.date_to
        )
        
        if self.organization:
            tasks = tasks.filter(farm__organization=self.organization)
        
        if self.farm:
            tasks = tasks.filter(farm=self.farm)
        
        task_data = {
            'summary': {
                'total_tasks': tasks.count(),
                'completed_tasks': tasks.filter(status='completed').count(),
                'overdue_tasks': tasks.filter(status='overdue').count()
            },
            'task_by_status': [],
            'productivity_metrics': []
        }
        
        # Tasks by status
        status_breakdown = tasks.values('status').annotate(count=Count('id'))
        for status in status_breakdown:
            task_data['task_by_status'].append({
                'status': status['status'],
                'count': status['count']
            })
        
        return task_data

    def _staff_productivity_report(self):
        # This would require staff/worker models which aren't fully defined
        # Placeholder implementation
        return {
            'summary': {
                'total_staff': 0,
                'average_productivity': 0
            },
            'staff_metrics': [],
            'productivity_trends': []
        }

    # Marketplace Reports Implementation
    def _generate_marketplace_report(self):
        if self.report.report_type == 'sales_performance':
            return self._sales_performance_report()
        elif self.report.report_type == 'market_analysis':
            return self._market_analysis_report()
        elif self.report.report_type == 'transaction_report':
            return self._transaction_report()
        elif self.report.report_type == 'customer_analysis':
            return self._customer_analysis_report()

    def _sales_performance_report(self):
        transactions = Transaction.objects.filter(
            created_at__gte=self.date_from,
            created_at__lte=self.date_to,
            status='completed'
        )
        
        if self.organization:
            transactions = transactions.filter(product__user__profile__organization=self.organization)
        
        sales_data = {
            'summary': {
                'total_sales': transactions.aggregate(total=Sum('amount'))['total'] or 0,
                'transaction_count': transactions.count(),
                'average_sale': 0
            },
            'sales_by_product': [],
            'monthly_trends': []
        }
        
        # Calculate average sale
        if sales_data['summary']['transaction_count'] > 0:
            sales_data['summary']['average_sale'] = sales_data['summary']['total_sales'] / sales_data['summary']['transaction_count']
        
        # Sales by product
        product_sales = transactions.values('product__name').annotate(
            total_sales=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_sales')
        
        for product in product_sales:
            sales_data['sales_by_product'].append({
                'product_name': product['product__name'],
                'total_sales': float(product['total_sales']),
                'transaction_count': product['transaction_count']
            })
        
        return sales_data

    def _market_analysis_report(self):
        products = Product.objects.all()
        transactions = Transaction.objects.filter(
            created_at__gte=self.date_from,
            created_at__lte=self.date_to
        )
        
        market_data = {
            'summary': {
                'total_products': products.count(),
                'active_listings': products.filter(is_active=True).count(),
                'average_price': 0
            },
            'price_analysis': [],
            'market_trends': []
        }
        
        # Price analysis by category
        price_by_category = products.values('category__name').annotate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            product_count=Count('id')
        )
        
        for category in price_by_category:
            market_data['price_analysis'].append({
                'category': category['category__name'],
                'average_price': float(category['avg_price'] or 0),
                'min_price': float(category['min_price'] or 0),
                'max_price': float(category['max_price'] or 0),
                'product_count': category['product_count']
            })
        
        return market_data

    def _transaction_report(self):
        transactions = Transaction.objects.filter(
            created_at__gte=self.date_from,
            created_at__lte=self.date_to
        )
        
        transaction_data = {
            'summary': {
                'total_transactions': transactions.count(),
                'completed_transactions': transactions.filter(status='completed').count(),
                'total_value': transactions.aggregate(total=Sum('amount'))['total'] or 0
            },
            'transaction_by_status': [],
            'daily_transactions': []
        }
        
        # Transactions by status
        status_breakdown = transactions.values('status').annotate(
            count=Count('id'),
            total_value=Sum('amount')
        )
        
        for status in status_breakdown:
            transaction_data['transaction_by_status'].append({
                'status': status['status'],
                'count': status['count'],
                'total_value': float(status['total_value'] or 0)
            })
        
        return transaction_data

    def _customer_analysis_report(self):
        # Customer analysis would require user/customer models integration
        return {
            'summary': {
                'total_customers': 0,
                'active_customers': 0,
                'customer_retention': 0
            },
            'customer_segments': [],
            'purchase_patterns': []
        }

    # Executive Reports Implementation
    def _generate_executive_report(self):
        if self.report.report_type == 'executive_dashboard':
            return self._executive_dashboard_report()
        elif self.report.report_type == 'kpi_scorecard':
            return self._kpi_scorecard_report()
        elif self.report.report_type == 'organization_overview':
            return self._organization_overview_report()

    def _executive_dashboard_report(self):
        # Combine key metrics from all areas
        financial_summary = self._financial_summary_report(self._get_base_budget_queryset())
        production_summary = self._yield_analysis_report()
        operational_summary = self._activity_completion_report()
        
        executive_data = {
            'financial_overview': {
                'total_revenue': financial_summary['key_metrics']['total_revenue'],
                'net_profit': financial_summary['key_metrics']['net_profit'],
                'profit_margin': financial_summary['key_metrics']['profit_margin']
            },
            'production_overview': {
                'average_yield': production_summary['summary']['average_yield'],
                'total_production': production_summary['summary']['total_production'],
                'yield_variance': production_summary['summary']['yield_variance']
            },
            'operational_overview': {
                'completion_rate': operational_summary['summary']['completion_rate'],
                'total_activities': operational_summary['summary']['total_activities']
            },
            'key_insights': self._generate_executive_insights(financial_summary, production_summary, operational_summary)
        }
        
        return executive_data

    def _kpi_scorecard_report(self):
        kpi_data = {
            'financial_kpis': {
                'revenue_growth': 0,  # Would calculate year-over-year
                'profit_margin': 0,
                'cost_per_hectare': 0,
                'budget_variance': 0
            },
            'production_kpis': {
                'yield_efficiency': 0,
                'crop_success_rate': 0,
                'harvest_timing': 0
            },
            'operational_kpis': {
                'task_completion_rate': 0,
                'equipment_uptime': 0,
                'staff_productivity': 0
            },
            'overall_score': 0
        }
        
        # This would be calculated based on actual data and benchmarks
        return kpi_data

    def _organization_overview_report(self):
        organization_data = {
            'summary': {
                'total_farms': 0,
                'total_hectares': 0,
                'active_farmers': 0,
                'organization_performance': 0
            },
            'farm_distribution': [],
            'performance_metrics': []
        }
        
        if self.organization:
            farms = Farm.objects.filter(organization=self.organization)
            organization_data['summary']['total_farms'] = farms.count()
            organization_data['summary']['total_hectares'] = farms.aggregate(
                total=Sum('blocks__size')
            )['total'] or 0
        
        return organization_data

    def _generate_executive_insights(self, financial, production, operational):
        insights = []
        
        # Financial insights
        if financial['key_metrics']['profit_margin'] > 15:
            insights.append({
                'type': 'positive',
                'category': 'financial',
                'message': 'Strong profit margins indicate healthy financial performance'
            })
        elif financial['key_metrics']['profit_margin'] < 5:
            insights.append({
                'type': 'warning',
                'category': 'financial',
                'message': 'Low profit margins require attention to cost management'
            })
        
        # Production insights
        if production['summary']['yield_variance'] > 10:
            insights.append({
                'type': 'positive',
                'category': 'production',
                'message': 'Yields are exceeding expectations'
            })
        elif production['summary']['yield_variance'] < -10:
            insights.append({
                'type': 'warning',
                'category': 'production',
                'message': 'Yields are below expectations - review farming practices'
            })
        
        # Operational insights
        if operational['summary']['completion_rate'] > 90:
            insights.append({
                'type': 'positive',
                'category': 'operational',
                'message': 'Excellent task completion rate'
            })
        elif operational['summary']['completion_rate'] < 70:
            insights.append({
                'type': 'warning',
                'category': 'operational',
                'message': 'Task completion rate needs improvement'
            })
        
        return insights