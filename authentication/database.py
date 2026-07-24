import boto3
import os
from dotenv import load_dotenv
import uuid


load_dotenv()


# DynamoDB connection

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
)


users_table = dynamodb.Table("users")


# No need to create database in DynamoDB
def create_database():
    pass



# Add user to DynamoDB

def add_user(name, email, password):

    user_id = str(uuid.uuid4())

    users_table.put_item(
        Item={
            "user_id": user_id,
            "name": name,
            "email": email,
            "password": password.decode("utf-8")
        }
    )



# Get user from DynamoDB

def get_user(email):

    response = users_table.scan(
        FilterExpression="email = :email",
        ExpressionAttributeValues={
            ":email": email
        }
    )


    items = response.get("Items", [])


    if items:
        return items[0]

    return None