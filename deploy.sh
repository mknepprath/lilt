#!/bin/bash

# Bundle the dependencies
pip install -t bundle -r requirements.txt --upgrade

# Add function code to bundle
cp bot.py bundle
cp command.py bundle
cp constants.py bundle
cp db.py bundle
cp event.py bundle
cp item.py bundle
cp lambda_function.py bundle
cp utils.py bundle

# Delete dependencies hosted on AWS
rm -rf bundle/numpy bundle/pandas bundle/numpy-*.dist-info bundle/pandas-*.dist-info

# Zip the bundle
cd bundle
zip -r ../bundle.zip *
cd ..

# Upload the bundle to S3
aws s3 cp bundle.zip s3://liltbot

# Delete the bundle locally
rm -rf bundle bundle.zip

# Update the Lambda function
aws lambda update-function-code --function-name lilt --s3-bucket liltbot --s3-key bundle.zip --region us-east-1
