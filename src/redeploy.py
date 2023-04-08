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
    logger.info(event)
    query_string_params = event.get(
        'queryStringParameters', default_query_params())

    debug = bool(strtobool(os.environ.get('DEBUG', False)))
    cluster = query_string_params.get('cluster')
    service = query_string_params.get('service')
    token = query_string_params.get('token')
    qry_tag = query_string_params.get('tag', None)

    if qry_tag:
        evt_tag = json.loads(event.get('body')).get('push_data').get('tag')
    else:
        evt_tag = None

    cluster_env = os.environ.get('CLUSTER')
    token_key = os.environ.get('TOKEN_KEY')
    token_ssm = ssm_client.get_parameter(
        Name=token_key,
        WithDecryption=True
    )

    slack_key = os.environ.get('SLACK_KEY', None)
    if slack_key:
        webhook = ssm_client.get_parameter(
            Name=slack_key,
            WithDecryption=True
        )['Parameter']['Value']
    tz = timezone(os.environ.get('TIMEZONE', 'UTC'))

    logger.info("Validating: {0} {1} {2} {3}".format(
        cluster, service, qry_tag, evt_tag))

    if cluster != cluster_env:
        raise InvalidClusterError(
            "Cluster redeployments not supported: {0}".format(cluster))

    if token != token_ssm['Parameter']['Value']:
        if debug:
            logger.info("Skipping token check as running in debug mode!")
        else:
            raise InvalidTokenError('Token does not match')

    if (qry_tag and evt_tag) and (qry_tag != evt_tag):
        raise InvalidTagError(
            "Tags do not match: {0} {1}".format(qry_tag, evt_tag))

    response = ecs_client.list_clusters()
    clusters = parse_arns_to_names(response.get('clusterArns', []))

    if not cluster in clusters:
        raise InvalidClusterError("Cluster was not found: {0}".format(cluster))

    response = ecs_client.list_services(
        cluster=cluster,
        maxResults=100
    )
    services = parse_arns_to_names(response.get('serviceArns', []))

    if not service in services:
        raise InvalidServiceError("Service was not found: {0}".format(service))

    if debug:
        return response_json('Debug only, thx!')

    try:
        ecs_client.update_service(
            cluster=cluster,
            service=service,
            forceNewDeployment=True
        )
        if webhook:
            send_slack_message(webhook, {
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


def parse_arns_to_names(arns):
    return map(lambda x: x.rsplit('/')[-1], arns)


def response_json(message):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': message})
    }


def send_slack_message(webhook, payload):
    return requests.post(webhook, json.dumps(payload))


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
