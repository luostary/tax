"""
This module contains a Caribou migration.

Migration Name: add_column 
Migration Version: 20240908183453
"""

def upgrade(connection):
    sql = "ALTER TABLE `driver` ADD COLUMN `user_type` VARCHAR(45) NULL COMMENT 'Тип пользователя' AFTER `referer_payed`;";
    sql = "UPDATE driver set user_type = 'driver' where user_type is null limit 1000;"
    sql = "ALTER TABLE `driver` ADD COLUMN `dt_subscribe_until` DATETIME NULL AFTER `user_type`"
    pass

def downgrade(connection):
    # add your downgrade step here
    pass
