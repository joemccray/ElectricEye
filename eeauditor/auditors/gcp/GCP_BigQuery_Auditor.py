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
from check_register import CheckRegister
import googleapiclient.discovery
import base64
import json

registry = CheckRegister()

def get_bigquery_tables(cache: dict, gcpProjectId, gcpCredentials) -> list[dict] | dict:
    """Retrieves the extended metadata of every table for every BigQuery dataset in the Project and returns them"""
    response = cache.get("get_bigquery_tables")
    if response:
        return response
    
    tableDetails: list[dict] = []
    
    service = googleapiclient.discovery.build('bigquery', 'v2', credentials=gcpCredentials)

    datasets = service.datasets().list(projectId=gcpProjectId).execute()

    if datasets["datasets"]:
        for dataset in datasets["datasets"]:
            datasetId = dataset["datasetReference"]["datasetId"]
            # now get the tables, we have to execute an additional GET per table to get the full metadata
            tables = service.tables().list(projectId=gcpProjectId, datasetId=datasetId).execute()
            for table in tables["tables"]:
                tableId = table["tableReference"]["tableId"]
                tableDetails.append(
                    service.tables().get(projectId=gcpProjectId, datasetId=datasetId, tableId=tableId).execute()
                )

    if tableDetails:
        cache["get_bigquery_tables"] = tableDetails
        return cache["get_bigquery_tables"]
    else:
        return {}
    
