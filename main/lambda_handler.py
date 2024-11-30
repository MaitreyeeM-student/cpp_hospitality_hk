import boto3
from PIL import Image
import io
import json
import logging

s3 = boto3.client('s3')

def resize_image(image_data, size=(300, 300)):
    """Resize the image to the specified size."""
    try:
        logging.info("Resizing the image...")
        image = Image.open(io.BytesIO(image_data))
        logging.info(f"Image loaded. Format: {image.format}, Size: {image.size}")
        
        image = image.resize(size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality resizing
        logging.info(f"Image resized to: {size}")

        output = io.BytesIO()
        image.save(output, format='JPEG')  # Save as JPEG; change format as needed
        output.seek(0)  # Move to the beginning of the BytesIO buffer
        logging.info("Image resize completed and saved to memory")
        return output.getvalue()
    except Exception as e:
        logging.error(f"Error resizing image: {e}")
        raise

def lambda_handler(event, context):
    
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    try:
        original_image = s3.get_object(Bucket=bucket_name, Key=key)
        image_data = original_image['Body'].read()
        logging.info(f"Image {key} fetched from S3.")

        resized_image = resize_image(image_data)

        processed_key = f"processed/{key}"

        s3.put_object(Bucket=bucket_name, Key=processed_key, Body=resized_image, ContentType='image/jpeg')
        logging.info(f"Resized image uploaded to {processed_key}.")

     
        s3.put_object_tagging(
            Bucket=bucket_name,
            Key=processed_key,
            Tagging={'TagSet': [{'Key': 'processed', 'Value': 'true'}]}
        )


        return {
            'statusCode': 200,
            'body': json.dumps({'processed_key': processed_key})
        }

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
