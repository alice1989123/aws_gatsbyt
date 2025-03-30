# constructs/ecr/ecr_construct.py
from aws_cdk import aws_ecr as ecr
from constructs import Construct

class EcrConstruct(Construct):
    def __init__(self, scope: Construct, id: str, repo_name: str) -> None:
        super().__init__(scope, id)

        self.repository = ecr.Repository(
            self, "AppEcrRepo",
            repository_name="crypto_repo"
        )