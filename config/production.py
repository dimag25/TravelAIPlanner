import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Production Configuration
CONFIG = {
    'DEBUG': False,
    'TESTING': False,
    'DATABASE_URL': os.environ.get('DATABASE_URL'),
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SECRET_KEY': os.environ.get('FLASK_SECRET_KEY'),
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file upload
    'PROPAGATE_EXCEPTIONS': True,
}

# AWS Configuration
AWS_CONFIG = {
    'region': 'us-east-1',
    'availability_zones': ['us-east-1a', 'us-east-1b'],
    'instance_type': 't2.micro',
    'min_instances': 1,
    'max_instances': 3,
    'scale_up_threshold': 75,  # CPU utilization percentage
    'scale_down_threshold': 25,
    'auto_scaling': {
        'enabled': True,
        'metrics': {
            'cpu_utilization': {
                'target': 75,
                'scale_out_cooldown': 300,
                'scale_in_cooldown': 300
            },
            'memory_utilization': {
                'target': 80,
                'scale_out_cooldown': 300,
                'scale_in_cooldown': 300
            }
        },
        'health_check': {
            'type': 'ELB',
            'grace_period': 300
        },
        'update_policy': {
            'min_instances_in_service': 1,
            'max_batch_size': 1,
            'pause_time': 'PT5M'
        }
    }
}

# Load AWS credentials from environment
AWS_CREDENTIALS = {
    'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
    'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
    'aws_security_group_id': os.environ.get('AWS_SECURITY_GROUP_ID'),
    'aws_iam_instance_profile': os.environ.get('AWS_IAM_INSTANCE_PROFILE')
}
