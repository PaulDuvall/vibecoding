# Amazon SES Migration Implementation Checklist

This checklist provides a comprehensive step-by-step guide for implementing the SendGrid to Amazon SES migration with AWS Parameter Store SecureString credential management.

---

## Pre-Migration Infrastructure Setup

### AWS SES Configuration
- [ ] **Verify Sender Email Address**
  - [ ] Access Amazon SES console in us-east-1 region
  - [ ] Add and verify sender email address
  - [ ] Confirm verification email and complete process
  - [ ] Test sending from verified address

- [ ] **Request Production Access**
  - [ ] Submit request to move SES out of sandbox mode
  - [ ] Provide business justification for sending limits
  - [ ] Wait for AWS approval (typically 24-48 hours)
  - [ ] Confirm production sending limits are adequate

- [ ] **Configure SES Settings**
  - [ ] Set up bounce and complaint handling
  - [ ] Configure reputation tracking
  - [ ] Enable sending statistics
  - [ ] Review default configuration limits

### AWS Parameter Store Setup
- [ ] **Create Parameter Hierarchy**
  - [ ] Create `/vibecoding/aws/access_key_id` (SecureString)
  - [ ] Create `/vibecoding/aws/secret_access_key` (SecureString)  
  - [ ] Create `/vibecoding/aws/region` (String, value: "us-east-1")
  - [ ] Create `/vibecoding/email/from_address` (String, verified SES email)
  - [ ] Create `/vibecoding/email/to_address` (String, recipient email)

- [ ] **Configure KMS Encryption**
  - [ ] Use AWS managed key (aws/ssm) for SecureString parameters
  - [ ] Verify encryption is enabled on all SecureString parameters
  - [ ] Test parameter retrieval with decryption

- [ ] **Set Parameter Values**
  - [ ] Generate new IAM access key/secret for SES operations
  - [ ] Store credentials in SecureString parameters
  - [ ] Validate all parameter values are correct
  - [ ] Test parameter retrieval from CLI

### IAM Role Configuration
- [ ] **Create Service Role**
  - [ ] Create new IAM role for application
  - [ ] Attach minimal SES sending permissions
  - [ ] Attach Parameter Store read permissions
  - [ ] Attach KMS decrypt permissions for Parameter Store

- [ ] **Policy Validation**
  - [ ] Test SES send_email permission with role
  - [ ] Test Parameter Store get_parameter permission
  - [ ] Verify no unnecessary permissions are granted
  - [ ] Document role ARN for deployment

---

## Code Implementation Changes

### Dependency Updates
- [ ] **Modify requirements.txt**
  - [ ] Add `boto3>=1.26.0` for AWS SDK support
  - [ ] Pin boto3 version for reproducible builds
  - [ ] Keep existing `requests` for RSS feed functionality
  - [ ] Remove any SendGrid-specific dependencies

- [ ] **Update Development Environment**
  - [ ] Install new dependencies: `pip install -r requirements.txt`
  - [ ] Update virtual environment
  - [ ] Verify boto3 installation with import test

### Configuration Layer Implementation
- [ ] **Create config_loader.py Module**
  - [ ] Implement `AWSCredentialManager` class
  - [ ] Add Parameter Store client initialization
  - [ ] Implement credential caching mechanism
  - [ ] Add error handling for missing parameters
  - [ ] Create secure memory cleanup functions

- [ ] **Parameter Store Integration**
  - [ ] Implement `get_aws_credentials()` function
  - [ ] Implement `get_email_config()` function
  - [ ] Add credential validation logic
  - [ ] Implement cache refresh mechanism
  - [ ] Add logging without credential exposure

### Email Utility Refactoring
- [ ] **Modify src/email_utils.py**
  - [ ] Replace SendGrid imports with boto3
  - [ ] Remove `requests` dependency for email
  - [ ] Update `send_email()` function signature
  - [ ] Implement SES client initialization
  - [ ] Replace HTTP POST with `ses.send_email()`

