import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AWSAutoScalingConfig:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.autoscaling = boto3.client('autoscaling', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)

    def create_launch_template(self, template_name, instance_type='t2.micro'):
        try:
            user_data = '''#!/bin/bash
            cd /home/ubuntu/travelaiplanner
            git pull origin main
            sudo docker-compose down
            sudo docker-compose up -d
            '''
            
            response = self.ec2.create_launch_template(
                LaunchTemplateName=template_name,
                VersionDescription='Initial version',
                LaunchTemplateData={
                    'InstanceType': instance_type,
                    'ImageId': 'ami-0c7217cdde317cfec',  # Amazon Linux 2 AMI
                    'UserData': user_data,
                    'SecurityGroupIds': [os.getenv('AWS_SECURITY_GROUP_ID')],
                    'IamInstanceProfile': {
                        'Name': os.getenv('AWS_IAM_INSTANCE_PROFILE')
                    },
                    'BlockDeviceMappings': [{
                        'DeviceName': '/dev/xvda',
                        'Ebs': {
                            'VolumeSize': 20,
                            'VolumeType': 'gp2'
                        }
                    }],
                    'TagSpecifications': [{
                        'ResourceType': 'instance',
                        'Tags': [{
                            'Key': 'Name',
                            'Value': 'TravelAIPlanner-AutoScaled'
                        }]
                    }]
                }
            )
            return response['LaunchTemplate']['LaunchTemplateId']
        except ClientError as e:
            logger.error(f"Error creating launch template: {str(e)}")
            raise

    def create_auto_scaling_group(self, asg_name, launch_template_id, min_size=1, max_size=3):
        try:
            response = self.autoscaling.create_auto_scaling_group(
                AutoScalingGroupName=asg_name,
                LaunchTemplate={
                    'LaunchTemplateId': launch_template_id,
                    'Version': '$Latest'
                },
                MinSize=min_size,
                MaxSize=max_size,
                DesiredCapacity=min_size,
                AvailabilityZones=[
                    f"{self.region}a",
                    f"{self.region}b"
                ],
                HealthCheckType='ELB',
                HealthCheckGracePeriod=300,
                Tags=[{
                    'Key': 'Name',
                    'Value': 'TravelAIPlanner-ASG',
                    'PropagateAtLaunch': True
                }]
            )
            return response
        except ClientError as e:
            logger.error(f"Error creating auto scaling group: {str(e)}")
            raise

    def create_scaling_policies(self, asg_name):
        try:
            # Scale up policy
            self.autoscaling.put_scaling_policy(
                AutoScalingGroupName=asg_name,
                PolicyName=f"{asg_name}-ScaleUp",
                PolicyType='TargetTrackingScaling',
                TargetTrackingConfiguration={
                    'PredefinedMetricSpecification': {
                        'PredefinedMetricType': 'ASGAverageCPUUtilization'
                    },
                    'TargetValue': 75.0,
                    'ScaleOutCooldown': 300,
                    'ScaleInCooldown': 300
                }
            )

            # Memory-based scaling policy using custom metric
            self.autoscaling.put_scaling_policy(
                AutoScalingGroupName=asg_name,
                PolicyName=f"{asg_name}-MemoryScaling",
                PolicyType='StepScaling',
                StepScalingPolicyConfiguration={
                    'AdjustmentType': 'ChangeInCapacity',
                    'MetricAggregationType': 'Average',
                    'StepAdjustments': [
                        {
                            'MetricIntervalLowerBound': 0,
                            'MetricIntervalUpperBound': 20,
                            'ScalingAdjustment': 1
                        },
                        {
                            'MetricIntervalLowerBound': 20,
                            'ScalingAdjustment': 2
                        }
                    ]
                }
            )
        except ClientError as e:
            logger.error(f"Error creating scaling policies: {str(e)}")
            raise

    def setup_auto_scaling(self):
        try:
            template_name = f"TravelAIPlanner-Template-{datetime.now().strftime('%Y%m%d')}"
            asg_name = f"TravelAIPlanner-ASG-{datetime.now().strftime('%Y%m%d')}"
            
            # Create launch template
            template_id = self.create_launch_template(template_name)
            
            # Create auto scaling group
            self.create_auto_scaling_group(asg_name, template_id)
            
            # Create scaling policies
            self.create_scaling_policies(asg_name)
            
            logger.info(f"Auto scaling setup completed for {asg_name}")
            return True
        except Exception as e:
            logger.error(f"Error setting up auto scaling: {str(e)}")
            return False
