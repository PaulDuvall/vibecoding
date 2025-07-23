# Amazon SES Migration Technical Architecture

## Overview

This document defines the technical architecture for migrating from SendGrid to Amazon SES with AWS Parameter Store SecureString credential management, ensuring security, maintainability, and operational excellence.

---

## Current State Architecture

### SendGrid Integration
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   vibe_digest   │────│   email_utils    │────│   SendGrid API  │
│                 │    │                  │    │                 │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Orchestration │    │ • HTTP requests  │    │ • Email delivery│
│ • Error handling│    │ • JSON payload   │    │ • Rate limiting │
│ • Logging       │    │ • Auth headers   │    │ • Status codes  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌──────────────────┐
                       │  Environment     │
                       │  Variables       │
                       │                  │
                       │ • SENDGRID_API_KEY
                       │ • EMAIL_FROM     │
                       │ • EMAIL_TO       │
                       └──────────────────┘
```

### Issues with Current Architecture
- **Security**: API keys stored in plaintext environment variables
- **Dependency**: External service dependency outside AWS ecosystem
- **Cost**: Additional third-party service costs
- **Compliance**: Limited audit trail and credential rotation capabilities

---

## Target State Architecture

### SES with Parameter Store Integration
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   vibe_digest   │────│   email_utils    │────│   Amazon SES    │
│                 │    │                  │    │   (us-east-1)   │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Orchestration │    │ • boto3 client   │    │ • Email delivery│
│ • Error handling│    │ • SES send_email │    │ • AWS native    │
│ • Logging       │    │ • Exception mgmt │    │ • Rate limiting │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌──────────────────┐
                       │  config_loader   │
                       │                  │
                       ├──────────────────┤
                       │ • SSM client     │
                       │ • Parameter cache│
                       │ • Error handling │
                       └──────────────────┘
                                ▲
                                │
                       ┌──────────────────┐
                       │ AWS Parameter    │
                       │ Store            │
                       │                  │
                       │ SecureString:    │
                       │ • access_key_id  │
                       │ • secret_key     │
                       │                  │
                       │ Standard:        │
                       │ • region         │
                       │ • from_address   │
                       └──────────────────┘
```

---

## Component Architecture

### 1. Email Delivery Layer (`src/email_utils.py`)

#### Current Implementation
```python
def send_email(html: str) -> None:
    # SendGrid API integration
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    response = requests.post("https://api.sendgrid.com/v3/mail/send", ...)
```

#### Target Implementation
```python
def send_email(html: str) -> None:
    # SES integration with Parameter Store
    credentials = get_aws_credentials()
    ses_client = boto3.client('ses', region_name=credentials['region'])
    ses_client.send_email(...)
```

#### Responsibilities
- **Email Formatting**: Maintain existing subject and HTML content generation
- **SES Client Management**: Initialize and configure boto3 SES client
- **Error Handling**: Process AWS-specific exceptions and provide meaningful errors
- **Logging**: Log delivery status without exposing credentials

### 2. Configuration Layer (`src/config_loader.py`)

#### New Module Requirements
```python
class AWSCredentialManager:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self._credential_cache = {}
    
    def get_aws_credentials(self) -> Dict[str, str]:
        """Retrieve AWS credentials from Parameter Store with caching"""
        
    def get_email_config(self) -> Dict[str, str]:
        """Retrieve email configuration from Parameter Store"""
```

#### Responsibilities
- **Parameter Store Access**: Secure retrieval of SecureString parameters
- **Credential Caching**: In-memory caching to minimize AWS API calls
- **Error Management**: Handle missing parameters and access denied scenarios
- **Security**: Ensure no credential logging or memory persistence

### 3. AWS Services Integration

#### Parameter Store Structure
```
/vibecoding/
├── aws/
│   ├── access_key_id     (SecureString, KMS encrypted)
│   ├── secret_access_key (SecureString, KMS encrypted)
│   └── region           (String, "us-east-1")
└── email/
    ├── from_address     (String, verified SES address)
    └── to_address       (String, recipient email)
```

