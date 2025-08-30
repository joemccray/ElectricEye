#This file is part of ElectricEye.
#SPDX-License-Identifier: Apache-2.0

#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at

#http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.

import datetime
import botocore
from check_register import CheckRegister
import base64
import json

registry = CheckRegister()

# loop through ECR repos
def describe_repositories(cache, session):
    response = cache.get("describe_repositories")
    if response:
        return response
    
    ecr = session.client("ecr")

    cache["describe_repositories"] = ecr.describe_repositories(maxResults=1000)["repositories"]
    return cache["describe_repositories"]

@registry.register_check("ecr")
def ecr_repo_vuln_scan_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[ECR.1] ECR repositories should be scanned for vulnerabilities by either Amazon Inspector V2 or Amazon ECR built-in scanning"""
    inspector = session.client("inspector2")
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for repo in describe_repositories(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(repo,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        repoArn = repo["repositoryArn"]
        repoName = repo["repositoryName"]

        # Determine if a Repository is scanned by checking both for Basic (ECR built-in) and Enhanced (Inspector V2) scanning
        # built-in
        if not repo["imageScanningConfiguration"]["scanOnPush"]:
            basicScan = False
        else:
            basicScan = True
        # inspector
        coverage = inspector.list_coverage(
            filterCriteria={
                "ecrRepositoryName": [
                    {
                        "comparison": "EQUALS",
                        "value": repoName
                    }
                ]
            }
        )["coveredResources"]
        if not coverage:
            enhancedScan = False
        else:
            if coverage[0]["scanStatus"]["statusCode"] == "ACTIVE":
                enhancedScan = True
            else:
                enhancedScan = False

        # If neither scanning is active, this is a failing check
        if basicScan is False and enhancedScan is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": repoArn + "/ecr-no-scan",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": repoArn,
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[ECR.1] ECR repositories should be scanned for vulnerabilities by either Amazon Inspector V2 or Amazon ECR built-in scanning",
                "Description": f"ECR repository {repoName} is not configured to be scanned for vulnerabilities by either Amazon Inspector V2 or Amazon ECR built-in scanning. Amazon ECR image scanning helps in identifying software vulnerabilities in your container images. The following scanning types are offered. With Enhanced scanning Amazon ECR integrates with Amazon Inspector to provide automated, continuous scanning of your repositories and your container images are scanned for both operating systems and programing language package vulnerabilities. With Basic scanning Amazon ECR uses the Common Vulnerabilities and Exposures (CVEs) database from the open-source Clair project. With basic scanning, you configure your repositories to scan on push or you can perform manual scans and Amazon ECR provides a list of scan findings. Refer to the remediation instructions if this configuration is not intended",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your repository should be configured to scan on push refer to the Image Scanning section in the Amazon ECR User Guide",
                        "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html",
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Containers",
                    "AssetService": "Amazon Elastic Container Registry",
                    "AssetComponent": "Repository"
                },
                "Resources": [
                    {
                        "Type": "AwsEcrRepository",
                        "Id": repoArn,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {"Other": {"RepositoryName": repoName}},
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 DE.CM-8",
                        "NIST CSF V1.1 ID.RA-1",
                        "NIST SP 800-53 Rev. 4 CA-2",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-8",
                        "NIST SP 800-53 Rev. 4 RA-3",
                        "NIST SP 800-53 Rev. 4 RA-5",
                        "NIST SP 800-53 Rev. 4 SA-5",
                        "NIST SP 800-53 Rev. 4 SA-11",
                        "NIST SP 800-53 Rev. 4 SI-2",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "NIST SP 800-53 Rev. 4 SI-5",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC7.1",
                        "ISO 27001:2013 A.12.6.1",
                        "ISO 27001:2013 A.12.6.4",
                        "ISO 27001:2013 A.18.2.3"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE",
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": repoArn + "/ecr-no-scan",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": repoArn,
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[ECR.1] ECR repositories should be scanned for vulnerabilities by either Amazon Inspector V2 or Amazon ECR built-in scanning",
                "Description": f"ECR repository {repoName} is configured to be scanned for vulnerabilities by either Amazon Inspector V2 or Amazon ECR built-in scanning.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your repository should be configured to scan on push refer to the Image Scanning section in the Amazon ECR User Guide",
                        "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html",
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Containers",
                    "AssetService": "Amazon Elastic Container Registry",
                    "AssetComponent": "Repository"
                },
                "Resources": [
                    {
                        "Type": "AwsEcrRepository",
                        "Id": repoArn,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {"Other": {"RepositoryName": repoName}},
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 DE.CM-8",
                        "NIST CSF V1.1 ID.RA-1",
                        "NIST SP 800-53 Rev. 4 CA-2",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-8",
                        "NIST SP 800-53 Rev. 4 RA-3",
                        "NIST SP 800-53 Rev. 4 RA-5",
                        "NIST SP 800-53 Rev. 4 SA-5",
                        "NIST SP 800-53 Rev. 4 SA-11",
                        "NIST SP 800-53 Rev. 4 SI-2",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "NIST SP 800-53 Rev. 4 SI-5",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC7.1",
                        "ISO 27001:2013 A.12.6.1",
                        "ISO 27001:2013 A.12.6.4",
                        "ISO 27001:2013 A.18.2.3"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED",
            }
            yield finding

@registry.register_check("ecr")
def ecr_repo_image_lifecycle_policy_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[ECR.2] ECR repositories should be have an image lifecycle policy configured"""
    ecr = session.client("ecr")
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for repo in describe_repositories(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(repo,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        repoArn = repo["repositoryArn"]
        repoName = repo["repositoryName"]
        
        # Evaluate if a lifecycle policy is configured
        lifecyclePolicy = True
        try:
            ecr.get_lifecycle_policy(repositoryName=repoName)
        except botocore.exceptions.ClientError:
            lifecyclePolicy = False

        # this is a passing check
        if lifecyclePolicy is True:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": repoArn + "/ecr-lifecycle-policy-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": repoArn,
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[ECR.2] ECR repositories should be have an image lifecycle policy configured",
                "Description": f"ECR repository {repoName} does have an image lifecycle policy configured.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your repository should be configured to have an image lifecycle policy refer to the Amazon ECR Lifecycle Policies section in the Amazon ECR User Guide",
                        "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html",
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Containers",
                    "AssetService": "Amazon Elastic Container Registry",
                    "AssetComponent": "Repository"
                },
                "Resources": [
                    {
                        "Type": "AwsEcrRepository",
                        "Id": repoArn,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {"Other": {"RepositoryName": repoName}},
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.BE-5",
                        "NIST CSF V1.1 PR.DS-4",
                        "NIST CSF V1.1 PR.PT-5",
                        "NIST SP 800-53 Rev. 4 AU-4",
                        "NIST SP 800-53 Rev. 4 CP-2",
                        "NIST SP 800-53 Rev. 4 CP-7",
                        "NIST SP 800-53 Rev. 4 CP-8",
                        "NIST SP 800-53 Rev. 4 CP-11",
                        "NIST SP 800-53 Rev. 4 CP-13",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SA-14",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-6",
                        "AICPA TSC CC3.1",
                        "AICPA TSC A1.1",
                        "AICPA TSC A1.2",
                        "ISO 27001:2013 A.11.1.4",
                        "ISO 27001:2013 A.12.3.1",
                        "ISO 27001:2013 A.17.1.1",
                        "ISO 27001:2013 A.17.1.2",
                        "ISO 27001:2013 A.17.2.1"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED",
            }
            yield finding
        # this is a failing check
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": repoArn + "/ecr-lifecycle-policy-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": repoArn,
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[ECR.2] ECR repositories should be have an image lifecycle policy configured",
                "Description": f"ECR repository {repoName} does not have an image lifecycle policy configured. Amazon ECR lifecycle policies provide more control over the lifecycle management of images in a private repository. A lifecycle policy contains one or more rules, where each rule defines an action for Amazon ECR. This provides a way to automate the cleaning up of your container images by expiring images based on age or count. You should expect that images become expired within 24 hours after they meet the expiration criteria per your lifecycle policy. When Amazon ECR performs an action based on a lifecycle policy, this is captured as an event in AWS CloudTrail. When considering the use of lifecycle policies, it's important to use the lifecycle policy preview to confirm which images the lifecycle policy expires before applying it to a repository. Using Lifecycle Policies can help to reduce security exposure by forcefully removing stale images and promoting good image hygeine by having processes to continually scan and rebuild container images. Refer to the remediation instructions if this configuration is not intended",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your repository should be configured to have an image lifecycle policy refer to the Amazon ECR Lifecycle Policies section in the Amazon ECR User Guide",
                        "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html",
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Containers",
                    "AssetService": "Amazon Elastic Container Registry",
                    "AssetComponent": "Repository"
                },
                "Resources": [
                    {
                        "Type": "AwsEcrRepository",
                        "Id": repoArn,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {"Other": {"RepositoryName": repoName}},
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.BE-5",
                        "NIST CSF V1.1 PR.DS-4",
                        "NIST CSF V1.1 PR.PT-5",
                        "NIST SP 800-53 Rev. 4 AU-4",
                        "NIST SP 800-53 Rev. 4 CP-2",
                        "NIST SP 800-53 Rev. 4 CP-7",
                        "NIST SP 800-53 Rev. 4 CP-8",
                        "NIST SP 800-53 Rev. 4 CP-11",
                        "NIST SP 800-53 Rev. 4 CP-13",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SA-14",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-6",
                        "AICPA TSC CC3.1",
                        "AICPA TSC A1.1",
                        "AICPA TSC A1.2",
                        "ISO 27001:2013 A.11.1.4",
                        "ISO 27001:2013 A.12.3.1",
                        "ISO 27001:2013 A.17.1.1",
                        "ISO 27001:2013 A.17.1.2",
                        "ISO 27001:2013 A.17.2.1"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE",
            }
            yield finding

@registry.register_check("ecr")
def ecr_repo_permission_policy_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[ECR.3] ECR repositories should be have a repository policy configured"""
    ecr = session.client("ecr")
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for repo in describe_repositories(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(repo,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        repoArn = repo["repositoryArn"]
        repoName = repo["repositoryName"]

        # Evaluate if there is a repository permission policy configured
        repoPermissionPolicy = True
        try:
            ecr.get_repository_policy(repositoryName=repoName)
        except botocore.exceptions.ClientError:
            repoPermissionPolicy = False
        
        # this is a passing finding
        if repoPermissionPolicy is True:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": repoArn + "/ecr-repo-access-policy-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": repoArn,
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[ECR.3] ECR repositories should be have a repository policy configured",
                "Description": "ECR repository "
                + repoName
                + " has a repository policy configured.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your repository should be configured to have a repository policy refer to the Amazon ECR Repository Policies section in the Amazon ECR User Guide",
                        "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-policies.html",
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Containers",
                    "AssetService": "Amazon Elastic Container Registry",
                    "AssetComponent": "Repository"
                },
                "Resources": [
                    {
                        "Type": "AwsEcrRepository",
                        "Id": repoArn,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {"Other": {"RepositoryName": repoName}},
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.AC-3",
                        "NIST CSF V1.1 PR.AC-4",
                        "NIST CSF V1.1 PR.DS-5",
                        "NIST SP 800-53 Rev. 4 AC-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-3",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AC-5",
                        "NIST SP 800-53 Rev. 4 AC-6",
                        "NIST SP 800-53 Rev. 4 AC-14",
                        "NIST SP 800-53 Rev. 4 AC-16",
                        "NIST SP 800-53 Rev. 4 AC-17",
                        "NIST SP 800-53 Rev. 4 AC-19",
                        "NIST SP 800-53 Rev. 4 AC-20",
                        "NIST SP 800-53 Rev. 4 AC-24",
                        "NIST SP 800-53 Rev. 4 PE-19",
                        "NIST SP 800-53 Rev. 4 PS-3",
                        "NIST SP 800-53 Rev. 4 PS-6",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SC-8",
                        "NIST SP 800-53 Rev. 4 SC-13",
                        "NIST SP 800-53 Rev. 4 SC-15",
                        "NIST SP 800-53 Rev. 4 SC-31",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC6.3",
                        "AICPA TSC CC6.6",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.6.1.2",
                        "ISO 27001:2013 A.6.2.1",
                        "ISO 27001:2013 A.6.2.2",
                        "ISO 27001:2013 A.7.1.1",
                        "ISO 27001:2013 A.7.1.2",
                        "ISO 27001:2013 A.7.3.1",
                        "ISO 27001:2013 A.8.2.2",
                        "ISO 27001:2013 A.8.2.3",
                        "ISO 27001:2013 A.9.1.1",
                        "ISO 27001:2013 A.9.1.2",
                        "ISO 27001:2013 A.9.2.3",
                        "ISO 27001:2013 A.9.4.1",
                        "ISO 27001:2013 A.9.4.4",
                        "ISO 27001:2013 A.9.4.5",
                        "ISO 27001:2013 A.10.1.1",
                        "ISO 27001:2013 A.11.1.4",
                        "ISO 27001:2013 A.11.1.5",
                        "ISO 27001:2013 A.11.2.1",
                        "ISO 27001:2013 A.11.2.6",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.1.3",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.3",
                        "ISO 27001:2013 A.13.2.4",
                        "ISO 27001:2013 A.14.1.2",
                        "ISO 27001:2013 A.14.1.3"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED",
            }
            yield finding
        # this is a failing finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": repoArn + "/ecr-repo-access-policy-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": repoArn,
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[ECR.3] ECR repositories should be have a repository policy configured",
                "Description": "ECR repository "
                + repoName
                + " does not have a repository policy configured. Refer to the remediation instructions if this configuration is not intended",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your repository should be configured to have a repository policy refer to the Amazon ECR Repository Policies section in the Amazon ECR User Guide",
                        "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-policies.html",
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Containers",
                    "AssetService": "Amazon Elastic Container Registry",
                    "AssetComponent": "Repository"
                },
                "Resources": [
                    {
                        "Type": "AwsEcrRepository",
                        "Id": repoArn,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {"Other": {"RepositoryName": repoName}},
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.AC-3",
                        "NIST CSF V1.1 PR.AC-4",
                        "NIST CSF V1.1 PR.DS-5",
                        "NIST SP 800-53 Rev. 4 AC-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-3",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AC-5",
                        "NIST SP 800-53 Rev. 4 AC-6",
                        "NIST SP 800-53 Rev. 4 AC-14",
                        "NIST SP 800-53 Rev. 4 AC-16",
                        "NIST SP 800-53 Rev. 4 AC-17",
                        "NIST SP 800-53 Rev. 4 AC-19",
                        "NIST SP 800-53 Rev. 4 AC-20",
                        "NIST SP 800-53 Rev. 4 AC-24",
                        "NIST SP 800-53 Rev. 4 PE-19",
                        "NIST SP 800-53 Rev. 4 PS-3",
                        "NIST SP 800-53 Rev. 4 PS-6",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SC-8",
                        "NIST SP 800-53 Rev. 4 SC-13",
                        "NIST SP 800-53 Rev. 4 SC-15",
                        "NIST SP 800-53 Rev. 4 SC-31",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC6.3",
                        "AICPA TSC CC6.6",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.6.1.2",
                        "ISO 27001:2013 A.6.2.1",
                        "ISO 27001:2013 A.6.2.2",
                        "ISO 27001:2013 A.7.1.1",
                        "ISO 27001:2013 A.7.1.2",
                        "ISO 27001:2013 A.7.3.1",
                        "ISO 27001:2013 A.8.2.2",
                        "ISO 27001:2013 A.8.2.3",
                        "ISO 27001:2013 A.9.1.1",
                        "ISO 27001:2013 A.9.1.2",
                        "ISO 27001:2013 A.9.2.3",
                        "ISO 27001:2013 A.9.4.1",
                        "ISO 27001:2013 A.9.4.4",
                        "ISO 27001:2013 A.9.4.5",
                        "ISO 27001:2013 A.10.1.1",
                        "ISO 27001:2013 A.11.1.4",
                        "ISO 27001:2013 A.11.1.5",
                        "ISO 27001:2013 A.11.2.1",
                        "ISO 27001:2013 A.11.2.6",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.1.3",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.3",
                        "ISO 27001:2013 A.13.2.4",
                        "ISO 27001:2013 A.14.1.2",
                        "ISO 27001:2013 A.14.1.3"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE",
            }
            yield finding

@registry.register_check("ecr")
def ecr_latest_image_vuln_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[ECR.4] The latest image in an ECR Repository should not have any vulnerabilities"""
    # ISO Time
    iso8601Time = (datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat())
    ecr = session.client("ecr")
    for repo in describe_repositories(cache, session):
        # B64 encode all of the details for the Asset
        repoName = repo["repositoryName"]
        if repo["imageScanningConfiguration"]["scanOnPush"] is True:
            for image in ecr.describe_images(repositoryName=repoName, filter={"tagStatus": "TAGGED"}, maxResults=1000)["imageDetails"]:
                assetJson = json.dumps(image,default=str).encode("utf-8")
                assetB64 = base64.b64encode(assetJson)
                imageDigest = image["imageDigest"]
                # use the first tag only as we need it to create the canonical ID for the Resource.Id in the ASFF for the Container Resource.Type
                imageTag = image["imageTags"][0]

                # Evaluate if there are any vulnerabilities
                imageHasVulns = False
                try:
                    imageVulnCheck = image["imageScanFindingsSummary"]["findingSeverityCounts"]
                    imageHasVulns = True
                except KeyError:
                    imageHasVulns = False

                # This is a failing check
                if imageHasVulns is True:
                    finding = {
                        "SchemaVersion": "2018-10-08",
                        "Id": f"arn:{awsPartition}:ecr:{awsRegion}:{awsAccountId}:image/{repoName}:{imageTag}/ecr-latest-image-vuln-check",
                        "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                        "GeneratorId": imageDigest,
                        "AwsAccountId": awsAccountId,
                        "Types": [
                            "Software and Configuration Checks/Vulnerabilities/CVE",
                            "Software and Configuration Checks/AWS Security Best Practices",
                        ],
                        "FirstObservedAt": iso8601Time,
                        "CreatedAt": iso8601Time,
                        "UpdatedAt": iso8601Time,
                        "Severity": {"Label": "MEDIUM"},
                        "Confidence": 99,
                        "Title": "[ECR.4] The latest image in an ECR Repository should not have any vulnerabilities",
                        "Description": f"The latest image {imageDigest} in the ECR repository {repoName} has {imageVulnCheck} vulnerabilities reported by ECR Basic Scans. The latest image is likely the last used or is likely active in your environment, while container vulnerabilities can be transient and harder to exploit, it is important for your security hygeine and threat reduction that active images are aggressively patched and minimized. Refer to the remediation instructions as well as your ECR Basic or Full (Inspector) scan results.",
                        "Remediation": {
                            "Recommendation": {
                                "Text": "For more information about scanning images refer to the Image Scanning section of the Amazon ECR User Guide",
                                "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html",
                            }
                        },
                        "ProductFields": {
                            "ProductName": "ElectricEye",
                            "Provider": "AWS",
                            "ProviderType": "CSP",
                            "ProviderAccountId": awsAccountId,
                            "AssetRegion": awsRegion,
                            "AssetDetails": assetB64,
                            "AssetClass": "Containers",
                            "AssetService": "Amazon Elastic Container Registry",
                            "AssetComponent": "Image"
                        },
                        "Resources": [
                            {
                                "Type": "Container",
                                "Id": f"arn:{awsPartition}:ecr:{awsRegion}:{awsAccountId}:image/{repoName}:{imageTag}",
                                "Partition": awsPartition,
                                "Region": awsRegion,
                                "Details": {
                                    "Container": {
                                        "Name": f"{repoName}:{imageTag}",
                                        "ImageId": imageDigest
                                    }
                                }
                            }
                        ],
                        "Compliance": {
                            "Status": "FAILED",
                            "RelatedRequirements": [
                                "NIST CSF V1.1 DE.CM-8",
                                "NIST CSF V1.1 ID.RA-1",
                                "NIST SP 800-53 Rev. 4 CA-2",
                                "NIST SP 800-53 Rev. 4 CA-7",
                                "NIST SP 800-53 Rev. 4 CA-8",
                                "NIST SP 800-53 Rev. 4 RA-3",
                                "NIST SP 800-53 Rev. 4 RA-5",
                                "NIST SP 800-53 Rev. 4 SA-5",
                                "NIST SP 800-53 Rev. 4 SA-11",
                                "NIST SP 800-53 Rev. 4 SI-2",
                                "NIST SP 800-53 Rev. 4 SI-4",
                                "NIST SP 800-53 Rev. 4 SI-5",
                                "AICPA TSC CC3.2",
                                "AICPA TSC CC7.1",
                                "ISO 27001:2013 A.12.6.1",
                                "ISO 27001:2013 A.12.6.4",
                                "ISO 27001:2013 A.18.2.3"
                            ]
                        },
                        "Workflow": {"Status": "NEW"},
                        "RecordState": "ACTIVE"
                    }
                    yield finding
                # This is a passing check
                else:
                    finding = {
                        "SchemaVersion": "2018-10-08",
                        "Id": f"arn:{awsPartition}:ecr:{awsRegion}:{awsAccountId}:image/{repoName}:{imageTag}/ecr-latest-image-vuln-check",
                        "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                        "GeneratorId": imageDigest,
                        "AwsAccountId": awsAccountId,
                        "Types": [
                            "Software and Configuration Checks/Vulnerabilities/CVE",
                            "Software and Configuration Checks/AWS Security Best Practices",
                        ],
                        "FirstObservedAt": iso8601Time,
                        "CreatedAt": iso8601Time,
                        "UpdatedAt": iso8601Time,
                        "Severity": {"Label": "INFORMATIONAL"},
                        "Confidence": 99,
                        "Title": "[ECR.4] The latest image in an ECR Repository should not have any vulnerabilities",
                        "Description": f"The latest image {imageDigest} in the ECR repository {repoName} does not have any vulnerabilities reported, good job!",
                        "Remediation": {
                            "Recommendation": {
                                "Text": "For more information about scanning images refer to the Image Scanning section of the Amazon ECR User Guide",
                                "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html",
                            }
                        },
                        "ProductFields": {
                            "ProductName": "ElectricEye",
                            "Provider": "AWS",
                            "ProviderType": "CSP",
                            "ProviderAccountId": awsAccountId,
                            "AssetRegion": awsRegion,
                            "AssetDetails": assetB64,
                            "AssetClass": "Containers",
                            "AssetService": "Amazon Elastic Container Registry",
                            "AssetComponent": "Image"
                        },
                        "Resources": [
                            {
                                "Type": "Container",
                                "Id": f"arn:{awsPartition}:ecr:{awsRegion}:{awsAccountId}:image/{repoName}:{imageTag}",
                                "Partition": awsPartition,
                                "Region": awsRegion,
                                "Details": {
                                    "Container": {
                                        "Name": f"{repoName}:{imageTag}",
                                        "ImageId": imageDigest
                                    }
                                }
                            }
                        ],
                        "Compliance": {
                            "Status": "PASSED",
                            "RelatedRequirements": [
                                "NIST CSF V1.1 DE.CM-8",
                                "NIST CSF V1.1 ID.RA-1",
                                "NIST SP 800-53 Rev. 4 CA-2",
                                "NIST SP 800-53 Rev. 4 CA-7",
                                "NIST SP 800-53 Rev. 4 CA-8",
                                "NIST SP 800-53 Rev. 4 RA-3",
                                "NIST SP 800-53 Rev. 4 RA-5",
                                "NIST SP 800-53 Rev. 4 SA-5",
                                "NIST SP 800-53 Rev. 4 SA-11",
                                "NIST SP 800-53 Rev. 4 SI-2",
                                "NIST SP 800-53 Rev. 4 SI-4",
                                "NIST SP 800-53 Rev. 4 SI-5",
                                "AICPA TSC CC3.2",
                                "AICPA TSC CC7.1",
                                "ISO 27001:2013 A.12.6.1",
                                "ISO 27001:2013 A.12.6.4",
                                "ISO 27001:2013 A.18.2.3"
                            ]
                        },
                        "Workflow": {"Status": "RESOLVED"},
                        "RecordState": "ARCHIVED"
                    }
                    yield finding

@registry.register_check("ecr")
def ecr_registry_policy_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[ECR.5] ECR Registires should be have a registry policy configured to allow for cross-account recovery"""
    ecr = session.client("ecr")
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    registryArn = f"arn:{awsPartition}:ecr:{awsRegion}:{awsAccountId}:registry"

    # determine if a registry policy is configured
    ecrRegistryPolicy = True
    try:
        policy = ecr.get_registry_policy()
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(policy,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
    except botocore.exceptions.ClientError:
        ecrRegistryPolicy = False
        assetB64 = None

    if ecrRegistryPolicy is True:
        # This is a passing check
        finding = {
            "SchemaVersion": "2018-10-08",
            "Id": f"{registryArn}/ecr-registry-access-policy-check",
            "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
            "GeneratorId": awsAccountId + awsRegion,
            "AwsAccountId": awsAccountId,
            "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
            "FirstObservedAt": iso8601Time,
            "CreatedAt": iso8601Time,
            "UpdatedAt": iso8601Time,
            "Severity": {"Label": "INFORMATIONAL"},
            "Confidence": 99,
            "Title": "[ECR.5] ECR Registires should be have a registry policy configured to allow for cross-account recovery",
            "Description": "ECR Registry "
            + awsAccountId
            + " in Region "
            + awsRegion
            + " has a registry policy configured.",
            "Remediation": {
                "Recommendation": {
                    "Text": "If your Registry should be configured to have a Registry policy refer to the Private registry permissions section in the Amazon ECR User Guide",
                    "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/registry-permissions.html"
                }
            },
            "ProductFields": {
                "ProductName": "ElectricEye",
                "Provider": "AWS",
                "ProviderType": "CSP",
                "ProviderAccountId": awsAccountId,
                "AssetRegion": awsRegion,
                "AssetDetails": assetB64,
                "AssetClass": "Containers",
                "AssetService": "Amazon Elastic Container Registry",
                "AssetComponent": "Registry"
            },
            "Resources": [
                {
                    "Type": "AwsEcrRegistry",
                    "Id": registryArn,
                    "Partition": awsPartition,
                    "Region": awsRegion,
                    "Details": {"Other": {"RegistryId": awsAccountId}},
                }
            ],
            "Compliance": {
                "Status": "PASSED",
                "RelatedRequirements": [
                    "NIST CSF V1.1 ID.BE-5",
                    "NIST CSF V1.1 PR.IP-4",
                    "NIST CSF V1.1 PR.PT-5",
                    "NIST SP 800-53 Rev. 4 CP-2",
                    "NIST SP 800-53 Rev. 4 CP-4",
                    "NIST SP 800-53 Rev. 4 CP-6",
                    "NIST SP 800-53 Rev. 4 CP-7",
                    "NIST SP 800-53 Rev. 4 CP-8",
                    "NIST SP 800-53 Rev. 4 CP-9",
                    "NIST SP 800-53 Rev. 4 CP-11",
                    "NIST SP 800-53 Rev. 4 CP-13",
                    "NIST SP 800-53 Rev. 4 PL-8",
                    "NIST SP 800-53 Rev. 4 SA-14",
                    "NIST SP 800-53 Rev. 4 SC-6",
                    "AICPA TSC A1.2",
                    "AICPA TSC A1.3",
                    "AICPA TSC CC3.1",
                    "ISO 27001:2013 A.11.1.4",
                    "ISO 27001:2013 A.12.3.1",
                    "ISO 27001:2013 A.17.1.1",
                    "ISO 27001:2013 A.17.1.2",
                    "ISO 27001:2013 A.17.1.3",
                    "ISO 27001:2013 A.17.2.1",
                    "ISO 27001:2013 A.18.1.3"
                ]
            },
            "Workflow": {"Status": "RESOLVED"},
            "RecordState": "ARCHIVED",
        }
        yield finding
    else:
        # this is a failing check
        finding = {
            "SchemaVersion": "2018-10-08",
            "Id": f"{registryArn}/ecr-registry-access-policy-check",
            "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
            "GeneratorId": awsAccountId + awsRegion,
            "AwsAccountId": awsAccountId,
            "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
            "FirstObservedAt": iso8601Time,
            "CreatedAt": iso8601Time,
            "UpdatedAt": iso8601Time,
            "Severity": {"Label": "LOW"},
            "Confidence": 99,
            "Title": "[ECR.5] ECR Registires should be have a registry policy configured to allow for cross-account recovery",
            "Description": "ECR Registry "
            + awsAccountId
            + " in Region "
            + awsRegion
            + " does not have a registry policy configured. ECR uses a registry policy to grant permissions to an AWS principal, allowing the replication of the repositories from a source registry to your registry. By default, you have permission to configure cross-Region replication within your own registry. You only need to configure the registry policy if you're granting another account permission to replicate contents to your registry. Refer to the remediation instructions if this configuration is not intended",
            "Remediation": {
                "Recommendation": {
                    "Text": "If your Registry should be configured to have a Registry policy refer to the Private registry permissions section in the Amazon ECR User Guide",
                    "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/registry-permissions.html"
                }
            },
            "ProductFields": {
                "ProductName": "ElectricEye",
                "Provider": "AWS",
                "ProviderType": "CSP",
                "ProviderAccountId": awsAccountId,
                "AssetRegion": awsRegion,
                "AssetDetails": assetB64,
                "AssetClass": "Containers",
                "AssetService": "Amazon Elastic Container Registry",
                "AssetComponent": "Registry"
            },
            "Resources": [
                {
                    "Type": "AwsEcrRegistry",
                    "Id": registryArn,
                    "Partition": awsPartition,
                    "Region": awsRegion,
                    "Details": {"Other": {"RegistryId": awsAccountId}},
                }
            ],
            "Compliance": {
                "Status": "FAILED",
                "RelatedRequirements": [
                    "NIST CSF V1.1 ID.BE-5",
                    "NIST CSF V1.1 PR.IP-4",
                    "NIST CSF V1.1 PR.PT-5",
                    "NIST SP 800-53 Rev. 4 CP-2",
                    "NIST SP 800-53 Rev. 4 CP-4",
                    "NIST SP 800-53 Rev. 4 CP-6",
                    "NIST SP 800-53 Rev. 4 CP-7",
                    "NIST SP 800-53 Rev. 4 CP-8",
                    "NIST SP 800-53 Rev. 4 CP-9",
                    "NIST SP 800-53 Rev. 4 CP-11",
                    "NIST SP 800-53 Rev. 4 CP-13",
                    "NIST SP 800-53 Rev. 4 PL-8",
                    "NIST SP 800-53 Rev. 4 SA-14",
                    "NIST SP 800-53 Rev. 4 SC-6",
                    "AICPA TSC A1.2",
                    "AICPA TSC A1.3",
                    "AICPA TSC CC3.1",
                    "ISO 27001:2013 A.11.1.4",
                    "ISO 27001:2013 A.12.3.1",
                    "ISO 27001:2013 A.17.1.1",
                    "ISO 27001:2013 A.17.1.2",
                    "ISO 27001:2013 A.17.1.3",
                    "ISO 27001:2013 A.17.2.1",
                    "ISO 27001:2013 A.18.1.3"
                ]
            },
            "Workflow": {"Status": "NEW"},
            "RecordState": "ACTIVE",
        }
        yield finding

@registry.register_check("ecr")
def ecr_registry_backup_rules_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[ECR.6] ECR Registires should use image replication to promote disaster recovery readiness"""
    ecr = session.client("ecr")
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    registryDetail = ecr.describe_registry()
    registryArn = f"arn:{awsPartition}:ecr:{awsRegion}:{awsAccountId}:registry"
    if not registryDetail["replicationConfiguration"]["rules"]:
        # B64 encode all of the details for the Asset
        assetB64 = None
        # This is a failing check
        finding = {
            "SchemaVersion": "2018-10-08",
            "Id": f"{registryArn}/ecr-registry-image-replication-check",
            "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
            "GeneratorId": awsAccountId + awsRegion,
            "AwsAccountId": awsAccountId,
            "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
            "FirstObservedAt": iso8601Time,
            "CreatedAt": iso8601Time,
            "UpdatedAt": iso8601Time,
            "Severity": {"Label": "LOW"},
            "Confidence": 99,
            "Title": "[ECR.6] ECR Registires should use image replication to promote disaster recovery readiness",
            "Description": "ECR Registry "
            + awsAccountId
            + " in Region "
            + awsRegion
            + " does not use Image replication. Registries can be configured to backup images to other Regions within your own Account or to other AWS Accounts to aid in disaster recovery readiness. Refer to the remediation instructions if this configuration is not intended",
            "Remediation": {
                "Recommendation": {
                    "Text": "If your Registry should be configured to for Private image replication refer to the Private image replication section in the Amazon ECR User Guide",
                    "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/replication.html"
                }
            },
            "ProductFields": {
                "ProductName": "ElectricEye",
                "Provider": "AWS",
                "ProviderType": "CSP",
                "ProviderAccountId": awsAccountId,
                "AssetRegion": awsRegion,
                "AssetDetails": assetB64,
                "AssetClass": "Containers",
                "AssetService": "Amazon Elastic Container Registry",
                "AssetComponent": "Registry"
            },
            "Resources": [
                {
                    "Type": "AwsEcrRegistry",
                    "Id": registryArn,
                    "Partition": awsPartition,
                    "Region": awsRegion,
                    "Details": {"Other": {"RegistryId": awsAccountId}},
                }
            ],
            "Compliance": {
                "Status": "FAILED",
                "RelatedRequirements": [
                    "NIST CSF V1.1 ID.BE-5",
                    "NIST CSF V1.1 PR.IP-4",
                    "NIST CSF V1.1 PR.PT-5",
                    "NIST SP 800-53 Rev. 4 CP-2",
                    "NIST SP 800-53 Rev. 4 CP-4",
                    "NIST SP 800-53 Rev. 4 CP-6",
                    "NIST SP 800-53 Rev. 4 CP-7",
                    "NIST SP 800-53 Rev. 4 CP-8",
                    "NIST SP 800-53 Rev. 4 CP-9",
                    "NIST SP 800-53 Rev. 4 CP-11",
                    "NIST SP 800-53 Rev. 4 CP-13",
                    "NIST SP 800-53 Rev. 4 PL-8",
                    "NIST SP 800-53 Rev. 4 SA-14",
                    "NIST SP 800-53 Rev. 4 SC-6",
                    "AICPA TSC A1.2",
                    "AICPA TSC A1.3",
                    "AICPA TSC CC3.1",
                    "ISO 27001:2013 A.11.1.4",
                    "ISO 27001:2013 A.12.3.1",
                    "ISO 27001:2013 A.17.1.1",
                    "ISO 27001:2013 A.17.1.2",
                    "ISO 27001:2013 A.17.1.3",
                    "ISO 27001:2013 A.17.2.1",
                    "ISO 27001:2013 A.18.1.3"
                ]
            },
            "Workflow": {"Status": "NEW"},
            "RecordState": "ACTIVE"
        }
        yield finding
    else:
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(registryDetail,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        finding = {
            "SchemaVersion": "2018-10-08",
            "Id": f"{registryArn}/ecr-registry-image-replication-check",
            "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
            "GeneratorId": awsAccountId,
            "AwsAccountId": awsAccountId,
            "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
            "FirstObservedAt": iso8601Time,
            "CreatedAt": iso8601Time,
            "UpdatedAt": iso8601Time,
            "Severity": {"Label": "INFORMATIONAL"},
            "Confidence": 99,
            "Title": "[ECR.6] ECR Registires should use image replication to promote disaster recovery readiness",
            "Description": "ECR Registry "
            + awsAccountId
            + " in Region "
            + awsRegion
            + " uses Image replication.",
            "Remediation": {
                "Recommendation": {
                    "Text": "If your Registry should be configured to for Private image replication refer to the Private image replication section in the Amazon ECR User Guide",
                    "Url": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/replication.html"
                }
            },
            "ProductFields": {
                "ProductName": "ElectricEye",
                "Provider": "AWS",
                "ProviderType": "CSP",
                "ProviderAccountId": awsAccountId,
                "AssetRegion": awsRegion,
                "AssetDetails": assetB64,
                "AssetClass": "Containers",
                "AssetService": "Amazon Elastic Container Registry",
                "AssetComponent": "Registry"
            },
            "Resources": [
                {
                    "Type": "AwsEcrRegistry",
                    "Id": registryArn,
                    "Partition": awsPartition,
                    "Region": awsRegion,
                    "Details": {"Other": {"RegistryId": awsAccountId}},
                }
            ],
            "Compliance": {
                "Status": "PASSED",
                "RelatedRequirements": [
                    "NIST CSF V1.1 ID.BE-5",
                    "NIST CSF V1.1 PR.IP-4",
                    "NIST CSF V1.1 PR.PT-5",
                    "NIST SP 800-53 Rev. 4 CP-2",
                    "NIST SP 800-53 Rev. 4 CP-4",
                    "NIST SP 800-53 Rev. 4 CP-6",
                    "NIST SP 800-53 Rev. 4 CP-7",
                    "NIST SP 800-53 Rev. 4 CP-8",
                    "NIST SP 800-53 Rev. 4 CP-9",
                    "NIST SP 800-53 Rev. 4 CP-11",
                    "NIST SP 800-53 Rev. 4 CP-13",
                    "NIST SP 800-53 Rev. 4 PL-8",
                    "NIST SP 800-53 Rev. 4 SA-14",
                    "NIST SP 800-53 Rev. 4 SC-6",
                    "AICPA TSC A1.2",
                    "AICPA TSC A1.3",
                    "AICPA TSC CC3.1",
                    "ISO 27001:2013 A.11.1.4",
                    "ISO 27001:2013 A.12.3.1",
                    "ISO 27001:2013 A.17.1.1",
                    "ISO 27001:2013 A.17.1.2",
                    "ISO 27001:2013 A.17.1.3",
                    "ISO 27001:2013 A.17.2.1",
                    "ISO 27001:2013 A.18.1.3"
                ]
            },
            "Workflow": {"Status": "RESOLVED"},
            "RecordState": "ARCHIVED"
        }
        yield finding

## EOF