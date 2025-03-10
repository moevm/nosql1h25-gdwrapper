from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv


load_dotenv('../.env')


db_uri = f'mongodb://{os.environ['MONGO_INITDB_ROOT_USERNAME']}:{os.environ['MONGO_INITDB_ROOT_PASSWORD']}@{os.environ['MONGO_DB_HOST']}:{os.environ['MONGO_DB_PORT']}/'
client = MongoClient(db_uri)

print('Cписок доступных БД по умолчанию:')
print(client.list_database_names())
print('')


gdwrapper_db = client['gdwrapper_db']
collection = gdwrapper_db['test_collection']
collection.insert_one(
    {
        'Info': 'This is test data',
        'Timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
    }
)

print('Cписок доступных БД после добавления gdwrapper_db:')
print(client.list_database_names())
print('')


print('Данные gdwrapper_db из коллекции test_collection:')
for item in client.get_database('gdwrapper_db').get_collection('test_collection').find():    
    print(item)
