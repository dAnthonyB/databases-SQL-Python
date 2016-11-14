--The total gifts by year and fund. This should be sorted first by year, then by fund ID.
--Return the year, fund ID, fund name, and total gifts.
SELECT date(gift_date, 'start of year') AS year, fund_id, fund_name, COUNT(gift_id) AS total_gifts
FROM gift
JOIN gift_fund_allocation USING (gift_id)
JOIN fund USING(fund_id)
GROUP BY fund_id, date(gift_date, 'start of year')
ORDER BY year, fund_id;

--The ‘top donors’ list: the 10 donors with the highest lifetime contributions across all funds.
-- Return their donor ID, name, and total gifts.
SELECT donor_id, donor_name, COUNT (DISTINCT gift_id) AS total_gifts
FROM donor
JOIN (SELECT donor_id, SUM(amount) AS total_amount
      FROM gift
      JOIN gift_fund_allocation USING (gift_id)
      GROUP BY donor_id
      ORDER BY total_amount DESC
      LIMIT 10)
  USING (donor_id)
JOIN gift USING (donor_id)
GROUP BY donor_id
ORDER BY total_amount DESC;

--For the year 2013, the donors to the ‘Veterinary Assistance’ fund with their total contributions to that fund for the year.
--List the donor ID, name, and funds contributed in 2013 to Veterinary Assistance.
SELECT donor_id, donor_name, total_amount
FROM donor
JOIN gift USING (donor_id)
JOIN gift_fund_allocation USING (gift_id)
JOIN (SELECT donor_id, SUM(amount) AS total_amount
      FROM gift
      JOIN gift_fund_allocation USING (gift_id)
      JOIN fund USING (fund_id)
      WHERE fund_name = 'Veterinary Assistance'
      GROUP BY donor_id
      HAVING date(gift_date, 'start of year') = '2013-01-01')
  USING (donor_id)
GROUP BY donor_id;

--The donors who have donated at least $10,000 since January 1, 2010 (donor ID, name, total gifts).
SELECT donor_id, donor_name, COUNT(gift_id) AS total_gifts
FROM donor
JOIN gift USING (donor_id)
JOIN gift_fund_allocation USING (gift_id)
JOIN (SELECT donor_id, SUM(amount) AS total_amount
      FROM gift
      JOIN gift_fund_allocation USING (gift_id)
      GROUP BY donor_id
      HAVING gift_date >= '2010-01-01')
  USING (donor_id)
GROUP BY donor_id;

--The names and e-mail addresses of all donors who contributed in the year 2012 (with no duplicates).
SELECT donor_name, donor_email
FROM donor
JOIN gift USING (donor_id)
WHERE date(gift_date, 'start of year') = '2012-01-01'
GROUP BY donor_id;