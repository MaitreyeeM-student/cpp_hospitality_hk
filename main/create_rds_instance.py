import boto3
from botocore.exceptions import ClientError

def create_rds_instance():
    rds_client = boto3.client('rds', region_name='us-east-1') 
    
    try:
        response = rds_client.create_db_instance(
            DBName='HotelMgmtDB',
            DBInstanceIdentifier='my-rds-instance',
            MasterUsername='sa',
            MasterUserPassword='Proj12345',
            DBInstanceClass='db.t3.micro',           
            Engine='postgres',                      
            AllocatedStorage=20,                    
            StorageType='gp2',                       
            BackupRetentionPeriod=4,
            MonitoringInterval=0                     
        )
        print("Creating RDS instance...")
    except ClientError as e:
        print(f"Failed to create or access RDS instance: {e}")
        return

    # Wait until the instance is available
    try:
        rds_waiter = rds_client.get_waiter('db_instance_available')
        rds_waiter.wait(DBInstanceIdentifier='my-rds-instance')
        print("RDS instance is now available!")
    except ClientError as e:
        print(f"Error while waiting for RDS instance to be available: {e}")

create_rds_instance()
