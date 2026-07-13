"""Functions for calculating steps in exchanging currency.

Python numbers documentation: https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex

Overview of exchanging currency when travelling: https://www.compareremit.com/money-transfer-tips/guide-to-exchanging-currency-for-overseas-travel/
"""



def exchange_money(budget, exchange_rate):
    """Calculate estimated value after exchange."""
        
    quy_doi = int(budget / exchange_rate)

    return quy_doi



def get_change(budget, exchanging_value):
    """Calculate currency left after an exchange."""
    tien_mat = int(budget - exchanging_value)
    return tien_mat

def get_value_of_bills(denomination, number_of_bills):
    """Calculate the total value of currency at current denomination."""
    sum_bill= int(number_of_bills * denomination)
    return sum_bill
def get_number_of_bills(amount, denomination):
    """Calculate the number of currency units (bills) within the amount."""
    number_of_bills = int(amount / denomination)
    return number_of_bills


def get_leftover_of_bills(amount, denomination):
    """Calculate leftover amount after exchanging into bills."""
    leftover_of_bills = amount % denomination
    return leftover_of_bills


def exchangeable_value(budget, exchange_rate, spread, denomination):
    """Calculate the maximum value of the new currency."""
    exchange_rate_tax = (1 + spread / 100) * exchange_rate 
    after_exchange = budget / exchange_rate_tax
    bills = int(after_exchange // denomination)
    sum_max = int(denomination * bills)
    return sum_max