from aws_cdk import (
    aws_ecs as ecs,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_ec2 as ec2,
    RemovalPolicy,
)
from constructs import Construct

class ScheduledScraperTaskConstruct(Construct):
    def __init__(self, scope: Construct, id: str, cluster: ecs.Cluster, image_uri: str, queue: sqs.Queue) -> None:
        super().__init__(scope, id)

        task_role = iam.Role(
            self, "ScraperScheduledTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),
            ]
        )
        queue.grant_send_messages(task_role)

        log_group_name = "/ecs/scraper"

        # Attempt to import the log group if it exists
        try:
            log_group = logs.LogGroup.from_log_group_name(self, "ScraperLogGroup", log_group_name)
        except Exception:
            # If the log group does not exist, create a new one
            log_group = logs.LogGroup(
                self, "ScraperLogGroup",
                log_group_name=log_group_name,
                removal_policy=RemovalPolicy.DESTROY
            )

        task_def = ecs.Ec2TaskDefinition(
            self, "ScraperTaskDefinition",
            task_role=task_role,
            network_mode=ecs.NetworkMode.BRIDGE
        )

        task_def.add_container(
            "ScraperContainer",
            image=ecs.ContainerImage.from_registry(image_uri),
            memory_limit_mib=512,
            cpu=256,
            environment={"QUEUE_URL": queue.queue_url},
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="scraper",
                log_group=log_group
            )
        )

        rule = events.Rule(
            self, "HourlyScraperSchedule",
            schedule=events.Schedule.cron(minute="0", hour="*"),  # every hour
        )

        rule.add_target(
            targets.EcsTask(
                cluster=cluster,
                task_definition=task_def,
                task_count=1,
                #subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),  # or PRIVATE_WITH_EGRESS
            )
        )
