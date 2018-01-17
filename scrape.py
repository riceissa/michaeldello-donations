#!/usr/bin/env python3
# License: CC0

import requests
from bs4 import BeautifulSoup
import csv
import sys
import datetime
import re


def main():
    # We collect USD and AUD grants separately because the latter require more
    # columns to be printed.
    usd_grants = []
    aud_grants = []

    response = requests.get("http://www.michaeldello.com/donations-log/")
    soup = BeautifulSoup(response.content, "lxml")
    rows = soup.find("tbody").find_all("tr")
    for row in rows:
        cols = list(map(lambda x: x.text.strip(), row.find_all("td")))
        if cols[3].endswith("AUD"):
            aud_grants.append(sql_tuple(cols))
        else:
            usd_grants.append(sql_tuple(cols))

    # Print USD grants
    first = True
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries,
    affected_regions) values""")
    for grant in usd_grants:
        print(("    " if first else "    ,") + grant)
        first = False
    print(";\n")

    # Print AUD grants
    first = True
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries,
    affected_regions, amount_original_currency, original_currency,
    currency_conversion_date, currency_conversion_basis) values""")
    for grant in aud_grants:
        print(("    " if first else "    ,") + grant)
        first = False
    print(";")


def mysql_quote(x):
    '''
    Quote the string x using MySQL quoting rules. If x is the empty string,
    return "NULL". Probably not safe against maliciously formed strings, but
    whatever; our input is fixed and from a basically trustable source..
    '''
    if not x:
        return "NULL"
    x = x.replace("\\", "\\\\")
    x = x.replace("'", "''")
    x = x.replace("\n", "\\n")
    return "'{}'".format(x)


def get_date(year_col, date_col):
    """Get the date in YYYY-MM-DD format."""
    if date_col in ["??", ""]:
        prec = "year"
        date = year_col + "-01-01"
    elif len(date_col) == 3:
        prec = "month"
        date = (year_col + "-" +
                datetime.datetime.strptime(date_col, "%b").strftime("%m") +
                "-01")
    else:
        prec = "day"
        date = (year_col + "-" +
                datetime.datetime.strptime(date_col, "%b %d").strftime("%m-%d"))

    return (date, prec)


def get_amount(amount_col, date):
    """Get the donation amount information as a tuple (amount,
    original_currency, amount_original_currency, currency_conversion_date). If
    the original currency is USD, only the first two values are filled."""
    if amount_col.endswith("AUD"):
        m = re.match(r"\$([0-9,]+) AUD", amount_col)
        return (aud_to_usd(float(m.group(1).replace(",", "")), date),
                "AUD", m.group(1), date)
    else:
        assert amount_col.endswith("US")
        m = re.match(r"\$([0-9,]+) US", amount_col)
        return (m.group(1).replace(",", ""), "USD", None, None)


def aud_to_usd(aud_amount, date):
    """Convert the AUD amount to USD."""
    r = requests.get("https://api.fixer.io/{}?base=USD".format(date))
    j = r.json()
    rate = j["rates"]["AUD"]
    return aud_amount / rate


def sql_tuple(cols):
    """Convert the given row to a SQL tuple."""
    donation_date, donation_date_precision = get_date(cols[0], cols[1])
    donee = cols[2]
    (amount,
     original_currency,
     amount_original_currency,
     currency_conversion_date) = get_amount(cols[3], donation_date)
    notes = cols[4]
    original_amount = []

    if original_amount == "AUD":
        original_amount = [
            str(amount_original_currency),  # amount_original_currency
            mysql_quote(original_currency),  # original_currency
            mysql_quote(currency_conversion_date),  # currency_conversion_date
            mysql_quote("Fixer.io"),  # currency_conversion_basis
        ]

    return ("(" + ",".join([
        mysql_quote("Michael Dello-Iacovo"),  # donor
        mysql_quote(donee),  # donee
        str(amount),  # amount
        mysql_quote(donation_date),  # donation_date
        mysql_quote(donation_date_precision),  # donation_date_precision
        mysql_quote("donation log"),  # donation_date_basis
        mysql_quote("FIXME"),  # cause_area
        mysql_quote("http://www.michaeldello.com/donations-log/"),  # url
        mysql_quote("FIXME"),  # donor_cause_area_url
        mysql_quote(notes),  # notes
        mysql_quote("FIXME"),  # affected_countries
        mysql_quote("FIXME"),  # affected_regions
    ] + original_amount) + ")")

if __name__ == "__main__":
    main()