#### IAM Role Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "ses:FromAddress": ["verified-sender@domain.com"]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters"
            ],
            "Resource": [
                "arn:aws:ssm:us-east-1:*:parameter/vibecoding/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": [
                "arn:aws:kms:us-east-1:*:key/*"
            ],
            "Condition": {
                "StringEquals": {
                    "kms:ViaService": "ssm.us-east-1.amazonaws.com"
                }
            }
        }
    ]
}
```

---

## Security Architecture

### 1. Credential Management

#### SecureString Encryption
- **Encryption**: AWS managed KMS keys (aws/ssm default key)
- **Access Control**: IAM policies restrict parameter access to specific paths
- **Audit Trail**: CloudTrail logs all parameter access events
- **Rotation**: Support for credential rotation without code deployment

#### In-Memory Security
```python
class SecureCredentialHandler:
    def __init__(self):
        self._credentials = {}
    
    def load_credentials(self):
        # Load from Parameter Store
        pass
    
    def clear_credentials(self):
        # Explicitly clear sensitive data
        for key in self._credentials:
            self._credentials[key] = None
        self._credentials.clear()
    
    def __del__(self):
        self.clear_credentials()
```

### 2. Network Security

#### VPC Integration (Optional)
```
┌─────────────────────────────────────────────────────────────┐
│                        VPC                                  │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────────┐ │
│  │  Lambda/EC2     │────│        VPC Endpoints            │ │
│  │  Application    │    │                                  │ │
│  │                 │    │  • ssm.us-east-1.amazonaws.com  │ │
│  └─────────────────┘    │  • ses.us-east-1.amazonaws.com  │ │
│                         │                                  │ │
│                         └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3. Error Handling Security

#### Secure Error Messages
```python
class SecureErrorHandler:
    @staticmethod
    def sanitize_aws_error(error: ClientError) -> str:
        """Remove sensitive information from AWS error messages"""
        safe_messages = {
            'AccessDenied': 'AWS access denied. Check IAM permissions.',
            'ParameterNotFound': 'Configuration parameter not found.',
            'InvalidParameterValue': 'Invalid parameter configuration.'
        }
        return safe_messages.get(error.response['Error']['Code'], 
                               'AWS service error occurred.')
```

---

## Performance Architecture

### 1. Credential Caching Strategy

#### Implementation Pattern
```python
class ParameterStoreCache:
    def __init__(self, ttl_seconds: int = 300):  # 5-minute TTL
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get_parameter(self, name: str) -> str:
        if self._is_cache_valid(name):
            return self._cache[name]['value']
        
        # Refresh from Parameter Store
        value = self._fetch_from_parameter_store(name)
        self._cache[name] = {
            'value': value,
            'timestamp': time.time()
        }
        return value
```

### 2. Connection Management

#### SES Client Pooling
```python
class SESClientManager:
    def __init__(self):
        self._client = None
        self._client_created_at = None
        self._client_ttl = 3600  # 1 hour
    
    def get_client(self) -> boto3.client:
        if self._should_refresh_client():
            credentials = get_aws_credentials()
            self._client = boto3.client('ses', 
                                      region_name=credentials['region'],
                                      aws_access_key_id=credentials['access_key_id'],
                                      aws_secret_access_key=credentials['secret_access_key'])
            self._client_created_at = time.time()
        return self._client
```

---

## Testing Architecture

### 1. Unit Testing Strategy

#### Mock Patterns
```python
@pytest.fixture
def mock_parameter_store():
    with patch('boto3.client') as mock_client:
        mock_ssm = mock_client.return_value
        mock_ssm.get_parameter.return_value = {
            'Parameter': {'Value': 'test-value'}
        }
        yield mock_ssm

@pytest.fixture  
def mock_ses_client():
    with patch('boto3.client') as mock_client:
        mock_ses = mock_client.return_value
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        yield mock_ses
```

### 2. Integration Testing

