import boto3
import os
import logging
from .models import Employee
from dotenv import load_dotenv
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)

sns_client = boto3.client('sns', region_name='us-east-1')
sqs_client = boto3.client('sqs', region_name='us-east-1')

ASSIGN_TASK_SNS_TOPIC = 'assign_task_notifications'
ASSIGN_TASK_SQS_QUEUE = 'assign_task_queue'


AWS_IAM_ROLE_ARN = os.getenv('AWS_IAM_ROLE_ARN')


def setup_notification_services():
    # Create SNS topic
    sns_topic_arn = create_sns_topic('assign_task_notifications')
    if not sns_topic_arn:
        logging.error("Failed to create SNS topic.")
        return

    # Create SQS queue
    queue_url = create_sqs_queue('assign_task_queue')
    if not queue_url:
        logging.error("Failed to create SQS queue.")
        return

    set_sqs_policy_for_sns(queue_url, sns_topic_arn)

    subscribe_sqs_to_sns(sns_topic_arn, queue_url)

    subscribe_new_employees_to_topic()


def get_employee_email(assigned_to):
    logging.info(f"Fetching email for employee ID: {assigned_to}")
    employee = Employee.query.filter_by(id=assigned_to).first()
    if employee and employee.email:
        logging.info(f"Found email for employee {assigned_to}: {employee.email}")
        return employee.email
    logging.error(f"Employee with ID {assigned_to} not found or has no email.")
    return None


def create_sns_topic(topic_name):
    try:
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response.get('TopicArn')
        logging.info(f"SNS topic '{topic_name}' created with ARN: {topic_arn}")
        return topic_arn
    except sns_client.exceptions.ClientError as e:
        if 'TopicAlreadyExists' in str(e):
            # If the topic already exists, get the existing ARN
            response = sns_client.list_topics()
            for topic in response['Topics']:
                if topic_name in topic['TopicArn']:
                    logging.info(f"SNS topic '{topic_name}' already exists with ARN: {topic['TopicArn']}")
                    return topic['TopicArn']
        logging.error(f"Error creating or fetching SNS topic '{topic_name}': {str(e)}")
        return None


def get_sqs_queue_url(queue_name):
    try:
        response = sqs_client.list_queues()
        logging.info(f"List of queues: {response.get('QueueUrls', [])}")
        if 'QueueUrls' in response:
            for queue_url in response['QueueUrls']:
                if queue_name in queue_url:
                    logging.info(f"SQS queue '{queue_name}' already exists with URL: {queue_url}")
                    return queue_url
        logging.warning(f"SQS queue '{queue_name}' not found.")
        return None
    except sqs_client.exceptions.ClientError as e:
        logging.error(f"Error fetching SQS queues: {str(e)}")
        return None


def create_sqs_queue(queue_name):
    queue_url = get_sqs_queue_url(queue_name)
    if not queue_url:
        try:
            response = sqs_client.create_queue(QueueName=queue_name)
            queue_url = response['QueueUrl']
            logging.info(f"SQS queue '{queue_name}' created with URL: {queue_url}")
        except sqs_client.exceptions.ClientError as e:
            logging.error(f"Error creating SQS queue '{queue_name}': {str(e)}")
            return None
    else:
        logging.info(f"SQS queue '{queue_name}' already exists with URL: {queue_url}")
    return queue_url
    
def set_sqs_policy_for_sns(queue_url, sns_topic_arn):
    try:
        # Fetch the ARN of the SQS queue using its URL
        sqs_queue_arn = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )['Attributes']['QueueArn']

        # Define the policy
        policy = f"""
        {{
            "Version": "2008-10-17",
            "Statement": {{
                "Effect": "Allow",
                "Principal": {{
                    "AWS": "*"
                }},
                "Action": "SQS:SendMessage",
                "Resource": "{sqs_queue_arn}",
                "Condition": {{
                    "ArnEquals": {{
                        "aws:SourceArn": "{sns_topic_arn}"
                    }}
                }}
            }}
        }}
        """

        # Set the policy on the SQS queue
        queue_attributes = {'Policy': policy}
        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes=queue_attributes)
        logging.info(f"SQS queue policy updated to allow SNS topic {sns_topic_arn} to send messages.")

    except sqs_client.exceptions.ClientError as e:
        logging.error(f"Error setting SQS policy: {str(e)}")



def subscribe_sqs_to_sns(sns_topic_arn, sqs_queue_url):
    try:
        sqs_queue_arn = sqs_client.get_queue_attributes(
            QueueUrl=sqs_queue_url,
            AttributeNames=['QueueArn']
        )['Attributes']['QueueArn']


        response = sns_client.list_subscriptions_by_topic(TopicArn=sns_topic_arn)
        existing_subscriptions = [sub['Endpoint'] for sub in response['Subscriptions']]
        
        if sqs_queue_arn not in existing_subscriptions:
            sns_client.subscribe(
                TopicArn=sns_topic_arn,
                Protocol='sqs',
                Endpoint=sqs_queue_arn
            )
            logging.info(f"Subscribed SQS queue '{sqs_queue_arn}' to SNS topic '{sns_topic_arn}'")
        else:
            logging.info(f"SQS queue '{sqs_queue_arn}' is already subscribed to SNS topic '{sns_topic_arn}'")
    except sns_client.exceptions.ClientError as e:
        logging.error(f"Error subscribing SQS queue to SNS topic: {str(e)}")


