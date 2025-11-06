
COINS = [100, 50, 20, 10, 5]

def calc_change(amount_cents):
    """Return change as list of coins [5,10,20,50,100] in descending order counts flattened.
    We'll return list of coins (e.g. [100, 20, 5]) which matches requirement.
    """
    change = []
    remaining = amount_cents#130   #30
    for c in COINS:
        while remaining >= c:
            remaining -= c  #130-100    30
            change.append(c)
    return change