#### Real AWS Service Testing
```python
class TestSESIntegration:
    def test_parameter_store_retrieval(self):
        """Test actual Parameter Store parameter retrieval"""
        # Use real AWS credentials in test environment
        
    def test_ses_email_delivery(self):
        """Test actual SES email sending to test recipient"""
        # Use verified test email addresses
```

### 3. Security Testing

#### Credential Exposure Testing
```python
class TestCredentialSecurity:
    def test_no_credentials_in_logs(self):
        """Verify no AWS credentials appear in log output"""
        
    def test_credential_memory_cleanup(self):
        """Verify credentials are cleared from memory"""
        
    def test_parameter_access_permissions(self):
        """Verify IAM permissions work correctly"""
```

---

## Deployment Architecture

### 1. Migration Strategy

#### Phase 1: Parallel Implementation
```
Current SendGrid ────┐
                     ├──── Feature Flag ──── Email Delivery
New SES Integration ─┘
```

#### Phase 2: Gradual Migration
```
10% Traffic ────── SES Integration
90% Traffic ────── SendGrid (fallback)
```

#### Phase 3: Complete Migration
```
100% Traffic ────── SES Integration
SendGrid ─────────── Deprecated/Removed
```

### 2. Infrastructure Requirements

#### AWS Prerequisites
1. **SES Configuration**
   - Verify sender email address in SES console
   - Request production sending limits (out of sandbox)
   - Configure bounce and complaint handling

2. **Parameter Store Setup**
   - Create SecureString parameters with appropriate KMS keys
   - Set up parameter hierarchy: `/vibecoding/aws/*` and `/vibecoding/email/*`

3. **IAM Configuration**
   - Create service role with minimal required permissions
   - Implement resource-based access controls
   - Set up cross-account access if needed

### 3. Monitoring and Observability

#### CloudWatch Integration
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │────│   CloudWatch     │────│    Alarms       │
│   Metrics       │    │   Logs/Metrics   │    │                 │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Email success │    │ • Log aggregation│    │ • Failure alerts│
│ • Delivery time │    │ • Custom metrics │    │ • Performance   │
│ • Error rates   │    │ • Dashboards     │    │ • Security      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Rollback Architecture

### 1. Feature Flag Implementation

#### Configuration-Based Switching
```python
class EmailDeliveryStrategy:
    def __init__(self):
        self.use_ses = os.getenv('USE_SES_EMAIL', 'false').lower() == 'true'
    
    def send_email(self, html: str) -> None:
        if self.use_ses:
            return self._send_via_ses(html)
        else:
            return self._send_via_sendgrid(html)
```

### 2. Rollback Triggers

#### Automated Rollback Conditions
- SES delivery failure rate > 5% over 10 minutes
- Parameter Store access failures
- AWS service availability issues
- Performance degradation > 50% from baseline

#### Manual Rollback Process
1. Update environment variable: `USE_SES_EMAIL=false`
2. Restart application services
3. Verify SendGrid functionality
4. Monitor delivery success rates

---

## Maintenance and Operations

### 1. Credential Rotation

#### Automated Rotation Process
```python
def rotate_aws_credentials():
    """Rotate AWS credentials stored in Parameter Store"""
    # Create new IAM access key
    # Update Parameter Store with new credentials
    # Test new credentials with SES
    # Deactivate old credentials
    # Log rotation completion
```

### 2. Monitoring and Alerting

#### Key Metrics
- **Email Delivery Success Rate**: Target 99.5%+
- **Parameter Store Retrieval Latency**: Target <500ms
- **SES API Response Time**: Target <2 seconds
- **AWS Service Error Rate**: Target <1%

#### Alert Thresholds
- Email delivery failures: >3 failures in 5 minutes
- Parameter Store access issues: Any access denied errors
- SES rate limiting: Approaching sending limits
- Cost anomalies: >20% increase in AWS costs

---

**Architecture Version**: 1.0.0  
**Last Updated**: 2025-07-23  
**Review Cycle**: Monthly  
**Owner**: Platform Engineering Team