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


def handler(event, context):
    query_string_params = event.get(
        'queryStringParameters', default_query_params())

    debug = bool(strtobool(os.environ.get('DEBUG', False)))
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

    logger.info("Validating: {0} {1} {2} {3}".format(
        cluster, service, qry_tag, evt_tag))

    if cluster != cluster_env:
        raise InvalidClusterError(
            "Cluster redeployments not supported: {0}".format(cluster))

    if token != token_ssm:
        if debug:
            logger.info("Skipping token check as running in debug mode!")
        else:
            raise InvalidTokenError('Token does not match')

    if qry_tag and (qry_tag != evt_tag):
        raise InvalidTagError(
            "Tags do not match: {0} {1}".format(qry_tag, evt_tag))

    if not cluster in get_clusters():
        raise InvalidClusterError("Cluster was not found: {0}".format(cluster))

    if not service in get_services(cluster):
        raise InvalidServiceError("Service was not found: {0}".format(service))

    if debug:
        return response_json('Debug only, thx!')

    try:
        update_service(cluster, service)
        if notification_key and webhook:
            send_notification_message(webhook, {
                "text": "Redeploying: {0} -- {1} -- {2}".format(cluster, service, datetime.now(tz))
            })

        return response_json('Ok!')
    except botocore.exceptions.ClientError as error:
        logger.error(error.response)
        raise RedeploymentError(
            "Failed to redeploy ECS service: {0} -- {1}".format(cluster, service))


def default_query_params():
    return {
        'cluster': '',
        'service': '',
        'token': '',
        'tag': None,
    }


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


def response_json(message):
    return {
        'statusCode': 200,
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


class InvalidClusterError(Exception):
    pass


class InvalidServiceError(Exception):
    pass


class InvalidTagError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class RedeploymentError(Exception):
    pass
