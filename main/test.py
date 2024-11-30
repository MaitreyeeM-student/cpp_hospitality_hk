'''import boto3
import os
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AWS configurations
region_name = os.getenv('AWS_REGION', 'us-east-1')
sns_client = boto3.client('sns', region_name=region_name)
sqs_client = boto3.client('sqs', region_name=region_name)

# Constants for SNS topic and SQS queue names
ASSIGN_TASK_SNS_TOPIC = os.getenv('ASSIGN_TASK_SNS_TOPIC', 'assign_task_notifications')
ASSIGN_TASK_SQS_QUEUE = os.getenv('ASSIGN_TASK_SQS_QUEUE', 'assign_task_queue')

def setup_notification_services():
    """
    Set up SNS and SQS resources, including creating the SNS topic and SQS queue,
    setting policies, and subscribing the SQS queue to the SNS topic.
    """
    # Create SNS topic
    sns_topic_arn = create_sns_topic(ASSIGN_TASK_SNS_TOPIC)
    if not sns_topic_arn:
        logging.error("Failed to create SNS topic.")
        return

    # Create SQS queue
    queue_url = create_sqs_queue(ASSIGN_TASK_SQS_QUEUE)
    if not queue_url:
        logging.error("Failed to create SQS queue.")
        return

    # Set the policy on SQS to allow SNS to send messages
    set_sqs_policy_for_sns(queue_url, sns_topic_arn)

    # Subscribe the SQS queue to SNS topic
    subscribe_sqs_to_sns(sns_topic_arn, queue_url)

def create_sns_topic(topic_name):
    """
    Create an SNS topic if it doesn't exist, or fetch the ARN of the existing topic.
    """
    try:
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response.get('TopicArn')
        logging.info(f"SNS topic '{topic_name}' created with ARN: {topic_arn}")
        return topic_arn
    except Exception as e:
        logging.error(f"Error creating SNS topic '{topic_name}': {str(e)}")
        return None

def create_sqs_queue(queue_name):
    """
    Create an SQS queue if it doesn't exist and return its URL.
    """
    queue_url = get_sqs_queue_url(queue_name)
    if not queue_url:
        try:
            response = sqs_client.create_queue(QueueName=queue_name)
            queue_url = response['QueueUrl']
            logging.info(f"SQS queue '{queue_name}' created with URL: {queue_url}")
        except Exception as e:
            logging.error(f"Error creating SQS queue '{queue_name}': {str(e)}")
            return None
    else:
        logging.info(f"SQS queue '{queue_name}' already exists with URL: {queue_url}")
    return queue_url

def get_sqs_queue_url(queue_name):
    """
    Fetch the URL of an existing SQS queue by its name.
    """
    try:
        response = sqs_client.list_queues()
        for queue_url in response.get('QueueUrls', []):
            if queue_name in queue_url:
                return queue_url
    except Exception as e:
        logging.error(f"Error listing SQS queues: {str(e)}")
    return None

def set_sqs_policy_for_sns(queue_url, sns_topic_arn):
    """
    Set the correct policy on the SQS queue to allow the SNS topic to send messages.
    """
    try:
        sqs_queue_arn = sqs_client.get_queue_attributes(
            QueueUrl=queue_url, AttributeNames=['QueueArn']
        )['Attributes']['QueueArn']

        policy = json.dumps({
            "Version": "2008-10-17",
            "Statement": {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "SQS:SendMessage",
                "Resource": sqs_queue_arn,
                "Condition": {"ArnEquals": {"aws:SourceArn": sns_topic_arn}}
            }
        })

        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes={'Policy': policy})
        logging.info("SQS policy set successfully.")
    except Exception as e:
        logging.error(f"Error setting SQS policy: {str(e)}")

def subscribe_sqs_to_sns(sns_topic_arn, sqs_queue_url):
    """
    Subscribe the SQS queue to the SNS topic.
    """
    try:
        sqs_queue_arn = sqs_client.get_queue_attributes(
            QueueUrl=sqs_queue_url, AttributeNames=['QueueArn']
        )['Attributes']['QueueArn']

        response = sns_client.list_subscriptions_by_topic(TopicArn=sns_topic_arn)
        existing_subscriptions = [sub['Endpoint'] for sub in response['Subscriptions']]
        
        if sqs_queue_arn not in existing_subscriptions:
            sns_client.subscribe(
                TopicArn=sns_topic_arn, Protocol='sqs', Endpoint=sqs_queue_arn
            )
            logging.info(f"SQS queue '{sqs_queue_arn}' subscribed to SNS topic '{sns_topic_arn}'.")
        else:
            logging.info(f"SQS queue '{sqs_queue_arn}' is already subscribed to SNS topic '{sns_topic_arn}'.")
    except Exception as e:
        logging.error(f"Error subscribing SQS to SNS: {str(e)}")

def subscribe_to_sns(topic_arn, email):
    """
    Subscribe an email address to an SNS topic.
    """
    try:
        sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        logging.info(f"Subscribed {email} to SNS topic: {topic_arn}")
    except Exception as e:
        logging.error(f"Error subscribing {email} to SNS topic {topic_arn}: {str(e)}")

# Main execution block for testing
if __name__ == '__main__':
    logging.info("Starting SNS-SQS setup.")
    
    # Step 1: Set up SNS topic and SQS queue
    setup_notification_services()

    # Optional: Publish a test message to SNS to verify integration
    sns_topic_arn = create_sns_topic(ASSIGN_TASK_SNS_TOPIC)
    if sns_topic_arn:
        try:
            sns_client.publish(
                TopicArn=sns_topic_arn,
                Message="Test SNS to SQS integration message."
            )
            logging.info("Test message published to SNS topic.")
        except Exception as e:
            logging.error(f"Error publishing test message: {str(e)}")'''
