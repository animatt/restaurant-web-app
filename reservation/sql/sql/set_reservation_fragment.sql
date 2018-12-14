SET @customer_app_id = %s, @customer_name = %s, @num_menus = %s, @res_datetime = %s;
SELECT L.id, space_name, loc_type, num_seating FROM timeline_location L INNER JOIN timeline_space S ON L.space_id = S.id LEFT JOIN timeline_transaction T ON L.id = T.location_id LEFT JOIN timeline_reservation R ON T.reservation_id = R.id WHERE ((R.res_datetime NOT BETWEEN @res_datetime AND DATE_ADD(@start, INTERVAL 1 HOUR) AND DATE_ADD(R.res_datetime, INTERVAL 1 HOUR) NOT BETWEEN @res_datetime AND DATE_ADD(@start, INTERVAL 1 HOUR)) OR R.res_datetime IS NULL) AND L.id IN ({}) GROUP BY L.id ORDER BY space_name, loc_type, num_seating DESC FOR UPDATE;
INSERT IGNORE INTO timeline_customer (vip, name, phone, app_id) VALUES (0, @customer_name, '', @customer_app_id);
SELECT id FROM timeline_customer WHERE app_id = @customer_app_id INTO @customer_id;
INSERT INTO timeline_reservation (num_menus, res_datetime, res_duration, res_requested, customer_id, confirmed) VALUES (@num_menus, @res_datetime, 60, UTC_TIMESTAMP(), @customer_id, 0);
SELECT LAST_INSERT_ID() INTO @reservation_id;
