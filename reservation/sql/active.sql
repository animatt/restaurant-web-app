WITH viable_table_group AS (
  SELECT *, SUM(num_seating) OVER(PARTITION BY loc_type ORDER BY id, num_seating)
	   AS cumsum FROM timeline_location
) SELECT * FROM viable_table_group
   WHERE cumsum <= 20
   ORDER BY loc_type, cumsum;

SET @num := 0;
SELECT L.id, space_name, loc_type, num_seating,
       SUM(num_seating) OVER(
	 PARTITION BY space_name, loc_type, num_seating DESC
	 ORDER BY L.id
       )
	 AS cumsum
  FROM timeline_location L INNER JOIN timeline_space S ON L.space_id = S.id;

SET @num := 0, @loc := NULL;
SELECT L.id, space_name, loc_type, num_seating, (@num := @num + num_seating) tot
  FROM timeline_location L INNER JOIN timeline_space S ON L.space_id = S.id
 WHERE (@num + num_seating <= 10)
 ORDER BY space_name, loc_type, num_seating DESC;

SELECT L.id, space_name, loc_type, num_seating
  FROM timeline_location L INNER JOIN timeline_space S ON L.space_id = S.id
 ORDER BY space_name, loc_type, num_seating DESC;

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

DESCRIBE timeline_reservation;

SHOW TABLES;
