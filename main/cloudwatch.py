import logging
import boto3
import time
from botocore.exceptions import ClientError

cloudwatch_logs = boto3.client('logs', region_name='us-east-1') 
log_group_name = 'group-houskeeping-managment-app'  
log_stream_name = 'stream-houskeeping-managment-app'  

class CloudWatchLogHandler(logging.Handler):
    def __init__(self, log_group, log_stream):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.sequence_token = None
        self._create_log_group_if_not_exists()

        try:
            
            response = cloudwatch_logs.describe_log_streams(
                logGroupName=self.log_group,
                logStreamNamePrefix=self.log_stream
            )
            if len(response['logStreams']) == 0:
                cloudwatch_logs.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
            else:
                self.sequence_token = response['logStreams'][0].get('uploadSequenceToken', None)
        except ClientError as e:
            print(f"Error creating or retrieving log stream: {e}")

    def _create_log_group_if_not_exists(self):
        """Creates the log group if it doesn't exist."""
        try:
            response = cloudwatch_logs.describe_log_groups(logGroupNamePrefix=self.log_group)
            log_groups = response.get('logGroups', [])
            if not any(group['logGroupName'] == self.log_group for group in log_groups):
                cloudwatch_logs.create_log_group(logGroupName=self.log_group)
                print(f"Log group {self.log_group} created.")
        except ClientError as e:
            print(f"Error creating log group: {e}")

    def emit(self, record):
        log_message = self.format(record)
     
        
        try:
        
            if self.sequence_token:
                response = cloudwatch_logs.put_log_events(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream,
                    logEvents=[{
                        'message': log_message
                    }],
                    sequenceToken=self.sequence_token
                )
                self.sequence_token = response['nextSequenceToken']
            else:
                response = cloudwatch_logs.put_log_events(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream,
                    logEvents=[{
                        'message': log_message
                    }]
                )
        except ClientError as e:
            print(f"Error sending log to CloudWatch: {e}")

def configure_cloudwatch_logging():
   
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  
    
    cloudwatch_handler = CloudWatchLogHandler(log_group_name, log_stream_name)
    cloudwatch_handler.setLevel(logging.INFO)

    logger.addHandler(cloudwatch_handler)
