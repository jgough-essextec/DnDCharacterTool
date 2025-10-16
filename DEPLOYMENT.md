# Deployment Guide

This guide covers deploying the D&D Character Creator to AWS using Zappa.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured locally
- Python 3.11+ with virtual environment activated
- PostgreSQL database (AWS RDS recommended)
- S3 buckets created for static files and Zappa deployments

## Environment Setup

### 1. AWS Configuration

Ensure your AWS CLI is configured:

```bash
aws configure
```

You'll need IAM permissions for:
- Lambda (Full Access)
- API Gateway (Full Access)
- S3 (Full Access)
- CloudFormation (Full Access)
- CloudWatch Logs (Full Access)
- VPC (for RDS access)
- IAM (for role creation)

### 2. Create S3 Buckets

```bash
# For Zappa deployments
aws s3 mb s3://your-zappa-deployments-bucket

# For static/media files
aws s3 mb s3://your-static-files-bucket
```

### 3. Set Up RDS PostgreSQL

1. Create an RDS PostgreSQL instance
2. Configure security groups to allow Lambda access
3. Note the endpoint, database name, username, and password

## Zappa Configuration

### 1. Initialize Zappa

```bash
zappa init
```

### 2. Configure zappa_settings.json

Update the generated file with your settings:

```json
{
    "dev": {
        "django_settings": "dnd_character_creator.settings.production",
        "s3_bucket": "your-zappa-deployments-bucket",
        "aws_region": "us-east-1",
        "runtime": "python3.11",
        "vpc_config": {
            "SubnetIds": ["subnet-xxxxx", "subnet-yyyyy"],
            "SecurityGroupIds": ["sg-xxxxx"]
        },
        "environment_variables": {
            "DEBUG": "False",
            "SECRET_KEY": "your-production-secret-key",
            "DB_NAME": "your_db_name",
            "DB_USER": "your_db_user",
            "DB_PASSWORD": "your_db_password",
            "DB_HOST": "your-rds-endpoint.amazonaws.com",
            "DB_PORT": "5432",
            "AWS_STORAGE_BUCKET_NAME": "your-static-files-bucket"
        },
        "keep_warm": false,
        "memory_size": 512,
        "timeout": 30
    },
    "production": {
        // Similar configuration with production values
    }
}
```

## Deployment Steps

### 1. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 2. Initial Deployment

```bash
# Deploy to development
zappa deploy dev

# Or deploy to production
zappa deploy production
```

### 3. Run Migrations

```bash
zappa manage dev migrate
```

### 4. Create Superuser

```bash
zappa manage dev createsuperuser
```

### 5. Load Initial Data

```bash
zappa manage dev import_dnd_data
```

## Updating Deployments

For subsequent updates:

```bash
# Update development
zappa update dev

# Update production
zappa update production
```

## Monitoring

### CloudWatch Logs

View logs:

```bash
zappa tail dev
```

### CloudWatch Metrics

Set up alarms in AWS Console for:
- Lambda errors
- Lambda duration
- API Gateway 4XX/5XX errors

## Rollback

If needed, rollback to previous version:

```bash
zappa rollback dev -n 1
```

## Custom Domain (Optional)

### 1. Certificate

Create an ACM certificate for your domain in us-east-1.

### 2. Update Zappa Settings

```json
{
    "dev": {
        "domain": "api.yourdomain.com",
        "certificate_arn": "arn:aws:acm:us-east-1:xxxx:certificate/yyyy"
    }
}
```

### 3. Deploy Domain

```bash
zappa certify dev
```

## Troubleshooting

### Common Issues

1. **Lambda Timeout**: Increase `timeout` in zappa_settings.json
2. **Memory Issues**: Increase `memory_size`
3. **Database Connection**: Check VPC and security group configuration
4. **Static Files 404**: Verify S3 bucket configuration and CORS settings

### Debug Mode

For debugging, temporarily enable debug mode:

```bash
zappa update dev -s DEBUG=True
```

Remember to disable after debugging!

## Cost Optimization

- Use CloudWatch to monitor Lambda invocations
- Set up billing alerts
- Consider Reserved Instances for RDS
- Use S3 lifecycle policies for old files
- Clean up old Lambda versions: `zappa manage dev delete_old_versions`

## Security Best Practices

- Never commit secrets to git
- Use AWS Secrets Manager for sensitive data
- Enable RDS encryption
- Set up WAF rules for API Gateway
- Regular security audits with `bandit` and `safety`