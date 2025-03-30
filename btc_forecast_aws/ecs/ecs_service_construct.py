# constructs/ecs/ecs_service_construct.py
from aws_cdk import (
    aws_ecs as ecs,
    aws_iam as iam,
)
from constructs import Construct

class EcsEc2ServiceConstruct(Construct):
    def __init__(self, scope: Construct, id: str, cluster: ecs.Cluster, image_uri: str) -> None:
        super().__init__(scope, id)

        task_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),  # ✅ this line!

            ]
        )

        task_def = ecs.Ec2TaskDefinition(self, "TaskDef",
                                         execution_role=task_role,
                                          network_mode=ecs.NetworkMode.AWS_VPC)
        task_def.add_container(
            "ScraperContainer",
            image=ecs.ContainerImage.from_registry(image_uri),
            memory_limit_mib=512,
            cpu=256,
            essential=True,
        )

        self.service = ecs.Ec2Service(
            self, "ScraperService",
            cluster=cluster,
            task_definition=task_def,
            desired_count=1,
        )
