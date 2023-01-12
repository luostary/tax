"""
This module contains a Caribou migration.

Migration Name: alter_client_tg_name_column
Migration Version: 20230112235043
"""

def upgrade(connection):
    sql = 'ALTER TABLE client ADD tg_first_name TEXT after name;';
    connection.execute(sql)

    sql = 'ALTER TABLE driver ADD tg_first_name TEXT after name;';
    connection.execute(sql)
    connection.commit()
    pass

def downgrade(connection):
    # add your downgrade step here
    pass
