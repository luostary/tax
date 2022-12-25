"""
This module contains a Caribou migration.

Migration Name: alter_route_column
Migration Version: 20221225220952
"""

def upgrade(conn):
    sql = """
        CREATE TEMPORARY TABLE temp AS
        SELECT
          id,
          client_id,
          status,
          departure_latitude,
          departure_longitude,
          destination_latitude,
          destination_longitude,
          dt_order,
          amount_client,
          route_length,
          route_time,
          driver_id
        FROM "order";
        """
    conn.execute(sql)

    sql = """
        DROP TABLE "order";"""
    conn.execute(sql)

    sql = """
        CREATE TABLE "order" (
        	id INTEGER PRIMARY KEY AUTOINCREMENT,
        	client_id INTEGER,
        	status TEXT,
        	departure_latitude NUMERIC,
        	departure_longitude NUMERIC,
        	destination_latitude NUMERIC,
        	destination_longitude NUMERIC,
        	dt_order TEXT,
        	amount_client INTEGER DEFAULT (0),
        	route_length INTEGER DEFAULT (0),
        	route_time INTEGER DEFAULT (0),
        	driver_id INTEGER
        );"""
    conn.execute(sql)

    sql = """
        INSERT INTO "order"
         (id,
          client_id,
          status,
          departure_latitude,
          departure_longitude,
          destination_latitude,
          destination_longitude,
          dt_order,
          amount_client,
          route_length,
          route_time,
          driver_id)
        SELECT
          id,
          client_id,
          status,
          departure_latitude,
          departure_longitude,
          destination_latitude,
          destination_longitude,
          dt_order,
          amount_client,
          route_length,
          route_time,
          driver_id
        FROM temp;"""
    conn.execute(sql)

    sql = """
        DROP TABLE temp;
        """
    conn.execute(sql)

    conn.commit()
    pass

def downgrade(connection):
    # add your downgrade step here
    pass
