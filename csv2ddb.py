import click
import boto3
import csv

@click.group()
def cli():
    pass

@cli.command()
@click.option("--table-name", required=True, type=click.STRING) # type=click.File("rb"), nargs=-1
@click.option("--primary-key", required=True, type=click.STRING)
@click.option("--sort-key", required=True, type=click.STRING)
@click.option("--sort-key-type", required=True, type=click.STRING)
def table(table_name, primary_key, sort_key, sort_key_type): 

    dynamodb_client = boto3.client('dynamodb')
    existing_tables = dynamodb_client.list_tables()['TableNames']

    if table_name not in existing_tables:
        # print("Creating Table: " + table_name + " ...")
        # print("Primary key: " + primary_key)
        # print("Sort key: " + sort_key)

        response = dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': primary_key,
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': sort_key,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': primary_key,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': sort_key,
                    'AttributeType': sort_key_type
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("Created table: " + table_name)
    else:
        print("Table " + table_name + " already exists.")


@cli.command()
@click.argument("filename", nargs=1)
@click.option("--table-name", required=True, type=click.STRING)
def load(filename, table_name):
    click.echo(filename)

    def csv_to_dict(filename):
        items = []
        with open(filename) as csvfile:
            print("Opening " + filename + "...")
            reader = csv.DictReader(csvfile)
            index = reader.fieldnames
            print("Columns: ", index)
            for row in reader:
                data = {}
                
                # Change User to integer type
                for col in index:
                    data[col] = row[col]
                    if col == 'User':
                        data[col] = int(data[col])
            
                items.append(data)

        # Replace empty string values with None type
        for row in items:
            for key, value in row.items():
                if value == '':
                    row[key] = None

        return items

    def dict_to_dynamodb(items, table_name):
        
        session = boto3.Session()
        print("Created session...")

        dynamodb = session.resource('dynamodb')
        db = dynamodb.Table(table_name)
        print("Loading " + table_name + "...")
        print(db.key_schema)

        with db.batch_writer() as batch:
            for item in items:
                #print(item)
                batch.put_item(Item=item)

        return print(table_name + " has been loaded.")

    items = csv_to_dict(filename)
    dict_to_dynamodb(items, table_name)