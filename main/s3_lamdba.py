import boto3
from botocore.exceptions import ClientError
import os
import logging
import json
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = "us-east-1"
AWS_BUCKET_NAME = "staff-task-documents"
LAMBDA_FUNCTION_NAME = 'image-resize-function'

AWS_IAM_ROLE_ARN = os.getenv('AWS_IAM_ROLE_ARN')

logging.basicConfig(level=logging.INFO)
logging.info(f"AWS_REGION is set to: {AWS_REGION}")

if not AWS_REGION:
    raise ValueError("AWS_REGION is not set correctly. Please specify a valid region.")

# Create AWS service clients with the region set explicitly
s3_client = boto3.client("s3", region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)


def create_bucket(bucket_name=AWS_BUCKET_NAME):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            try:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
                )
                print(f"Bucket '{bucket_name}' created successfully.")
            except ClientError as ce:
                print(f"Error creating bucket: {ce}")
                raise
        else:
            print(f"Error checking bucket: {e}")
            raise


def upload_file_to_s3(file, key, bucket_name=AWS_BUCKET_NAME):
    try:
        s3_client.upload_fileobj(file, bucket_name, key)
        print(f"File uploaded successfully to {key}.")
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        raise


def trigger_lambda_image_processing(original_key):
    payload = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": AWS_BUCKET_NAME
                    },
                    "object": {
                        "key": original_key
                    }
                }
            }
        ]
    }
    try:
        logging.info(f"Triggering Lambda for image processing with original key: {original_key}")
        
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps(payload) 
        )
        
        status_code = response['StatusCode']
        if status_code == 200:
            logging.info("Lambda invoked successfully.")
        else:
            logging.warning(f"Lambda invocation failed with status code: {status_code}")
        
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        
        logging.info(f"Lambda response: {response_payload}")

        body = response_payload.get('body', '{}')
        body_data = json.loads(body)

        processed_key = body_data.get('processed_key', '')
        if processed_key:
            logging.info(f"Image processing successful. Processed key: {processed_key}")
        else:
            logging.warning("Lambda response did not include a processed key.")
        
        return processed_key

    except ClientError as e:
        logging.error(f"ClientError occurred while invoking Lambda: {e}")
    except Exception as e:
        logging.error(f"An error occurred while triggering Lambda: {e}")
    return None


def generate_presigned_url(key, expiration=604800):
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_BUCKET_NAME, 'Key': key},
            ExpiresIn=expiration
        )
        return response
    except Exception as e:
        logging.error(f"Error generating presigned URL: {e}")
        return None


def create_lambda_function():
    try:
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime='python3.9',
            Role=AWS_IAM_ROLE_ARN,
            Handler='lambda_handler.handler',
            Code={'ZipFile': open("lambda_function.zip", "rb").read()},
            Timeout=15
        )
        lambda_arn = response['FunctionArn']
        logging.info(f"Lambda function '{LAMBDA_FUNCTION_NAME}' created with ARN: {lambda_arn}")
        return lambda_arn
    except lambda_client.exceptions.ResourceConflictException:
        lambda_arn = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)['Configuration']['FunctionArn']
        logging.info(f"Lambda function '{LAMBDA_FUNCTION_NAME}' already exists with ARN: {lambda_arn}")
        return lambda_arn
    except Exception as e:
        logging.error(f"Error creating or fetching Lambda function: {str(e)}")
        return None


def set_s3_trigger(lambda_arn):
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_FUNCTION_NAME,
            StatementId="S3Invoke",
            Action="lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn=f"arn:aws:s3:::{AWS_BUCKET_NAME}",
        )

        s3_client.put_bucket_notification_configuration(
            Bucket=AWS_BUCKET_NAME,
            NotificationConfiguration={
                "LambdaFunctionConfigurations": [
                    {
                        "LambdaFunctionArn": lambda_arn,
                        "Events": ["s3:ObjectCreated:*"],
                    }
                ]
            },
        )
        logging.info(f"Lambda trigger successfully set for bucket '{AWS_BUCKET_NAME}'.")
    except ClientError as e:
        logging.error(f"Error setting Lambda trigger: {e}")
        raise e


if __name__ == "__main__":
    create_bucket(AWS_BUCKET_NAME)
    lambda_arn = create_lambda_function()

    if lambda_arn:
        set_s3_trigger(lambda_arn)
    else:
        logging.error("Failed to create or fetch Lambda function ARN. Exiting...")
