#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests of the project. Each function related to the workers individual tools
are tested in this suite. There is no communication.
"""

import mock
from mock import Mock
import unittest

from ADSDeploy import app
from ADSDeploy.tests import test_base
from ADSDeploy.models import Base, KeyValue
from ADSDeploy.pipeline.deploy import Deploy, BeforeDeploy, AfterDeploy
from ADSDeploy.pipeline.workers import IntegrationTestWorker
from collections import OrderedDict, namedtuple
import time


class TestIntegrationWorker(unittest.TestCase):
    """
    Unit tests for the test integration worker
    """

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        app.close_app()


    @mock.patch('ADSDeploy.pipeline.integration_tester.open')
    @mock.patch('ADSDeploy.pipeline.integration_tester.os.path.isdir')
    @mock.patch('ADSDeploy.pipeline.integration_tester.ChangeDirectory')
    @mock.patch('ADSDeploy.pipeline.integration_tester.shutil.rmtree')
    @mock.patch('ADSDeploy.pipeline.integration_tester.subprocess')
    @mock.patch('ADSDeploy.pipeline.integration_tester.git.Repo.clone_from')
    @mock.patch('ADSDeploy.pipeline.integration_tester.IntegrationTestWorker.publish')
    def test_worker_running_test(self, mocked_publish, mocked_clone, mocked_subprocess, mocked_rmtree, mocked_cd, mocked_isdir, mocked_open):
        """
        Test that the integration worker follows the expected workflow:
        """

        # Mock responses
        # 1. File object
        file_instance = mocked_open.return_value
        file_instance.__enter__.return_value = file_instance
        file_instance.__exit__.return_value = None

        # 2. Change Directory
        instance_cd = mocked_cd.return_value
        instance_cd.__enter__.return_value = instance_cd
        instance_cd.__exit__.return_value = None

        # 3. Subprocess
        process = mock.Mock()
        process.communicate.return_value = '10 passed', ''
        mocked_subprocess.Popen.return_value = process

        # 4. Others
        mocked_isdir.return_value = True
        mocked_publish.return_value = None
        mocked_clone.return_value = None

        example_payload = {
            'application': 'staging',
            'service': 'adsws',
            'release': 'v1.0.0',
            'config': {},
            'action': 'test'
        }

        worker = IntegrationTestWorker()
        result = worker.run_test(example_payload)

        # The worker downloads the repository that contains the integration
        # tests
        mocked_clone.assert_has_calls(
            [mock.call('https://github.com/adsabs/adsrex.git', '/tmp/adsrex', branch='develop')]
        )

        # Test that the local config gets produced
        mocked_open.assert_has_calls(
            [mock.call('/tmp/adsrex/v1/local_config.py', 'w')]
        )

        # The worker changes into the directory and runs the tests using
        # a bash script
        mocked_subprocess.Popen.assert_has_calls(
            [mock.call(['py.test'], stdin=mocked_subprocess.PIPE, stdout=mocked_subprocess.PIPE)]
        )

        # The test repository should also no longer exist
        mocked_rmtree.assert_has_calls(
            [mock.call('/tmp/adsrex')]
        )

        # The test passes and it forwards a packet on to the relevant worker,
        # with the updated keyword for test pass
        example_payload['test passed'] = True
        self.assertEqual(
            example_payload,
            result
        )

    @mock.patch('ADSDeploy.pipeline.integration_tester.open')
    @mock.patch('ADSDeploy.pipeline.integration_tester.os.path.isdir')
    @mock.patch('ADSDeploy.pipeline.integration_tester.ChangeDirectory')
    @mock.patch('ADSDeploy.pipeline.integration_tester.shutil.rmtree')
    @mock.patch('ADSDeploy.pipeline.integration_tester.subprocess')
    @mock.patch('ADSDeploy.pipeline.integration_tester.git.Repo.clone_from')
    @mock.patch('ADSDeploy.pipeline.integration_tester.IntegrationTestWorker.publish')
    def test_subprocess_raises_error(self, mocked_publish, mocked_clone, mocked_subprocess, mocked_rmtree, mocked_cd, mocked_isdir, mocked_open):
        """
        Test that nothing breaks if subprocess fails
        """

        # Mock responses
        # 1. File object
        file_instance = mocked_open.return_value
        file_instance.__enter__.return_value = file_instance
        file_instance.__exit__.return_value = None

        # 2. Change Directory
        instance_cd = mocked_cd.return_value
        instance_cd.__enter__.return_value = instance_cd
        instance_cd.__exit__.return_value = None

        # 3. Subprocess
        mocked_subprocess.Popen.side_effect = ValueError('ValueError')

        # 4. Others
        mocked_isdir.return_value = True
        mocked_publish.return_value = None
        mocked_clone.return_value = None

        example_payload = {
            'application': 'staging',
            'service': 'adsws',
            'release': 'v1.0.0',
            'config': {},
            'action': 'test'
        }

        worker = IntegrationTestWorker()
        result = worker.run_test(example_payload.copy())

        # The worker downloads the repository that contains the integration
        # tests
        mocked_clone.assert_has_calls(
            [mock.call('https://github.com/adsabs/adsrex.git', '/tmp/adsrex', branch='develop')]
        )

        # Test that the local config gets produced
        mocked_open.assert_has_calls(
            [mock.call('/tmp/adsrex/v1/local_config.py', 'w')]
        )

        # The worker changes into the directory and runs the tests using
        # a bash script
        mocked_subprocess.Popen.assert_has_calls(
            [mock.call(['py.test'], stdin=mocked_subprocess.PIPE, stdout=mocked_subprocess.PIPE)]
        )

        # The test repository should also no longer exist
        mocked_rmtree.assert_has_calls(
            [mock.call('/tmp/adsrex')]
        )

        # The test passes and it forwards a packet on to the relevant worker,
        # with the updated keyword for test pass
        example_payload['test passed'] = False

        self.assertEqual(
            example_payload,
            result
        )

    @mock.patch('ADSDeploy.pipeline.integration_tester.open')
    @mock.patch('ADSDeploy.pipeline.integration_tester.os.path.isdir')
    @mock.patch('ADSDeploy.pipeline.integration_tester.ChangeDirectory')
    @mock.patch('ADSDeploy.pipeline.integration_tester.shutil.rmtree')
    @mock.patch('ADSDeploy.pipeline.integration_tester.subprocess')
    @mock.patch('ADSDeploy.pipeline.integration_tester.git.Repo.clone_from')
    @mock.patch('ADSDeploy.pipeline.integration_tester.IntegrationTestWorker.publish')
    def test_git_raises_error(self, mocked_publish, mocked_clone, mocked_subprocess, mocked_rmtree, mocked_cd, mocked_isdir, mocked_open):
        """
        Test that nothing breaks if git pull fails
        """

        # Mock responses
        # 1. File object
        file_instance = mocked_open.return_value
        file_instance.__enter__.return_value = file_instance
        file_instance.__exit__.return_value = None

        # 2. Change Directory
        instance_cd = mocked_cd.return_value
        instance_cd.__enter__.return_value = instance_cd
        instance_cd.__exit__.return_value = None

        # 3. Subprocess
        process = mock.Mock()
        process.communicate.return_value = '10 passed', ''
        mocked_subprocess.Popen.return_value = process

        # 4. Others
        mocked_isdir.return_value = True
        mocked_publish.return_value = None
        mocked_clone.side_effect = ValueError('ValueError')

        example_payload = {
            'application': 'staging',
            'service': 'adsws',
            'release': 'v1.0.0',
            'config': {},
            'action': 'test'
        }

        worker = IntegrationTestWorker()
        result = worker.run_test(example_payload.copy())

        # The worker downloads the repository that contains the integration
        # tests
        mocked_clone.assert_has_calls(
            [mock.call('https://github.com/adsabs/adsrex.git', '/tmp/adsrex', branch='develop')]
        )

        # Test that the local config does not get produced
        self.assertFalse(mocked_open.called)

        # Subprocess should not be called
        self.assertFalse(mocked_subprocess.called)

        # Regardless, rmtree should still be called to cleanup any folders
        mocked_rmtree.assert_has_calls(
            [mock.call('/tmp/adsrex')]
        )

        # The test passes and it forwards a packet on to the relevant worker,
        # with the updated keyword for test pass
        example_payload['test passed'] = False

        self.assertEqual(
            example_payload,
            result
        )

    def test_make_local_config(self):
        """
        Test that making the local config looks like it is expected to
        """
        input_dictionary = OrderedDict([
            ('first_value', 1),
            ('first_word', 'word one'),
            ('second_value', 2.0),
            ('second_word', 'word two')
        ])
        expected_text = 'first_value = 1\nfirst_word = \'word one\'\n' \
                        'second_value = 2.0\nsecond_word = \'word two\''

        actual_text = IntegrationTestWorker.make_local_config(input_dictionary)

        self.assertEqual(expected_text, actual_text)


class TestWorkers(test_base.TestUnit):
    """
    Tests the GenericWorker's methods
    """

    def tearDown(self):
        test_base.TestUnit.tearDown(self)
        Base.metadata.drop_all()
        app.close_app()

    def create_app(self):
        app.init_app({
            'SQLALCHEMY_URL': 'sqlite:///',
            'SQLALCHEMY_ECHO': False,
            'AFTER_DEPLOY_CLEANUP_TIME': 1
        })
        with app.session_scope() as session:
            Base.metadata.bind = session.get_bind()
            Base.metadata.create_all()
        return app

    @mock.patch('ADSDeploy.pipeline.deploy.BeforeDeploy.publish')
    @mock.patch('ADSDeploy.osutils.Executioner.cmd', 
                return_value=Mock(**dict(retcode=0, 
                                         out='Ready adsws-sandbox.elasticbeanstalk.com adsws:v1.0.0:v1.0.2-17-g1b31375 Green adsws-sandbox')))
    def test_deploy_before_deploy(self, PatchedBeforeDeploy, exect):
        """Checks the worker has access to the AWS"""
        worker = BeforeDeploy()
        worker.process_payload({'application': 'sandbox', 'environment': 'adsws'})
        worker.publish.assert_called_with({'environment': 'adsws', 'application': 'sandbox', 'msg': 'OK to deploy'})

    def test_deploy_after_deploy(self):
        worker = AfterDeploy()
        worker.process_payload({'application': 'sandbox', 'environment': 'adsws'})
        with app.session_scope() as sess:
            u = sess.query(KeyValue).first()
            assert u.toJSON()['key'] == u'sandbox.adsws.last-used'
            assert float(u.toJSON()['value']) < time.time() + 1
            assert float(u.toJSON()['value']) > time.time() - 1

if __name__ == '__main__':
    unittest.main()
