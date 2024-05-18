import json
import logging
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
import settings
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)


WS_ENDPOINT = settings.WS_ENDPOINT
table = boto3.resource('dynamodb').Table(settings.DYNAMODB_TABLE_NAME)
api_gateway_management_api = boto3.client('apigatewaymanagementapi', endpoint_url=WS_ENDPOINT)


def lambda_handler(event, context):
    # Log the received event
    print("Received event: " + json.dumps(event))

    # Handle the connection and message routes
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')

    if route_key is None or connection_id is None:
        return {
            "statusCode": 400,
            "body": f"routeKey={route_key}, connectionId={connection_id}"
        }

    if route_key == '$connect':
        return handle_connect(event, connection_id)
    elif route_key == '$disconnect':
        return handle_disconnect(connection_id)
    elif route_key == '$default':
        return handle_message(event)
    else:
        return {
            'statusCode': 400,
            'body': 'Unknown route'
        }

def handle_connect(event, connection_id):
    user_id = event.get('queryStringParameters', {}).get('userId')
    
    table.put_item(Item={'userId': user_id, 'connectionId': connection_id})
    
    print(f"Connect: {connection_id}")
    
    return {
        'statusCode': 200,
        'body': 'Connected'
    }

def handle_disconnect(connection_id):
    response = table.scan(FilterExpression=Attr('connectionId').eq(connection_id))
    items = response.get('Items', [])
    
    if items:
        user_id = items[0]['userId']
        table.delete_item(Key={'userId': user_id, 'connectionId': connection_id})
        
    print(f"Disconnect: {connection_id}")
    return {
        'statusCode': 200,
        'body': 'Disconnected'
    }

def handle_message(event):
    body = json.loads(event.get('body', ''))
    recipient_id = body.get('recipient_id')
    message = body.get('message')

    response = table.scan(FilterExpression=Attr('userId').eq(recipient_id))

    for item in response.get('Items', []):
        send_message_to_client(item['connectionId'], message)
        # print(f"Message from {item['connectionId']}: {message}")
    
    return {
        'statusCode': 200,
        'body': 'Message received'
    }
    
def send_message_to_client(recipient_id, message):
    try:
        api_gateway_management_api.post_to_connection(
            ConnectionId=recipient_id,
            Data=json.dumps({"message": message})
        )
    # except api_gateway_management_api.exception.GoneException:
    #     pass
    except ClientError:
        traceback.print_exc()
