"""
This module contains a Caribou migration.

Migration Name: example
Migration Version: 20221224112852

install lib
pip install caribou

Create migration -d m - is a dir with files
$ caribou create -d m migration_name

update migration
caribou upgrade taxi.db m

def upgrade(connection):
    # rows query
    sql = """
        CREATE TABLE client (
    	   id INTEGER PRIMARY KEY AUTOINCREMENT,
    	   name TEXT,
    	   tg_username TEXT,
    	   tg_user_id INTEGER,
    	   phone INTEGER
        );
        """
    # connection.execute(sql)

    # inline query
    sql = 'ALTER TABLE client ADD test_column NUMERIC';
    # connection.execute(sql)
    pass

def downgrade(connection):
    # add your downgrade step here
    pass
