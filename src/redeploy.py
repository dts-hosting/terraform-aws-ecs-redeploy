import botocore
import boto3
import json
import logging
import os
import requests

from datetime import datetime
from distutils.util import strtobool
from pytz import timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ecs_client = boto3.client('ecs')
ssm_client = boto3.client('ssm')


def handler(event, _context):
    debug = bool(strtobool(os.environ.get('DEBUG', 'false')))
    query_string_params = event.get('queryStringParameters')
    cluster = query_string_params.get('cluster')
    service = query_string_params.get('service')
    token = query_string_params.get('token')
    qry_tag = query_string_params.get('tag', None)

    cluster_env = os.environ.get('CLUSTER')
    notification_key = os.environ.get('NOTIFICATION_KEY', None)
    token_ssm = get_parameter(os.environ.get('TOKEN_KEY'))
    tz = timezone(os.environ.get('TIMEZONE', 'UTC'))

    if debug:
        logger.info(event)

    if qry_tag:
        evt_tag = parse_event_for_tag(event)
    else:
        evt_tag = None

    if notification_key:
        webhook = get_parameter(notification_key)

    logger.info(f"Validating: {cluster} {service} {qry_tag} {evt_tag}")

    if cluster != cluster_env:
        return response_json(f"Service redeployment not supported for cluster: {cluster}", 500)

    if token != token_ssm:
        if debug:
            logger.info("Skipping token check as running in debug mode!")
        else:
            return response_json('Token does not match', 500)

    if qry_tag and (qry_tag != evt_tag):
        return response_json(f"Tags do not match: {qry_tag} {evt_tag}", 500)

    if not cluster in get_clusters():
        return response_json(f"Cluster was not found: {cluster}", 500)

    if not service in get_services(cluster):
        return response_json(f"Service was not found: {service}", 500)

    if debug:
        return response_json('Debug only, thx!')

    try:
        update_service(cluster, service)
        if notification_key and webhook:
            notification_time = datetime.now(tz)
            send_notification_message(webhook, {
                "text": f"Redeploying: {cluster} -- {service} -- {notification_time}"
            })

        return response_json('Ok!')
    except botocore.exceptions.ClientError as _error:
        return response_json(f"Failed to redeploy ECS service: {cluster} {service}", 500)


def get_clusters():
    response = ecs_client.list_clusters()
    return parse_arns_to_names(response.get('clusterArns', []))


def get_parameter(key):
    response = ssm_client.get_parameter(Name=key, WithDecryption=True)
    return response['Parameter']['Value']


def get_services(cluster):
    response = ecs_client.list_services(
        cluster=cluster,
        maxResults=100
    )
    return parse_arns_to_names(response.get('serviceArns', []))


def parse_arns_to_names(arns):
    return map(lambda x: x.rsplit('/')[-1], arns)


def parse_event_for_tag(event):
    tag = json.loads(event.get('body', '{}')).get(
        'push_data', {}).get('tag', None)
    return tag if tag else None


def response_json(message, status=200):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': message})
    }


def send_notification_message(webhook, payload):
    return requests.post(webhook, json.dumps(payload))


def update_service(cluster, service):
    return ecs_client.update_service(
        cluster=cluster,
        service=service,
        forceNewDeployment=True
    )
