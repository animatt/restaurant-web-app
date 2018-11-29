SELECT L.id, space_name, loc_type, num_seating
  FROM
      timeline_location L
      INNER JOIN
      timeline_space S
	  ON L.space_id = S.id
      LEFT JOIN
      timeline_transaction T
	  ON L.id = T.location_id
      LEFT JOIN
      timeline_reservation R
      	  ON T.reservation_id = R.id
 WHERE (R.res_datetime NOT BETWEEN @start AND @end
	AND
	DATE_ADD(R.res_datetime, INTERVAL 1 HOUR) NOT BETWEEN @start AND @end)
    OR R.res_datetime IS NULL
 GROUP BY L.id
 ORDER BY space_name, loc_type, num_seating DESC;