- [ ] **Preserve Email Formatting**
  - [ ] Maintain identical subject generation logic
  - [ ] Preserve HTML content structure
  - [ ] Keep Eastern Time formatting
  - [ ] Maintain emoji support in subjects
  - [ ] Test email content integrity

- [ ] **Error Handling Updates**
  - [ ] Replace requests exceptions with boto3 exceptions
  - [ ] Add AWS-specific error handling (ClientError, BotoCoreError)
  - [ ] Implement exponential backoff for transient failures
  - [ ] Update logging for SES-specific errors

### Environment Variable Migration
- [ ] **Update Variable References**
  - [ ] Remove all `SENDGRID_API_KEY` references
  - [ ] Keep `EMAIL_TO` environment variable
  - [ ] Replace `EMAIL_FROM` with Parameter Store retrieval  
  - [ ] Add `AWS_REGION` as fallback configuration

- [ ] **Update Validation Logic**
  - [ ] Modify environment variable checks in `vibe_digest.py`
  - [ ] Update error messages for missing variables
  - [ ] Test configuration validation logic

---

## Testing Implementation

### Unit Test Updates
- [ ] **Update Existing Tests**
  - [ ] Replace SendGrid mocks with boto3 mocks
  - [ ] Update `test_vibe_digest.py` environment setup
  - [ ] Modify `test_integration.py` for SES testing
  - [ ] Update all test files removing `SENDGRID_API_KEY` references

- [ ] **Create New Test Files**
  - [ ] Create `tests/test_ses_integration.py`
  - [ ] Create `tests/test_parameter_store.py`  
  - [ ] Create `tests/test_error_handling.py`
  - [ ] Create `tests/test_security.py`
  - [ ] Create `tests/test_performance.py`

### Integration Testing
- [ ] **SES Integration Tests**
  - [ ] Test actual SES email sending (to test recipient)
  - [ ] Validate email content and formatting
  - [ ] Test SES error scenarios (rate limits, invalid recipients)
  - [ ] Verify delivery success logging

- [ ] **Parameter Store Integration Tests**
  - [ ] Test SecureString parameter retrieval
  - [ ] Test parameter caching functionality
  - [ ] Test error handling for missing parameters
  - [ ] Validate credential security (no logging)

### Performance Testing
- [ ] **Benchmark Performance**
  - [ ] Measure email delivery time including Parameter Store retrieval
  - [ ] Compare performance with SendGrid baseline
  - [ ] Test parameter caching effectiveness
  - [ ] Validate timeout compliance (30 seconds)

---

## Security Validation

### Credential Security Testing
- [ ] **Validate Secure Storage**
  - [ ] Confirm no credentials in source code
  - [ ] Verify SecureString encryption is active
  - [ ] Test parameter access with incorrect permissions
  - [ ] Validate credential cleanup in memory

- [ ] **Access Control Testing**
  - [ ] Test IAM role permissions work correctly
  - [ ] Verify denial of access without proper role
  - [ ] Test Parameter Store path-based restrictions
  - [ ] Validate KMS key usage for decryption

### Security Scanning
- [ ] **Code Security Scan**
  - [ ] Run automated security scan for hardcoded credentials
  - [ ] Check for AWS credential exposure in logs
  - [ ] Validate secure error handling (no credential leaks)
  - [ ] Review IAM policy for least-privilege compliance

---

## Documentation Updates

### Technical Documentation
- [ ] **Update CLAUDE.md**
  - [ ] Replace SendGrid references with SES
  - [ ] Update environment variable section
  - [ ] Add AWS Parameter Store setup instructions
  - [ ] Document new IAM role requirements

- [ ] **Update README.md**
  - [ ] Modify setup instructions for AWS prerequisites
  - [ ] Update environment variable documentation
  - [ ] Add SES verification instructions
  - [ ] Include troubleshooting for AWS issues

