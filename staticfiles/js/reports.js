// Reports Module JavaScript

// Initialize reports functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeReports();
});

function initializeReports() {
    // Initialize chart loading if report data is available
    if (typeof reportData !== 'undefined') {
        loadReportCharts(reportData);
    }
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize export handlers
    initializeExportHandlers();
    
    // Initialize auto-refresh for generating reports
    initializeAutoRefresh();
}

// Chart loading functions
function loadReportCharts(data) {
    console.log('Loading report charts with data:', data);
    
    // Load different chart types based on report type
    if (window.location.pathname.includes('financial')) {
        loadFinancialCharts(data);
    } else if (window.location.pathname.includes('production')) {
        loadProductionCharts(data);
    } else if (window.location.pathname.includes('operational')) {
        loadOperationalCharts(data);
    }
}

function loadFinancialCharts(data) {
    // Revenue chart
    if (document.getElementById('revenueChart')) {
        const ctx = document.getElementById('revenueChart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.revenue ? data.revenue.breakdown?.map(item => item.category) || [] : [],
                datasets: [{
                    data: data.revenue ? data.revenue.breakdown?.map(item => item.amount) || [] : [],
                    backgroundColor: [
                        '#28a745', '#17a2b8', '#ffc107', '#fd7e14', '#6610f2',
                        '#e83e8c', '#20c997', '#6f42c1', '#fd7e14', '#28a745'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Expense chart
    if (document.getElementById('expenseChart')) {
        const ctx = document.getElementById('expenseChart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.expenses ? data.expenses.breakdown?.map(item => item.category) || [] : [],
                datasets: [{
                    data: data.expenses ? data.expenses.breakdown?.map(item => item.amount) || [] : [],
                    backgroundColor: [
                        '#dc3545', '#fd7e14', '#ffc107', '#6f42c1', '#e83e8c',
                        '#28a745', '#17a2b8', '#20c997', '#6610f2', '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

function loadProductionCharts(data) {
    // Yield chart
    if (document.getElementById('yieldChart')) {
        const ctx = document.getElementById('yieldChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.yield_by_crop ? data.yield_by_crop.map(item => item.crop_name) : [],
                datasets: [{
                    label: 'Average Yield (kg)',
                    data: data.yield_by_crop ? data.yield_by_crop.map(item => item.average_yield) : [],
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Seasonal chart
    if (document.getElementById('seasonalChart')) {
        const ctx = document.getElementById('seasonalChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.monthly_trends ? data.monthly_trends.map(item => item.month) : [],
                datasets: [{
                    label: 'Average Yield (kg)',
                    data: data.monthly_trends ? data.monthly_trends.map(item => item.average_yield) : [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

function loadOperationalCharts(data) {
    // Implementation for operational charts
    console.log('Loading operational charts:', data);
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Export handlers
function initializeExportHandlers() {
    // Export buttons
    document.querySelectorAll('[data-export-report]').forEach(button => {
        button.addEventListener('click', function() {
            const reportId = this.dataset.exportReport;
            const format = this.dataset.exportFormat;
            exportReport(reportId, format);
        });
    });
}

function exportReport(reportId, format) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/reports/${reportId}/export/`;
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     getCookie('csrftoken');
    
    if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
    }
    
    // Add format
    const formatInput = document.createElement('input');
    formatInput.type = 'hidden';
    formatInput.name = 'format';
    formatInput.value = format;
    form.appendChild(formatInput);
    
    // Submit form
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// Auto-refresh for generating reports
function initializeAutoRefresh() {
    const reportStatus = document.querySelector('.report-status');
    if (reportStatus && reportStatus.textContent.trim().toLowerCase() === 'generating') {
        setTimeout(() => {
            window.location.reload();
        }, 10000); // Refresh every 10 seconds
    }
}

// Utility functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showLoading(element) {
    if (element) {
        element.innerHTML = '<span class="loading-spinner"></span> Loading...';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

// Date range functions
function setDateRange(days) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);
    
    const dateFromField = document.getElementById('id_date_from');
    const dateToField = document.getElementById('id_date_to');
    
    if (dateFromField) dateFromField.value = formatDate(startDate);
    if (dateToField) dateToField.value = formatDate(endDate);
}

function setCurrentMonth() {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    const dateFromField = document.getElementById('id_date_from');
    const dateToField = document.getElementById('id_date_to');
    
    if (dateFromField) dateFromField.value = formatDate(startOfMonth);
    if (dateToField) dateToField.value = formatDate(endOfMonth);
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Report type information
function updateReportTypeInfo(reportType) {
    const reportTypeDescriptions = {
        'budget_vs_actual': {
            title: 'Budget vs Actual Analysis',
            description: 'Compare planned budget amounts with actual expenses and income to identify variances and performance.',
            features: ['Budget variance analysis', 'Percentage comparisons', 'Category breakdowns', 'Trend analysis']
        },
        'profit_loss': {
            title: 'Profit & Loss Statement',
            description: 'Comprehensive financial statement showing revenue, expenses, and net profit for the selected period.',
            features: ['Revenue breakdown', 'Expense categorization', 'Profit margins', 'Monthly comparisons']
        },
        'cost_analysis': {
            title: 'Cost Analysis Report',
            description: 'Detailed analysis of costs per hectare, crop, and category to optimize resource allocation.',
            features: ['Cost per hectare', 'Category analysis', 'Farm comparisons', 'Cost optimization insights']
        },
        'cash_flow': {
            title: 'Cash Flow Report',
            description: 'Track cash inflows and outflows to understand liquidity and cash management.',
            features: ['Cash flow statements', 'Monthly breakdowns', 'Liquidity analysis', 'Cash projections']
        },
        'yield_analysis': {
            title: 'Yield Analysis Report',
            description: 'Analyze crop yields across different blocks, seasons, and varieties to optimize production.',
            features: ['Yield comparisons', 'Block performance', 'Seasonal trends', 'Variety analysis']
        },
        'crop_performance': {
            title: 'Crop Performance Report',
            description: 'Comprehensive analysis of crop performance including yield, quality, and profitability.',
            features: ['Performance metrics', 'Quality indicators', 'Profitability analysis', 'Benchmarking']
        }
    };
    
    const infoDiv = document.getElementById('reportTypeInfo');
    if (infoDiv && reportType && reportTypeDescriptions[reportType]) {
        const info = reportTypeDescriptions[reportType];
        infoDiv.innerHTML = `
            <h6>${info.title}</h6>
            <p class="small text-muted">${info.description}</p>
            <h6 class="mt-3">Features:</h6>
            <ul class="small">
                ${info.features.map(feature => `<li>${feature}</li>`).join('')}
            </ul>
        `;
    } else if (infoDiv) {
        infoDiv.innerHTML = '<p class="text-muted">Select a report type to see details</p>';
    }
}

// Quick report generation
function generateQuickReport(reportType) {
    window.location.href = `/reports/create/?type=${reportType}&quick=1`;
}

// Global functions for template use
window.exportReport = exportReport;
window.setDateRange = setDateRange;
window.setCurrentMonth = setCurrentMonth;
window.updateReportTypeInfo = updateReportTypeInfo;
window.generateQuickReport = generateQuickReport;