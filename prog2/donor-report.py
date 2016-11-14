import sys
import sqlite3
from contextlib import closing
import jinja2

engine = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

year = sys.argv[1]

# open the database connection
with closing(sqlite3.connect('charity.db')) as cxn:
    # next we need a cursor
    with closing(cxn.cursor()) as cur:
        # finds the table of donor_ids that donated in the given year
        cur.execute('''
            SELECT donor_id
            FROM donor
            JOIN gift USING (donor_id)
            WHERE date(gift_date, 'start of year') = ?
            GROUP BY donor_id
        ''', (year,))
        donor_ids = []

        #stores ids in list
        for donor_id in cur:
            donor_ids.append(donor_id)
        if donor_ids is None:
           print('Invalid year')
           sys.exit(1)
        users = 0
        #loops over every user
        for users in donor_ids:
            #gets user's contact info
            cur.execute('''
                SELECT donor_name, donor_address, donor_state, donor_city, donor_zip
                FROM donor
                WHERE donor_id = ?
            ''', users)

            #stores user's info
            donorInfo = cur.fetchone()
            donor_name=donorInfo[0]
            donor_address=donorInfo[1]
            donor_city=donorInfo[2]
            donor_state=donorInfo[3]
            donor_zip=donorInfo[4]

            #gets user's gift info
            cur.execute('''
                SELECT gift_date, fund_name, amount
                FROM gift
                JOIN gift_fund_allocation USING (gift_id)
                JOIN fund USING(fund_id)
                JOIN (SELECT donor_id
                      FROM donor
                      JOIN gift USING (donor_id)
                      WHERE donor_id = ?
                      GROUP BY donor_id) USING (donor_id)
                WHERE date(gift_date, 'start of year') = ?
                ORDER BY gift_date
            ''', (users[0], year,))
            #stores user's gift info
            byGift = []
            byGiftTotal = 0
            for date, name, amount in cur:
                byGift.append({'date': date, 'fund': name, 'amount': amount})
                byGiftTotal += amount

            #gets user's fund info
            cur.execute('''
                SELECT fund_name, SUM(amount) as total
                FROM gift
                JOIN gift_fund_allocation USING (gift_id)
                JOIN fund USING(fund_id)
                JOIN (SELECT donor_id
                      FROM donor
                      JOIN gift USING (donor_id)
                      WHERE donor_id = ?
                      GROUP BY donor_id) USING (donor_id)
                WHERE date(gift_date, 'start of year') = ?
                GROUP BY fund_name
                ORDER BY gift_date
            ''', (users[0], year,))
            byFund = []
            byFundTotal = 0
            for name, amount in cur:
                byFund.append({'fund': name, 'amount': amount})
                byFundTotal += amount

            template = engine.get_template('donationReport.html')
            with open('{}.html'.format(users[0]), 'w') as outf:
                    print(template.render(donor_name=donor_name, donor_address=donor_address,
                                          donor_city=donor_city, donor_state=donor_state,
                                          donor_zip=donor_zip, byGiftTotal=byGiftTotal,
                                          byFundTotal=byFundTotal, year=year[0:4],
                                          byGifts=byGift, byFunds=byFund),
                          file=outf)

