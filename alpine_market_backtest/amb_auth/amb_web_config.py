import os

mysql_config = {
    'pool_name': 'mypool',
    'pool_size': 1,
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'alpinemk2'),
    'password': os.environ.get('DB_PASSWORD', ''),
}