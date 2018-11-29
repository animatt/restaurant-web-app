WITH viable_table_group AS (
  SELECT *, SUM(num_seating) OVER(PARTITION BY loc_type ORDER BY id, num_seating)
	   AS cumsum FROM timeline_location
) SELECT * FROM viable_table_group
   WHERE cumsum <= 20
   ORDER BY loc_type, cumsum;

SELECT L.id, space_name, loc_type, num_seating,
       SUM(num_seating) OVER(
	 PARTITION BY space_name, loc_type, num_seating DESC
	 ORDER BY L.id
       )
	 AS cumsum
  FROM
      timeline_location L
      INNER JOIN
      timeline_space S
	  ON L.space_id = S.id
      INNER JOIN
      timeline_transaction T
	  ON L.id = T.location_id
      INNER JOIN
      timeline_reservation R
	  ON T.reservation_id = R.id;

SELECT L.id, space_name, loc_type, num_seating
  FROM timeline_location L INNER JOIN timeline_space S ON L.space_id = S.id
 ORDER BY space_name, loc_type, num_seating DESC;


SELECT num_seating, SUM(num_seating)
  FROM (
    SELECT T.location_id, T.reservation_id, L.num_seating
      FROM timeline_location L
	     INNER JOIN timeline_transaction T
		 ON
		 L.id = T.location_id
  ) LT
	 INNER JOIN
	 timeline_reservation R
	     ON
	     R.id = LT.reservation_id
 WHERE res_datetime NOT BETWEEN %s AND %s
 GROUP BY num_seating ORDER BY num_seating DESC;

SELECT L.id, R.id, R.res_datetime, space_name, loc_type, num_seating
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
  -- GROUP BY L.id
 ORDER BY space_name, loc_type, num_seating DESC;

SELECT id, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined FROM auth_user;

SHOW TABLES;

START TRANSACTION;
-- customer_id and customer_name should come from django session
SET @customer_id = %s, @customer_name = %s, @num_menus = %s,
  @res_datetime = %s;
INSERT IGNORE INTO timeline_customer (id, vip, name) VALUES (
  %s, 0, %s
);
INSERT INTO timeline_reservation (
  num_menus, res_datetime, res_duration, customer_id
) VALUES (
  %s, %s, 60, %s
);
COMMIT;


SELECT * FROM timeline_transaction;

SELECT reservation_id, COUNT(reservations_id) FROM timeline_transaction GROUP BY reservation_id;

SELECT * FROM timeline_customer;

SELECT * FROM timeline_reservation;

SELECT * FROM timeline_transaction;

DESCRIBE timeline_customer;

DESCRIBE timeline_reservation;

DESCRIBE timeline_transaction;

DELETE FROM timeline_reservation WHERE id IN (5, 8, 9);

SHOW CREATE TABLE timeline_reservation;

SHOW TABLES;

SET
  @start = '2018-12-31 12:59:00.000000',
  @end = DATE_ADD('2018-12-31 12:59:00.000000', INTERVAL 1 HOUR);
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
