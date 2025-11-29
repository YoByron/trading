# Cloud RL Service Integration Guide

**Last Updated**: November 26, 2025
**Status**: ✅ **FULLY INTEGRATED**

---

## 🎯 Overview

The trading system now supports cloud-hosted reinforcement learning services for scalable model training. This allows you to:

- **Train models in the cloud** - Offload compute-intensive RL training
- **Use managed RL services** - Leverage Vertex AI RL, Azure ML RL, AWS SageMaker RL
- **Scale training** - Handle larger datasets and longer training runs
- **Fallback to local** - Automatic fallback if cloud service unavailable

---

## 🔑 Setup

### 1. Add RL_AGENT_KEY to .env

```bash
# Add to your .env file
RL_AGENT_KEY=your_vertex_ai_api_key_here
```

For Vertex AI, you can use:
- **API Key**: Direct API key string
- **Service Account**: Path to JSON file (e.g., `/path/to/service-account.json`)

### 2. (Optional) Configure Google Cloud Project

For full Vertex AI SDK integration:

```bash
# Add to .env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  # or your preferred region
```

### 3. Install Vertex AI SDK (Optional)

```bash
pip install google-cloud-aiplatform
```

**Note**: The system works without the SDK (API key mode), but full integration requires the SDK.

---

## 🚀 Usage

### Basic Training with Cloud RL

```python
from src.ml.trainer import ModelTrainer

# Initialize trainer with cloud RL enabled
trainer = ModelTrainer(use_cloud_rl=True, rl_provider="vertex_ai")

# Train a model (will submit to cloud RL service)
result = trainer.train_supervised("SPY")
print(f"Job ID: {result['job_id']}")
print(f"Status: {result['status']}")
```

### Command Line Training

```bash
# Train with cloud RL (default)
python scripts/train_with_cloud_rl.py --symbols SPY QQQ

# Train locally (bypass cloud)
python scripts/train_with_cloud_rl.py --symbols SPY --local

# Use different provider
python scripts/train_with_cloud_rl.py --symbols SPY --provider azure_ml
```

### Test Connection

```bash
# Test RL service connection
python scripts/test_rl_service.py
```

---

## 📋 Supported Providers

### 1. Vertex AI RL (Default)

**Provider**: `vertex_ai`

**Requirements**:
- `RL_AGENT_KEY` in .env (API key or service account path)
- Optional: `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`

**Features**:
- Managed RL training jobs
- Automatic scaling
- Integration with Google Cloud ML

### 2. Azure ML RL

**Provider**: `azure_ml`

**Requirements**:
- `RL_AGENT_KEY` in .env
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `AZURE_ML_WORKSPACE`

### 3. AWS SageMaker RL

**Provider**: `aws_sagemaker`

**Requirements**:
- AWS credentials configured (`~/.aws/credentials` or environment)
- `RL_AGENT_KEY` (optional, for custom auth)

### 4. Paperspace

**Provider**: `paperspace`

**Requirements**:
- `RL_AGENT_KEY` (Paperspace API key)

---

## 🔧 Integration Points

### ModelTrainer Integration

The `ModelTrainer` class automatically supports cloud RL:

```python
# Enable cloud RL
trainer = ModelTrainer(use_cloud_rl=True)

# Train (will use cloud if available, fallback to local)
result = trainer.train_supervised("SPY")
```

### RLServiceClient Direct Usage

```python
from src.ml.rl_service_client import RLServiceClient

# Initialize client
client = RLServiceClient(provider="vertex_ai")

# Submit training job
env_spec = {
    "name": "trading_env",
    "state_space": "continuous",
    "action_space": "discrete",
    "actions": ["BUY", "SELL", "HOLD"]
}

job_info = client.start_training(
    env_spec=env_spec,
    algorithm="DQN",
    job_name="my_training_job"
)

# Check job status
status = client.get_job_status(job_info["job_id"])

# Get trained policy
policy = client.get_trained_policy(job_info["job_id"])
```

---

## 📊 Training Workflow

### Cloud RL Training Flow

```
1. Initialize ModelTrainer with use_cloud_rl=True
   ↓
2. Prepare environment specification
   ↓
3. Submit job to cloud RL service
   ↓
4. Receive job_id and status
   ↓
5. (Async) Monitor job status
   ↓
6. (When complete) Download trained policy
   ↓
7. Integrate policy into trading system
```

