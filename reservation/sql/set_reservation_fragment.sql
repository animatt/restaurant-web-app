SET @customer_app_id = %s, @customer_name = %s, @num_menus = %s, @res_datetime = %s;
INSERT IGNORE INTO timeline_customer (vip, name, phone, app_id) VALUES (0, @customer_name, '', @customer_app_id);
SELECT id FROM timeline_customer WHERE app_id = @customer_app_id INTO @customer_id;
INSERT INTO timeline_reservation (num_menus, res_datetime, res_duration, customer_id) VALUES (@num_menus, @res_datetime, 60, @customer_id);
SELECT LAST_INSERT_ID() INTO @reservation_id;
