import boto3
from aws_cdk import aws_ecr as ecr
from constructs import Construct

class EcrConstruct(Construct):
    def __init__(self, scope: Construct, id: str, repo_name: str = "crypto_repo") -> None:
        super().__init__(scope, id)

        # Use the passed-in repo_name or default to "crypto_repo"
        self.repo_name = repo_name

        ecr_client = boto3.client("ecr")
        try:
            # Check if repo exists
            ecr_client.describe_repositories(repositoryNames=[self.repo_name])
            print(f"✔️ ECR repository '{self.repo_name}' exists. Importing.")
            self.repository = ecr.Repository.from_repository_name(
                self, "ImportedRepo", repository_name=self.repo_name
            )
        except ecr_client.exceptions.RepositoryNotFoundException:
            print(f"❌ ECR repository '{self.repo_name}' does not exist. Creating it.")
            self.repository = ecr.Repository(
                self, "AppEcrRepo",
                repository_name=self.repo_name
            )
