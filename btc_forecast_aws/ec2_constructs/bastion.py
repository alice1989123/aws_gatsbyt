from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    Stack
)
from constructs import Construct
from aws_cdk.aws_ec2 import KeyPair
import dotenv
import os 
dotenv.load_dotenv("btc_forecast_aws/.env")

WG_CLIENT_KEY = os.getenv("WG_CLIENT_KEY")
if not WG_CLIENT_KEY:
    raise ValueError("WG_CLIENT_KEY not found in environment!")

WG_SERVER_KEY = os.getenv("WG_SERVER_KEY")
if not WG_SERVER_KEY:
    raise ValueError("WG_SERVER_KEY not found in environment!")


class BastionHostWithWireGuard(Construct):
    def __init__(self, scope: Construct, construct_id: str, vpc ,**kwargs):
        super().__init__(scope, construct_id, **kwargs)
        # IAM Role for EC2 to access SSM
        role = iam.Role(
            self, "BastionHostRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
            ]
        )
        key_pair = ec2.KeyPair.from_key_pair_name(self, "ImportedKey", "bastion-key")

        # Amazon Linux 2 AMI with ECS support
        ami = ec2.MachineImage.latest_amazon_linux2()

        # Security Group
        sg = ec2.SecurityGroup(self, "BastionSG", vpc=vpc, allow_all_outbound=True)
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.udp(51820), "Allow WireGuard")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH")
        self.sg = sg
        # User data for configuring WireGuard
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
                "set -e",
                "amazon-linux-extras enable epel",
                "amazon-linux-extras enable kernel-5.10",
                "yum clean metadata",
                "yum install -y epel-release",
                "yum install -y wireguard-tools iptables-services kernel-devel-$(uname -r) kernel-headers-$(uname -r)",
                "mkdir -p /etc/wireguard",
                "cat <<EOF > /etc/wireguard/wg5.conf",
                "[Interface]",
                f"PrivateKey = {WG_SERVER_KEY}",
                "Address = 10.66.67.1/24",
                "ListenPort = 51820",
                "",
                "[Peer]",
                f"PublicKey = {WG_CLIENT_KEY}",
                "AllowedIPs = 10.66.67.2/32",
                "PersistentKeepalive = 25",
                "EOF",
                "chmod 600 /etc/wireguard/wg5.conf",
                "systemctl enable wg-quick@wg5",
                "systemctl start wg-quick@wg5",
                "iptables --insert FORWARD 1 --in-interface docker+ --destination 169.254.169.254/32 --jump DROP",
                "service iptables save"
            )


        # Bastion host EC2 instance
        self.bastion_instance = self.bastion_instance = ec2.Instance(
            self, "BastionHost",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ami,
            vpc=vpc,
            role=role,
            security_group=sg,
            user_data=user_data,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            key_pair=key_pair  # Make sure this key pair exists in AWS EC2 console
        )