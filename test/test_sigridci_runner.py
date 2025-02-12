# Copyright Software Improvement Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile
import types
import unittest
import urllib
from sigridci.sigridci import SigridApiClient, SigridCiRunner, UploadOptions, TargetQuality, LOG_HISTORY

class SigridCiRunnerTest(unittest.TestCase):

    def setUp(self):
        os.environ["SIGRID_CI_ACCOUNT"] = "dummy"
        os.environ["SIGRID_CI_TOKEN"] = "dummy"
        LOG_HISTORY.clear()
        
    def testForceLowerCaseForCustomerAndSystemName(self):
        args = types.SimpleNamespace(partner="sig", customer="Aap", system="NOOT", sigridurl="", publish=False, publishonly=False)
        apiClient = SigridApiClient(args)
        
        self.assertEqual(apiClient.urlCustomerName, "aap")
        self.assertEqual(apiClient.urlSystemName, "noot")
        
    def testValidateSystemNameAccordingToRules(self):
        runner = SigridCiRunner()
    
        self.assertTrue(runner.isValidSystemName("noot", "aap"))
        self.assertTrue(runner.isValidSystemName("noot", "aap-noot"))
        self.assertTrue(runner.isValidSystemName("noot", "aap123"))
        self.assertTrue(runner.isValidSystemName("noot", "AAP"))
        self.assertTrue(runner.isValidSystemName("noot", "a" * 59))

        self.assertFalse(runner.isValidSystemName("noot", "aap_noot"))
        self.assertFalse(runner.isValidSystemName("noot", "a"))
        self.assertFalse(runner.isValidSystemName("noot", "$$$"))
        self.assertFalse(runner.isValidSystemName("noot", "-aap"))
        self.assertFalse(runner.isValidSystemName("noot", "a" * 65))
        self.assertFalse(runner.isValidSystemName("noot", "aap--aap"))
        
    def testSystemNameIsConvertedToLowerCaseInApiClient(self):
        args = types.SimpleNamespace(partner="sig", customer="Aap", system="NOOT", \
            sigridurl="example.com", publish=False, publishonly=False)
        apiClient = SigridApiClient(args)
        
        self.assertEqual(apiClient.urlCustomerName, "aap")
        self.assertEqual(apiClient.urlSystemName, "noot")

    def testRegularRun(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "a.py", "print(123)")
        
        options = UploadOptions(sourceDir=tempDir)
        target = TargetQuality("/tmp/nonexistent", 3.5)
        apiClient = MockApiClient(publish=False)
        
        runner = SigridCiRunner()
        runner.run(apiClient, options, target, [])

        expectedLog = [
            "Found system in Sigrid",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Submitting upload",
            "Upload successful",
            "Waiting for analysis results"
        ]
        
        expectedCalls = [
            "/analysis-results/sigridci/aap/noot/v1/ci", 
            "/inboundresults/sig/aap/noot/ci/uploads/v1", 
            "UPLOAD",
            "/analysis-results/sigridci/aap/noot/v1/ci/results/123",
            "/analysis-results/api/v1/system-metadata/aap/noot"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
        self.assertEqual(apiClient.called, expectedCalls)
        
    def testPublishRun(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "a.py", "print(123)")
        
        options = UploadOptions(sourceDir=tempDir, publishOnly=False)
        target = TargetQuality("/tmp/nonexistent", 3.5)
        apiClient = MockApiClient(publish=True)
        
        runner = SigridCiRunner()
        runner.run(apiClient, options, target, [])

        expectedLog = [
            "Found system in Sigrid",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Publishing upload",
            "Upload successful",
            "Waiting for analysis results"
        ]
        
        expectedCalls = [
            "/analysis-results/sigridci/aap/noot/v1/ci", 
            "/inboundresults/sig/aap/noot/ci/uploads/v1/publish", 
            "UPLOAD",
            "/analysis-results/sigridci/aap/noot/v1/ci/results/123",
            "/analysis-results/api/v1/system-metadata/aap/noot"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
        self.assertEqual(apiClient.called, expectedCalls)
        
    def testPublishOnlyRun(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "a.py", "print(123)")
        
        options = UploadOptions(sourceDir=tempDir, publishOnly=True)
        target = TargetQuality("/tmp/nonexistent", 3.5)
        apiClient = MockApiClient(publish=True)
        
        runner = SigridCiRunner()
        runner.run(apiClient, options, target, [])

        expectedLog = [
            "Found system in Sigrid",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Publishing upload",
            "Upload successful",
            "Your project's source code has been published to Sigrid"
        ]
        
        expectedCalls = [
            "/analysis-results/sigridci/aap/noot/v1/ci", 
            "/inboundresults/sig/aap/noot/ci/uploads/v1/publish",             
            "UPLOAD",
            "/analysis-results/api/v1/system-metadata/aap/noot"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
        self.assertEqual(apiClient.called, expectedCalls)
        
    def testOnBoardingRun(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "a.py", "print(123)")
        
        options = UploadOptions(sourceDir=tempDir)
        target = TargetQuality("/tmp/nonexistent", 3.5)
        apiClient = MockApiClient(systemExists=False)
        
        runner = SigridCiRunner()
        runner.run(apiClient, options, target, [])

        expectedLog = [
            "System is not yet on-boarded to Sigrid",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Submitting upload",
            "Upload successful",
            "System 'noot' is on-boarded to Sigrid, and will appear in sigrid-says.com shortly"
        ]
        
        expectedCalls = [
            "/analysis-results/sigridci/aap/noot/v1/ci", 
            "/inboundresults/sig/aap/noot/ci/uploads/v1/onboarding", 
            "UPLOAD"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
        self.assertEqual(apiClient.called, expectedCalls)
        
    def testExitWithMessageIfUploadEmpty(self):
        tempDir = tempfile.mkdtemp()    
        options = UploadOptions(sourceDir=tempDir)
        target = TargetQuality("/tmp/nonexistent", 3.5)
        apiClient = MockApiClient(systemExists=False)
        
        runner = SigridCiRunner()
        with self.assertRaises(SystemExit):
            runner.run(apiClient, options, target, [])
            
    def testRetryIfUploadFailsTheFirstTime(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "a.py", "print(123)")
        
        options = UploadOptions(sourceDir=tempDir)
        target = TargetQuality("/tmp/nonexistent", 3.5)
        apiClient = MockApiClient(systemExists=True, uploadAttempts=3)
        
        runner = SigridCiRunner()
        runner.run(apiClient, options, target, [])

        expectedLog = [
            "Found system in Sigrid",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Submitting upload",
            "Retrying",
            "Retrying",
            "Upload successful",
            "Waiting for analysis results"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
    
    def testExitIfUploadKeepsFailing(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "a.py", "print(123)")
        
        options = UploadOptions(sourceDir=tempDir)
        target = TargetQuality("/tmp/nonexistent", 3.5)
        apiClient = MockApiClient(systemExists=True, uploadAttempts=99)
        runner = SigridCiRunner()
        
        expectedLog = [
            "Found system in Sigrid",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Submitting upload",
            "Retrying",
            "Retrying",
            "Retrying",
            "Retrying",
            "Retrying",
            "Sigrid is currently unavailable, failed after 5 attempts"
        ]
        
        with self.assertRaises(SystemExit):
            runner.run(apiClient, options, target, [])
        self.assertEqual(LOG_HISTORY, expectedLog)
        
    def testReadScopeFileWhenInRepository(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "sigrid.yaml", "component_depth: 1")
        uploadOptions = UploadOptions(sourceDir=tempDir)
        
        self.assertEquals(uploadOptions.readScopeFile(), "component_depth: 1")
        
    def testScopeFileIsNoneWhenNotInRepository(self):
        tempDir = tempfile.mkdtemp()    
        uploadOptions = UploadOptions(sourceDir=tempDir)
        
        self.assertIsNone(uploadOptions.readScopeFile())
        
    def testValidateScopeFile(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "sigrid.yaml", "languages:\n- java")
        uploadOptions = UploadOptions(sourceDir=tempDir)
        
        apiClient = MockApiClient(publish=False)
        apiClient.responses["/inboundresults/sig/aap/noot/ci/validate/v1"] = {"valid": True};
        
        runner = SigridCiRunner()
        runner.run(apiClient, uploadOptions, None, [])
        
        expectedLog = [
            "Found system in Sigrid",
            "Validating scope configuration file",
            "Validation passed",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Submitting upload",
            "Upload successful",
            "Waiting for analysis results"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
    
    def testFailIfScopeFileIsNotValid(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "sigrid.yaml", "languages:\n- aap")
        uploadOptions = UploadOptions(sourceDir=tempDir)
        
        apiClient = MockApiClient(publish=False)
        apiClient.responses["/inboundresults/sig/aap/noot/ci/validate/v1"] = {"valid" : False, "notes" : ["test"]};
    
        with self.assertRaises(SystemExit):
            runner = SigridCiRunner()
            runner.run(apiClient, uploadOptions, None, [])
            
        expectedLog = [
            "Found system in Sigrid",
            "Validating scope configuration file",
            "--------------------------------------------------------------------------------",
            "Invalid scope configuration file:",
            "    - test",
            "--------------------------------------------------------------------------------"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
        
    def testDumpAvailableMetadataToOutput(self):
        tempDir = tempfile.mkdtemp()    
        self.createTempFile(tempDir, "sigrid.py", "print(123)")
        uploadOptions = UploadOptions(sourceDir=tempDir)
    
        apiClient = MockApiClient(publish=False)
        apiClient.responses["/analysis-results/api/v1/system-metadata/aap/noot"] = {"aap" : 2, "noot" : None};
        
        runner = SigridCiRunner()
        runner.run(apiClient, uploadOptions, None, [])
        
        expectedLog = [
            "Found system in Sigrid",
            "Creating upload", 
            "Upload size is 1 MB",
            "Warning: Upload is very small, source directory might not contain all source code",
            "Preparing upload", 
            "Sigrid CI analysis ID: 123",
            "Submitting upload",
            "Upload successful",
            "Waiting for analysis results"
        ]

        self.assertEqual(LOG_HISTORY, expectedLog)
        
    def createTempFile(self, dir, name, contents):
        with open(f"{dir}/{name}", "w") as fileRef:
            fileRef.write(contents)
        return f"{dir}/{name}"
        
        
class MockApiClient(SigridApiClient):
    def __init__(self, publish=False, systemExists=True, uploadAttempts=0):
        self.called = []
        self.urlPartnerName = "sig"
        self.urlCustomerName = "aap"
        self.urlSystemName = "noot"
        self.publish = publish
        self.systemExists = systemExists
        self.uploadAttempts = uploadAttempts
        self.attempt = 0
        self.responses = {}
        self.POLL_INTERVAL = 1

    def callSigridAPI(self, path, body=None, contentType=None):
        self.called.append(path)
    
        if not self.systemExists and path.endswith("/sigridci/aap/noot/v1/ci"):
            # Mock a HTTP 404.
            raise urllib.error.HTTPError(path, 404, "", {}, None)
        
        defaultResponse = {"ciRunId" : "123", "uploadUrl" : "dummy"}
        return self.responses.get(path, defaultResponse)
        
    def attemptUpload(self, url, upload):
        self.attempt += 1
        if self.attempt >= self.uploadAttempts:            
            self.called.append("UPLOAD")
            return True
        else:
            raise urllib.error.HTTPError("/upload", 500, "", {}, None)
     