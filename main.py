from minio import Minio 
import json 

client = Minio(
    endpoint='localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin123',
    secure=False
)

response = client.get_object(
    bucket_name='int3405',
    object_name='tuan-1/objectives.json',
)

data = response.read().decode("utf-8")

data = json.loads(data)

print('\n'.join(data))
