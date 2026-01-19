"""Bot-side pricing utilities.

This module provides pricing utilities for the bot, mirroring the API's
pricing constants and calculations.
"""

from decimal import ROUND_HALF_UP, Decimal

# Conversion constant: $1 = 1000 credits
CREDITS_PER_USD = 1000


def usd_to_credits(usd_amount: float | Decimal) -> int:
    """Convert USD amount to credits.
    
    Formula: credits = usd_amount * 1000
    
    Args:
        usd_amount: Price in USD (e.g., 0.027 for seedream-v4)
    
    Returns:
        Integer credit amount (e.g., 27 credits)
    
    Examples:
        >>> usd_to_credits(0.027)
        27
        >>> usd_to_credits(0.14)
        140
        >>> usd_to_credits(0.45)
        450
    """
    if isinstance(usd_amount, float):
        usd_amount = Decimal(str(usd_amount))
    credits = (usd_amount * Decimal(str(CREDITS_PER_USD))).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(credits)


def credits_to_usd(credits_amount: int) -> Decimal:
    """Convert credits to USD amount.
    
    Formula: usd = credits / 1000
    
    Args:
        credits_amount: Credit amount (e.g., 27)
    
    Returns:
        Decimal USD amount (e.g., 0.027)
    """
    return Decimal(str(credits_amount)) / Decimal(str(CREDITS_PER_USD))


def calculate_estimated_generations(balance: int, average_price: int) -> int:
    """Calculate estimated number of generations from balance.
    
    Args:
        balance: User's credit balance
        average_price: Average generation price in credits
    
    Returns:
        Estimated number of generations possible
    """
    if average_price <= 0:
        return 0
    return int(balance // average_price)
