from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_autoscaling as autoscaling
)
from constructs import Construct

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

        # 🧱 Auto Scaling Group (with ECS-optimized AMI)
        asg = autoscaling.AutoScalingGroup(
            self, "EcsAsg",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            desired_capacity=1,
            min_capacity=1,
            max_capacity=1,
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
            ]
        )

        # ⚙️ Attach Capacity Provider
        capacity_provider = ecs.AsgCapacityProvider(
            self, "EcsAsgCapacityProvider",
            auto_scaling_group=asg
        )

        self.cluster.add_asg_capacity_provider(capacity_provider)
