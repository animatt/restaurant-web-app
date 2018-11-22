SELECT num_seating, SUM(num_seating)
  FROM (
    SELECT T.location_id, T.reservations_id, L.num_seating
      FROM timeline_location L
	     INNER JOIN timeline_transaction T
		 ON
		 L.id = T.location_id
  ) LT
	 INNER JOIN
	 timeline_reservation R
	     ON
	     R.id = LT.reservations_id
 WHERE res_datetime NOT BETWEEN %s AND %s
 GROUP BY num_seating ORDER BY num_seating DESC;