### Fallback Behavior

If cloud RL fails or is unavailable:
- Automatically falls back to local training
- Logs warning but continues execution
- No interruption to training pipeline

---

## 🧪 Testing

### Test RL Service Connection

```bash
python scripts/test_rl_service.py
```

**Expected Output**:
```
✅ RL_AGENT_KEY loaded (length: 39)
✅ Connected to RL service (Vertex AI RL)
✅ Training job submitted successfully
   Job ID: vertex_ai_dqn_trading_v1
   Status: submitted
```

### Test ModelTrainer Integration

```python
from src.ml.trainer import ModelTrainer

trainer = ModelTrainer(use_cloud_rl=True)
result = trainer.train_supervised("SPY", use_cloud_rl=True)
assert result["success"] == True
assert "job_id" in result
```

---

## 🔍 Monitoring

### Check Job Status

```python
from src.ml.rl_service_client import RLServiceClient

client = RLServiceClient()
status = client.get_job_status("your_job_id")
print(status)
```

### View Training Logs

Cloud RL services provide logs through their respective dashboards:
- **Vertex AI**: Google Cloud Console → Vertex AI → Training Jobs
- **Azure ML**: Azure Portal → Machine Learning → Jobs
- **AWS SageMaker**: AWS Console → SageMaker → Training Jobs

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RL_AGENT_KEY` | Yes | API key or service account path |
| `GOOGLE_CLOUD_PROJECT` | No* | GCP project ID (for Vertex AI SDK) |
| `GOOGLE_CLOUD_LOCATION` | No* | GCP region (default: us-central1) |
| `AZURE_SUBSCRIPTION_ID` | No* | Azure subscription (for Azure ML) |
| `AZURE_RESOURCE_GROUP` | No* | Azure resource group (for Azure ML) |
| `AZURE_ML_WORKSPACE` | No* | Azure ML workspace name |

*Required only for full SDK integration with that provider

### Code Configuration

```python
# Enable cloud RL
trainer = ModelTrainer(
    use_cloud_rl=True,           # Enable cloud RL
    rl_provider="vertex_ai",      # Choose provider
    models_dir="models/ml",       # Local model directory
    device="cpu"                  # Device for local fallback
)
```

---

## 🛠️ Troubleshooting

### RL_AGENT_KEY Not Found

**Error**: `RL_AGENT_KEY environment variable must be set`

**Fix**: Add `RL_AGENT_KEY=your_key` to `.env` file

### Vertex AI SDK Not Installed

**Warning**: `google-cloud-aiplatform not installed`

**Fix**:
```bash
pip install google-cloud-aiplatform
```

**Note**: System works in API key mode without SDK, but full features require SDK.

### Cloud Service Unavailable

**Behavior**: Automatic fallback to local training

**Check**:
- Verify API key is valid
- Check cloud service status
- Review logs for specific error messages

### Job Submission Fails

**Possible Causes**:
- Invalid API key
- Insufficient permissions
- Service quota exceeded
- Network connectivity issues

**Debug**:
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test connection
from src.ml.rl_service_client import RLServiceClient
client = RLServiceClient()
```

---

## 📈 Best Practices

1. **Use Cloud RL for Production**: Offload compute-intensive training
2. **Keep Local Fallback**: Always have local training as backup
3. **Monitor Job Status**: Check job progress regularly
4. **Set Resource Limits**: Configure appropriate timeouts and quotas
5. **Version Control**: Track which models were trained with which jobs
6. **Cost Management**: Monitor cloud service usage and costs

---

## 🎯 Next Steps

1. **Configure Google Cloud Project** (for Vertex AI)
   - Enable Vertex AI API
   - Set up service account or API key
   - Configure project and location

2. **Set Up Training Pipeline**
   - Create training container/image
   - Configure environment specifications
   - Set up monitoring and alerts

3. **Integrate with Trading System**
   - Use trained policies in trading decisions
   - Set up automatic retraining schedule
   - Monitor model performance

---

**CTO**: Claude (AI Agent)
**CEO**: Igor Ganapolsky
