import boto3
import os
import socket
import time
import paramiko

ec2_resource = boto3.resource('ec2', region_name='us-east-1')
ec2_client = boto3.client('ec2')

with open('userdata.sh', 'r') as f:
    user_data_script = f.read()

# Create the instance
instances = ec2_resource.create_instances(
    ImageId='ami-084568db4383264d4', # Ubuntu AMI for us-east-1
    MinCount=1,
    MaxCount=1,
    InstanceType=os.environ["INSTANCE_TYPE"],
    KeyName=os.environ["KEYPAIR_NAME"],  # Replace with your actual key pair
    SecurityGroupIds=[os.environ["SECURITY_GROUP"]],  # Replace with your security group ID
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/xvda',
            'Ebs': {
                'VolumeSize': int(os.environ["MEMORY_SIZE"]),
                'VolumeType': 'gp3',
                'DeleteOnTermination': True,
                'Encrypted': False
            }
        },
    ],
    UserData=user_data_script,
    IamInstanceProfile={
        'Arn': os.environ["IAM_INSTANCE_PROFILE"]  # Or use 'Arn': 'arn:aws:iam::123456789012:instance-profile/your-profile'
    },
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': os.environ["INSTANCE_NAME"]} 
            ]
        }
    ]
)


for instance in instances:
    print(f"Launching instance with ID: {instance.id}")

instance = instances[0]

# 2. Wait until it's running and has a public IP
print("Waiting for instance to run...")
instance.wait_until_running()
instance.reload()
print("Instance Ready")

print("Associating EIP")
ec2_client.associate_address(
    InstanceId=instance.id,
    AllocationId=os.environ["ELASTIC_IP_ID"]
)
print("EIP associated")


def wait_for_ssh(host, port=22, timeout=300):

    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except OSError as e:
            print(f"Error: {e}")
            time.sleep(5)
    raise TimeoutError("SSH did not become available in time.")

print("Waiting for SSH")
wait_for_ssh(instance.public_dns_name)
print("SSH ready")

print("Getting key")
key = paramiko.RSAKey.from_private_key_file(os.environ["PATH_TO_KEYPAIR"])
print("Creating ssh client")
ssh = paramiko.SSHClient()

print("Setting missing host key policy")
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("Connecting with ssh client")
ssh.connect(instance.public_dns_name, username="ubuntu", pkey=key)

print("Running full startup script...")
stdin, stdout, stderr = ssh.exec_command('source ./dolphin_capture/deploy/init.ssh')

# Stream stdout in real-time
while not stdout.channel.exit_status_ready():
    if stdout.channel.recv_ready():
        output = stdout.channel.recv(1024).decode('utf-8')
        print(output, end='')

    time.sleep(0.1)  # Avoid tight loop

# Optionally capture final exit status and stderr
exit_status = stdout.channel.recv_exit_status()
if exit_status != 0:
    error_output = stderr.read().decode()
    print("Error:", error_output)

print(f"\nCommand exited with status {exit_status}")
ssh.close()

print("DONE")
