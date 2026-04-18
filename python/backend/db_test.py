from pymongo import MongoClient

uri = "mongodb+srv://expense:expense123@cluster1.gdy11ld.mongodb.net/?appName=Cluster1"
client = MongoClient(uri)

print("Connected. Databases:")
print(client.list_database_names())