@registry.register_check("gcp.bigquery")
def bigquery_table_updated_within_90_days_check(cache: dict, awsAccountId, awsRegion, awsPartition, gcpProjectId, gcpCredentials):
    """[GCP.BigQuery.1] BigQuery Tables that have not been modified in 90 days should be reviewed"""
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.UTC).replace(tzinfo=datetime.timezone.utc).isoformat()
    # Loop the datasets
    for table in get_bigquery_tables(cache, gcpProjectId, gcpCredentials):
        fullTableId = table["id"]
        tableId = table["tableReference"]["tableId"]
        assetJson = json.dumps(table,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        modifyCheckFail = False
        lastModifiedEpoch = int(table.get("lastModifiedTime", 0))
        if lastModifiedEpoch == 0:
            modifyCheckFail = True
        else:
            # convert epochmillis and use timedelta to check if older than 90 days
            lastModified = datetime.datetime.fromtimestamp(lastModifiedEpoch / 1000.0, tz=datetime.timezone.utc)
            if datetime.datetime.now(datetime.timezone.utc) - lastModified > datetime.timedelta(days=90):
                modifyCheckFail = True

        # this is a failing check
        if modifyCheckFail:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{fullTableId}/bigquery-table-not-modified-in-90-days-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{fullTableId}/bigquery-table-not-modified-in-90-days-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[GCP.BigQuery.1] BigQuery Tables that have not been modified in 90 days should be reviewed",
                "Description": f"BigQuery table {tableId} has not been modified in 90 days. This may be an unused resource that can be deleted, especially if there is not any business use case to keeping the table operational. Review you internal policies and usage logs, as well as potentially sensitive or critical information, to make the determination if the table should be deleted. Refer to the remediation instructions if keeping the table is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "For more information on BigQuery best practices for backing up tables refer to the Backup & Disaster Recovery strategies for BigQuery entry in the Google Cloud blog.",
                        "Url": "https://cloud.google.com/blog/topics/developers-practitioners/backup-disaster-recovery-strategies-bigquery"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "GCP",
                    "ProviderType": "CSP",
                    "ProviderAccountId": gcpProjectId,
                    "AssetRegion": table["location"],
                    "AssetDetails": assetB64,
                    "AssetClass": "Analytics",
                    "AssetService": "Google Cloud BigQuery",
                    "AssetComponent": "Table"
                },
                "Resources": [
                    {
                        "Type": "GcpBigQueryTable",
                        "Id": fullTableId,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "ProjectId": gcpProjectId,
                                "TableId": table["tableReference"]["tableId"],
                                "DatasetId": table["tableReference"]["datasetId"],
                                "LastModifiedTime": lastModified
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-2",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 PM-5",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.1.1",
                        "ISO 27001:2013 A.8.1.2",
                        "ISO 27001:2013 A.12.5.1"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        # this is a passing check
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{fullTableId}/bigquery-table-not-modified-in-90-days-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{fullTableId}/bigquery-table-not-modified-in-90-days-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[GCP.BigQuery.1] BigQuery Tables that have not been modified in 90 days should be reviewed",
                "Description": f"BigQuery table {tableId} has been modified within the last 90 days. Periodically review your BigQuery tables to ensure they are still needed and that the data is still relevant. Refer to the remediation instructions if keeping the table is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "For more information on BigQuery best practices for backing up tables refer to the Backup & Disaster Recovery strategies for BigQuery entry in the Google Cloud blog.",
                        "Url": "https://cloud.google.com/blog/topics/developers-practitioners/backup-disaster-recovery-strategies-bigquery"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "GCP",
                    "ProviderType": "CSP",
                    "ProviderAccountId": gcpProjectId,
                    "AssetRegion": table["location"],
                    "AssetDetails": assetB64,
                    "AssetClass": "Analytics",
                    "AssetService": "Google Cloud BigQuery",
                    "AssetComponent": "Table"
                },
                "Resources": [
                    {
                        "Type": "GcpBigQueryTable",
                        "Id": fullTableId,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "ProjectId": gcpProjectId,
                                "TableId": table["tableReference"]["tableId"],
                                "DatasetId": table["tableReference"]["datasetId"],
                                "LastModifiedTime": lastModified
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-2",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 PM-5",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.1.1",
                        "ISO 27001:2013 A.8.1.2",
                        "ISO 27001:2013 A.12.5.1"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("gcp.bigquery")
def bigquery_table_custom_cmek_check(cache: dict, awsAccountId, awsRegion, awsPartition, gcpProjectId, gcpCredentials):
    """[GCP.BigQuery.2] BigQuery Tables should be encrypted with a customer-managed encryption key (CMEK)"""
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.UTC).replace(tzinfo=datetime.timezone.utc).isoformat()
    # Loop the datasets
    for table in get_bigquery_tables(cache, gcpProjectId, gcpCredentials):
        fullTableId = table["id"]
        tableId = table["tableReference"]["tableId"]
        assetJson = json.dumps(table,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        # this is a failing check
        if table.get("encryptionConfiguration", {}).get("kmsKeyName", "") == "":
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{fullTableId}/bigquery-table-custom-cmek-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{fullTableId}/bigquery-table-custom-cmek-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "LOW"},
                "Confidence": 99,
                "Title": "[GCP.BigQuery.2] BigQuery Tables should be encrypted with a customer-managed encryption key (CMEK)",
                "Description": f"BigQuery table {tableId} is not encrypted with a customer-managed encryption key (CMEK). By default, BigQuery encrypts all data before it is written to disk, and decrypts it when read by an authorized user. This process is transparent to users. However, you can choose to use your own encryption keys instead of the default Google-managed keys. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "For more information on CMEK refer to the Customer-managed encryption keys for BigQuery entry in the Google Cloud documentation.",
                        "Url": "https://cloud.google.com/bigquery/docs/customer-managed-encryption"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "GCP",
                    "ProviderType": "CSP",
                    "ProviderAccountId": gcpProjectId,
                    "AssetRegion": table["location"],
                    "AssetDetails": assetB64,
                    "AssetClass": "Analytics",
                    "AssetService": "Google Cloud BigQuery",
                    "AssetComponent": "Table"
                },
                "Resources": [
                    {
                        "Type": "GcpBigQueryTable",
                        "Id": fullTableId,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "ProjectId": gcpProjectId,
                                "TableId": table["tableReference"]["tableId"],
                                "DatasetId": table["tableReference"]["datasetId"]
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        # this is a passing check
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{fullTableId}/bigquery-table-custom-cmek-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{fullTableId}/bigquery-table-custom-cmek-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[GCP.BigQuery.2] BigQuery Tables should be encrypted with a customer-managed encryption key (CMEK)",
                "Description": f"BigQuery table {tableId} is encrypted with a customer-managed encryption key (CMEK). By default, BigQuery encrypts all data before it is written to disk, and decrypts it when read by an authorized user. This process is transparent to users. However, you can choose to use your own encryption keys instead of the default Google-managed keys. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "For more information on CMEK refer to the Customer-managed encryption keys for BigQuery entry in the Google Cloud documentation.",
                        "Url": "https://cloud.google.com/bigquery/docs/customer-managed-encryption"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "GCP",
                    "ProviderType": "CSP",
                    "ProviderAccountId": gcpProjectId,
                    "AssetRegion": table["location"],
                    "AssetDetails": assetB64,
                    "AssetClass": "Analytics",
                    "AssetService": "Google Cloud BigQuery",
                    "AssetComponent": "Table"
                },
                "Resources": [
                    {
                        "Type": "GcpBigQueryTable",
                        "Id": fullTableId,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "ProjectId": gcpProjectId,
                                "TableId": table["tableReference"]["tableId"],
                                "DatasetId": table["tableReference"]["datasetId"]
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

# end