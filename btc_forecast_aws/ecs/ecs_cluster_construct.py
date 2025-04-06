from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_autoscaling as autoscaling
)
from constructs import Construct
import dotenv
import os 
dotenv.load_dotenv("btc_forecast_aws/.env")

WG_CLIENT_KEY = os.getenv("WG_CLIENT_KEY")
if not WG_CLIENT_KEY:
    raise ValueError("WG_CLIENT_KEY not found in environment!")

WG_SERVER_KEY = os.getenv("WG_SERVER_KEY")
if not WG_SERVER_KEY:
    raise ValueError("WG_SERVER_KEY not found in environment!")
    


class EcsClusterConstruct(Construct):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc) -> None:
        super().__init__(scope, id)

        # ✅ Create ECS Cluster first
        self.cluster = ecs.Cluster(self, "EcsEc2Cluster", vpc=vpc)

        # 🛡️ EC2 IAM Role
        ecs_instance_role = iam.Role(
            self, "EcsInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),
            ]
        )
        user_data = ec2.UserData.for_linux()

        


        user_data.add_commands(
            "set -e",
            "amazon-linux-extras enable epel",
            "amazon-linux-extras enable kernel-5.10",
            "yum clean metadata",
            "yum install -y epel-release",
            "yum install -y wireguard-tools iptables-services kernel-devel-$(uname -r) kernel-headers-$(uname -r)",
            "mkdir -p /etc/wireguard",
            "cat <<EOF > /etc/wireguard/wg0.conf",
            "[Interface]",
            f"PrivateKey = {WG_CLIENT_KEY}",
            "Address = 10.66.66.3/32",
            "DNS = 1.1.1.1",
            "",
            "[Peer]",
            f"PublicKey = {WG_SERVER_KEY}",
            "Endpoint = drunkduckface.duckdns.org:443",
            "AllowedIPs = 0.0.0.0/0",
            "PersistentKeepalive = 25",
            "EOF",
            "chmod 600 /etc/wireguard/wg0.conf",
            "systemctl enable wg-quick@wg0",
            "systemctl start wg-quick@wg0",
            'echo "ECS_CLUSTER=BtcForecastAwsStack-EcsClusterEcsEc2ClusterF779F1E0-GngTcoqmzfma" >> /etc/ecs/ecs.config',
            'echo "ECS_AWSVPC_BLOCK_IMDS=true" >> /etc/ecs/ecs.config',
            "iptables --insert FORWARD 1 --in-interface docker+ --destination 169.254.169.254/32 --jump DROP",
            "service iptables save"
        )
        

        # 🧱 Auto Scaling Group (with ECS-optimized AMI)
        asg = autoscaling.AutoScalingGroup(
            self, "EcsAsg",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2023(),
            desired_capacity=1,
            min_capacity=0,
            max_capacity=2,
            key_name="alice_lap",
            associate_public_ip_address=True,
            role=ecs_instance_role,
            block_devices=[
                autoscaling.BlockDevice(
                    device_name="/dev/xvda",
                    volume=autoscaling.BlockDeviceVolume.ebs(
                        volume_size=30,
                        volume_type=autoscaling.EbsDeviceVolumeType.GP3
                    )
                )
            ] ,
            user_data=user_data 
        )

        # ⚙️ Attach Capacity Provider
        capacity_provider = ecs.AsgCapacityProvider(
            self, "EcsAsgCapacityProvider",
            auto_scaling_group=asg
        )

        self.cluster.add_asg_capacity_provider(capacity_provider)
