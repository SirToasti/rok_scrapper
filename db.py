from sqlalchemy import create_engine
import models
import boto3
import os

def main():
    engine = create_engine("postgresql+psycopg2://postgres:password@127.0.0.1:5432/rok_screenshot_test")
    models.Base.metadata.create_all(engine)

if __name__ == "__main__":
    main()

def init_db(config):
    username = config['username']
    host = config['host']
    port = config.get('port', 5432)
    database = config['database']
    password = os.getenv('DB_PASSWORD') or get_password(config['password_parameter_name'])
    connection_string = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(username, password, host, port, database)
    engine = create_engine(connection_string)
    models.Base.metadata.create_all(engine)
    return engine

def get_password(parameter_name):
    client = boto3.client('ssm')
    return client.get_parameter(Name=parameter_name, WithDecryption=True)['Parameter']['Value']
