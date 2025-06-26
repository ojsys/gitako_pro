from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency_short(value):
    """
    Convert currency values to short format:
    1000 -> 1K
    1500000 -> 1.5M
    1000000000 -> 1B
    """
    if not value:
        return "₦0"
    
    try:
        # Convert to float for calculations
        num = float(value)
        
        if num == 0:
            return "₦0"
        
        # Handle negative numbers
        is_negative = num < 0
        num = abs(num)
        
        # Define units and their thresholds
        if num >= 1_000_000_000:  # Billions
            result = num / 1_000_000_000
            formatted = f"{result:.1f}B" if result != int(result) else f"{int(result)}B"
        elif num >= 1_000_000:  # Millions
            result = num / 1_000_000
            formatted = f"{result:.1f}M" if result != int(result) else f"{int(result)}M"
        elif num >= 1_000:  # Thousands
            result = num / 1_000
            formatted = f"{result:.1f}K" if result != int(result) else f"{int(result)}K"
        else:
            formatted = f"{num:.0f}"
        
        # Add negative sign back if needed
        if is_negative:
            formatted = f"-{formatted}"
        
        return f"₦{formatted}"
    
    except (ValueError, TypeError, AttributeError):
        return "₦0"


@register.filter  
def percentage_short(value):
    """
    Format percentage values with 1 decimal place
    """
    if not value:
        return "0%"
    
    try:
        num = float(value)
        if num == int(num):
            return f"{int(num)}%"
        else:
            return f"{num:.1f}%"
    except (ValueError, TypeError):
        return "0%"


@register.filter
def currency_format(value):
    """
    Format currency with commas and ₦ symbol
    Examples: 1000000 -> ₦1,000,000
    """
    if not value:
        return "₦0"
    
    try:
        num = float(value)
        return f"₦{num:,.0f}"
    except (ValueError, TypeError):
        return "₦0"


@register.filter
def subtract(value, arg):
    """
    Subtract arg from value
    Usage: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0