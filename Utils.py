def get_annual_average(month_data, year):
    # Month data must be a list with 12 elements.
    year = int(year)
    if year % 4 == 0 and year not in [1800, 1900, 2100]:
        # Leap year.
        weights = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else:
        weights = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    # return weighted average,
    return sum([a * b for a, b in zip(month_data, weights)]) / sum(weights)