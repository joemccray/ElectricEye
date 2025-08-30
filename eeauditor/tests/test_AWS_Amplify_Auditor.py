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
import pytest

from botocore.stub import Stubber

from auditors.aws.AWS_Amplify_Auditor import (amplify, 
    amplify_basic_auth_enabled_check, 
    amplify_branch_auto_deletion_enabled_check
)

list_apps_true_response = {
    'apps': [
        {
            'appId': 'AmplifyAppId',
            'appArn': 'AmplifyAppArn',
            'name': 'AmplifyAppName',
            'enableBasicAuth': True,
            'description': 'string',
            'repository': 'string',
            'platform': 'WEB',
            'createTime': '2015-01-01',
            'updateTime': '2015-01-01',
            'iamServiceRoleArn': 'string',
            'environmentVariables': {
                'string': 'string'
            },
            'defaultDomain': 'string',
            'enableBranchAutoBuild': True,
            'enableBranchAutoDeletion': True
        },
    ]
}

list_apps_false_response = {
    'apps': [
        {
            'appId': 'AmplifyAppId',
            'appArn': 'AmplifyAppArn',
            'name': 'AmplifyAppName',
            'enableBasicAuth': False,
            'description': 'string',
            'repository': 'string',
            'platform': 'WEB',
            'createTime': '2015-01-01',
            'updateTime': '2015-01-01',
            'iamServiceRoleArn': 'string',
            'environmentVariables': {
                'string': 'string'
            },
            'defaultDomain': 'string',
            'enableBranchAutoBuild': True,
            'enableBranchAutoDeletion': False
        },
    ]
}


@pytest.fixture(scope="function")
def amplify_stubber():
    amplify_stubber = Stubber(amplify)
    amplify_stubber.activate()
    yield amplify_stubber
    amplify_stubber.deactivate()


def test_basic_auth_true(amplify_stubber):
    amplify_stubber.add_response("list_apps", list_apps_true_response)
    results = amplify_basic_auth_enabled_check(
        cache={}, awsAccountId="012345678901", awsRegion="us-east-1", awsPartition="aws"
    )
    for result in results:
        assert result["RecordState"] == "ARCHIVED"
    amplify_stubber.assert_no_pending_responses()


def test_basic_auth_false(amplify_stubber):
    amplify_stubber.add_response("list_apps", list_apps_false_response)
    results = amplify_basic_auth_enabled_check(
        cache={}, awsAccountId="012345678901", awsRegion="us-east-1", awsPartition="aws"
    )
    for result in results:
        assert result["RecordState"] == "ACTIVE"
    amplify_stubber.assert_no_pending_responses()


def test_auto_delete_true(amplify_stubber):
    amplify_stubber.add_response("list_apps", list_apps_true_response)
    results = amplify_branch_auto_deletion_enabled_check(
        cache={}, awsAccountId="012345678901", awsRegion="us-east-1", awsPartition="aws"
    )
    for result in results:
        assert result["RecordState"] == "ACTIVE"
    amplify_stubber.assert_no_pending_responses()


def test_auto_delete_false(amplify_stubber):
    amplify_stubber.add_response("list_apps", list_apps_false_response)
    results = amplify_branch_auto_deletion_enabled_check(
        cache={}, awsAccountId="012345678901", awsRegion="us-east-1", awsPartition="aws"
    )
    for result in results:
        assert result["RecordState"] == "ARCHIVED"
    amplify_stubber.assert_no_pending_responses()