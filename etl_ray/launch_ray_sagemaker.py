import sagemaker
from sagemaker.pytorch import PyTorchProcessor

# 1. Setup SageMaker session and role
role = "arn:aws:iam::135692633042:role/service-role/AmazonSageMakerAdminIAMExecutionRole"
session = sagemaker.Session()
region = session.boto_region_name

# 2. Define the Processor
instance_type = 'ml.t3.medium'

# PyTorchProcessor handles source_dir and requirements.txt automatically
processor = PyTorchProcessor(
    framework_version='2.1.0',
    py_version='py310',
    role=role,
    instance_count=1,
    instance_type=instance_type,
    base_job_name='ray-etl-noaa-practice',
    sagemaker_session=session
)

# 3. Run the Job
print(f"Starting SageMaker Processing Job on {instance_type}...")
processor.run(
    code='etl_ray_practice.py',
    source_dir='.', # Uploads etl_ray folder (including requirements.txt)
    wait=False
)

print(f"Job submitted! Monitor in Classic Console:")
print(f"https://{region}.console.aws.amazon.com/sagemaker/home?region={region}#/processing-jobs")
