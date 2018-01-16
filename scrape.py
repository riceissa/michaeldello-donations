#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import csv
import sys
import datetime


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


def main():
    # We collect USD and AUD grants separately because the latter require more
    # columns to be printed.
    usd_grants = []
    aud_grants = []

    response = requests.get("http://www.michaeldello.com/donations-log/")
    soup = BeautifulSoup(response.content, "lxml")
    rows = soup.find("tbody").find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        donation_date, donation_date_precision = get_date(cols[0], cols[1])
        donee = cols[2]
        if cols[3].endswith("AUD"):
            aud_grants.append({

            })
        else:
            usd_grants.append({
            })
        (amount, amount_original_currency, original_currency) = get_amount(cols[3])
        notes = cols[4]

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


def get_date(year_col, date_col):
    """Get the date in YYYY-MM-DD format."""
    if date_col == "??":
        prec = "year"
        date = year_col + "-01-01"
    elif len(date_col) == 3:
        prec = "month"
        date = (year_col +
                datetime.datetime.strptime(date_col, "%b").strftime("%m-%d") +
                "-01")
    else:
        prec = "day"
        date = (year_col +
                datetime.datetime.strptime(date_col, "%b %d").strftime("%m-%d"))

    return (date, prec)


def get_amount(amount_col):
    """Get the amount."""
    if amount_col.endswith("AUD"):
        pass
    else:
        assert amount_col.endswith("US")


def aud_to_usd(aud_amount, date):
    """Convert the AUD amount to USD."""
    r = requests.get("https://api.fixer.io/{}?base=USD".format(date))
    j = r.json()
    rate = j["rates"]["AUD"]
    return aud_amount / rate

def converted_row():
    """Convert the given row to a SQL tuple."""

if __name__ == "__main__":
    main()