def subscribe_to_sns(topic_arn, email):
    try:
        sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        logging.info(f"Subscribed {email} to SNS topic: {topic_arn}")
    except Exception as e:
        logging.error(f"Error subscribing {email} to SNS topic {topic_arn}: {str(e)}")

def get_existing_subscriptions(topic_arn):
    subscriptions = []
    try:
        response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        subscriptions = [sub['Endpoint'] for sub in response['Subscriptions']]
        logging.info(f"Found existing subscriptions: {subscriptions}")
    except Exception as e:
        logging.error(f"Error fetching subscriptions for topic {topic_arn}: {str(e)}")
    return subscriptions


def subscribe_new_employees_to_topic():
    logging.info("Checking and subscribing staff employees to the SNS topic.")
    
    assign_topic_arn = create_sns_topic(ASSIGN_TASK_SNS_TOPIC)
    if not assign_topic_arn:
        logging.error(f"Failed to create or get SNS topic '{ASSIGN_TASK_SNS_TOPIC}' ARN.")
        return

    existing_subscriptions = get_existing_subscriptions(assign_topic_arn)

    # Fetch all employees with role 'staff'
    staff_employees = Employee.query.filter_by(role='Staff').all()
    

    for employee in staff_employees:
        email = employee.email
        if email and email not in existing_subscriptions:
            logging.info(f"Subscribing {email} to the SNS topic.")
            subscribe_to_sns(assign_topic_arn, email)
        else:
            logging.info(f"Employee {email} is already subscribed or does not have an email.")
            
            
topic_arn = sns_client.create_topic(Name=ASSIGN_TASK_SNS_TOPIC)['TopicArn']

def format_details(details_data, employee_name):
    formatted_details = []
    
    formatted_details.append(f"Employee: {employee_name}")
    
    if isinstance(details_data, dict):  
        for key, value in details_data.items():
            if isinstance(value, list):
                formatted_details.append(f"{key}: {', '.join([str(v) for v in value])}")
            elif value:  
                formatted_details.append(f"{key}: {value}")
    else:
        logging.warning(f"Expected details_data to be a dictionary, but got {type(details_data)} instead.")
        formatted_details.append(f"Details: {details_data}")  

    return ", ".join(formatted_details)


def publish_message_to_sns(topic_name, message_data):
    try:
       
        type_message = message_data.get("type", "No Type")
        details_message = message_data.get("details", {})
        employee_name = message_data.get("employee_name", "Unknown Employee")
        
        assigned_to = message_data.get("assigned_to")
        print(f"Assigned to employee: {assigned_to}")  
        
        if not assigned_to:
            print("Error: 'assigned_to' key is missing in the message data.")
            return  
        
        formatted_details = format_details(details_message, employee_name)
        message = f"Type: {type_message}\nDetails: {formatted_details}"
        print(f"Message to be published:\n{message}")
        
        assigned_employee_email = assigned_to
        print(f"sending to email:\n{assigned_employee_email}")
        
        if not assigned_employee_email:
            print("Assigned employee email not found!")
            return
        
        sns_client.publish(
            TopicArn=topic_arn,
            Message=message,
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': assigned_employee_email
                }
            }
        )
        
    
        print(f"Message successfully published to {assigned_employee_email}")

    except json.JSONDecodeError as e:
        print(f"JSON encoding error while publishing to {topic_name}: {str(e)}")
    except Exception as e:
        print(f"Error publishing message to SNS topic {topic_name}: {str(e)}")




if __name__ == '__main__':
    logging.info("Starting application.")
    '''sns_topic_arn = create_sns_topic(ASSIGN_TASK_SNS_TOPIC)
    if not sns_topic_arn:
        logging.error(f"Failed to create or get SNS topic '{ASSIGN_TASK_SNS_TOPIC}' ARN.")
        exit()

    # Step 2: Create the SQS queue
    queue_url = create_sqs_queue(ASSIGN_TASK_SQS_QUEUE)
    if not queue_url:
        logging.error(f"Failed to create SQS queue '{ASSIGN_TASK_SQS_QUEUE}'.")
        exit()

    # Step 3: Set the SQS policy to allow SNS to send messages to it
    set_sqs_policy_for_sns(queue_url, sns_topic_arn)

    # Step 4: Subscribe the SQS queue to the SNS topic
    subscribe_sqs_to_sns(sns_topic_arn, queue_url)'''
