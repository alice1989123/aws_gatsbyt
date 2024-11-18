import aws_cdk as core
import aws_cdk.assertions as assertions

from btc_forecast_aws.btc_forecast_aws_stack import BtcForecastAwsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in btc_forecast_aws/btc_forecast_aws_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BtcForecastAwsStack(app, "btc-forecast-aws")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