- [ ] **Update Architecture Documentation**
  - [ ] Modify ARCHITECTURE.md with SES integration
  - [ ] Document Parameter Store credential flow
  - [ ] Update system diagrams and flowcharts
  - [ ] Add security architecture documentation

### Configuration Files
- [ ] **Update GitHub Secrets**
  - [ ] Modify `scripts/set_github_secrets.sh`
  - [ ] Remove SENDGRID_API_KEY references
  - [ ] Add AWS credential variables for CI/CD
  - [ ] Update GitHub Actions workflow if needed

- [ ] **Update CI/CD Pipeline**
  - [ ] Modify `.github/workflows/vibe-coding-digest.yml`
  - [ ] Update environment variables for AWS
  - [ ] Add AWS credential configuration
  - [ ] Test CI/CD pipeline with new configuration

---

## Migration Execution

### Feature Flag Implementation
- [ ] **Add Feature Toggle**
  - [ ] Implement `USE_SES_EMAIL` environment variable
  - [ ] Create email delivery strategy pattern
  - [ ] Add fallback to SendGrid for rollback
  - [ ] Test feature flag switching functionality

### Gradual Migration Testing
- [ ] **Phase 1: Parallel Testing**
  - [ ] Deploy with feature flag disabled (SendGrid active)
  - [ ] Test SES functionality in background
  - [ ] Validate all SES components work correctly
  - [ ] Compare delivery success rates

- [ ] **Phase 2: Limited Production Testing**
  - [ ] Enable SES for 10% of email deliveries
  - [ ] Monitor delivery success rates
  - [ ] Compare performance metrics
  - [ ] Validate error handling in production

- [ ] **Phase 3: Full Migration**
  - [ ] Enable SES for 100% of email deliveries
  - [ ] Monitor for 48 hours
  - [ ] Validate all functionality works correctly
  - [ ] Remove SendGrid code and dependencies

### Rollback Preparation
- [ ] **Document Rollback Process**
  - [ ] Create step-by-step rollback instructions
  - [ ] Test rollback procedure in staging environment
  - [ ] Prepare emergency rollback commands
  - [ ] Define rollback triggers and thresholds

---

## Post-Migration Validation

### Operational Validation
- [ ] **Monitor Email Delivery**
  - [ ] Confirm 99%+ delivery success rate
  - [ ] Validate email formatting and content
  - [ ] Check delivery time performance
  - [ ] Monitor AWS costs for email delivery

- [ ] **Security Validation**
  - [ ] Confirm no credential exposure in logs
  - [ ] Validate Parameter Store access patterns
  - [ ] Review CloudTrail logs for security events
  - [ ] Test credential rotation procedures

### Cleanup Tasks
- [ ] **Remove SendGrid Dependencies**
  - [ ] Remove SendGrid references from code
  - [ ] Update all documentation
  - [ ] Remove SendGrid API key from secrets
  - [ ] Cancel SendGrid service subscription

- [ ] **Finalize Documentation**
  - [ ] Update operational runbooks
  - [ ] Create troubleshooting guides
  - [ ] Document lessons learned
  - [ ] Update team training materials

---

## Success Criteria Checklist

- [ ] Email delivery success rate ≥ 99% (matches SendGrid baseline)
- [ ] Email delivery time ≤ 30 seconds (including Parameter Store retrieval)
- [ ] All AWS credentials stored as SecureString parameters
- [ ] IAM role follows least-privilege principle
- [ ] No hardcoded credentials in source code
- [ ] All tests passing (unit, integration, security)
- [ ] Documentation updated and accurate
- [ ] Team trained on new AWS-based system
- [ ] Monitoring and alerting operational
- [ ] Rollback procedure tested and documented

---

**Checklist Version**: 1.0.0  
**Last Updated**: 2025-07-23  
**Estimated Implementation Time**: 3-5 days  
**Required Skills**: AWS services, Python, DevOps, Security