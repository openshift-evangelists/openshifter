#!/bin/bash

if [ "$#" -ne 2 ]; then
   echo "Usage:  ./create_project.sh <PROJECT_ID> <EMAIL> <REGION> <ZONE>"
   echo "   eg:  ./create_project.sh wks cmoulliard@redhat.com"
   exit
fi

# FNR value should be changed if you have several accounts"
ACCOUNT_ID=$(gcloud alpha billing accounts list | awk 'FNR == 2 {print $1}')
PROJECT_PREFIX=${1:-project}
EMAIL=${2:-cmoulliard@redhat.com}
REGION=${3:-europe-west1}
ZONE=${4:-europe-west1-b}
SERVICEACCOUNT="my-sa-1"

PROJECT_ID=$(echo "${PROJECT_PREFIX}-${EMAIL}" | sed 's/@/-/g' | sed 's/\./-/g' | cut -c 1-30)

echo "Creating project $PROJECT_ID ... "
gcloud projects create $PROJECT_ID
sleep 2

echo ">>> Make this project the default"
gcloud config set project $PROJECT_ID

echo ">>> Enable Billing for the project"
gcloud alpha billing accounts projects link $PROJECT_ID --account-id=$ACCOUNT_ID

echo ">>> Enable Services"
gcloud service-management enable cloudbilling.googleapis.com
gcloud service-management enable cloudapis.googleapis.com
gcloud service-management enable dns.googleapis.com
gcloud service-management enable compute-component.googleapis.com

echo ">>> Change default location"
gcloud compute project-info add-metadata --metadata google-compute-default-region=$REGION,google-compute-default-zone=$ZONE

echo ">>> Add role owner to the user"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$EMAIL" --role="roles/owner"

echo ">>> Add a Service Account"
gcloud iam service-accounts create $SERVICEACCOUNT --display-name "my-wks-service-account"
gcloud iam service-accounts keys create $PROJECT_ID.json --iam-account $SERVICEACCOUNT@$PROJECT_ID.iam.gserviceaccount.com

echo ">>> Give role owner to the serviceaccount and bind it to the project"
gcloud iam service-accounts add-iam-policy-binding $SERVICEACCOUNT@$PROJECT_ID.iam.gserviceaccount.com --role="roles/owner" --member="user:$EMAIL"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICEACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/owner"
