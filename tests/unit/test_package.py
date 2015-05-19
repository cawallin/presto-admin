from fabric.state import env
from mock import patch
from prestoadmin import package
from prestoadmin.util import constants
from tests import utils


class TestPackage(utils.BaseTestCase):

    @patch('prestoadmin.package.sudo')
    @patch('prestoadmin.package.put')
    def test_deploy_is_called(self, mock_put, mock_sudo):
        env.host = "any_host"
        package.deploy("/any/path/rpm")
        mock_sudo.assert_called_with("mkdir -p " +
                                     constants.REMOTE_PACKAGES_PATH)
        mock_put.assert_called_with("/any/path/rpm",
                                    constants.REMOTE_PACKAGES_PATH,
                                    use_sudo=True)

    @patch('prestoadmin.package.sudo')
    def test_rpm_install(self, mock_sudo):
        env.host = "any_host"
        env.nodeps = False
        package.rpm_install("test.rpm")
        mock_sudo.assert_called_with("rpm -i "
                                     "/opt/prestoadmin/packages/test.rpm")

    @patch('prestoadmin.package.sudo')
    def test_rpm_install_nodeps(self, mock_sudo):
        env.host = "any_host"
        env.nodeps = True
        package.rpm_install("test.rpm")
        mock_sudo.assert_called_with("rpm -i --nodeps "
                                     "/opt/prestoadmin/packages/test.rpm")

    @patch('prestoadmin.package.rpm_install')
    @patch('prestoadmin.package.deploy')
    @patch('prestoadmin.package.check_if_valid_rpm')
    def test_install(self, mock_chksum, mock_deploy, mock_install):
        env.host = "any_host"
        self.remove_runs_once_flag(package.install)
        package.install("/any/path/rpm")
        mock_chksum.assert_called_with("/any/path/rpm")
        mock_deploy.assert_called_with("/any/path/rpm")
        mock_install.assert_called_with("rpm")

    @patch('prestoadmin.package.local')
    @patch('prestoadmin.package.abort')
    def test_check_rpm_checksum(self, mock_abort, mock_local):
        mock_local.return_value = lambda: None
        setattr(mock_local.return_value, 'stderr', '')
        setattr(mock_local.return_value, 'stdout', 'sha1 MD5 NOT OK')
        package.check_if_valid_rpm("/any/path/rpm")

        mock_local.assert_called_with("rpm -K --nosignature /any/path/rpm",
                                      capture=True)
        mock_abort.assert_called_with("Corrupted RPM. "
                                      "Try downloading the RPM again.")

    @patch('prestoadmin.package.local')
    @patch('prestoadmin.package.abort')
    def test_check_rpm_checksum_err(self, mock_abort, mock_local):
        mock_local.return_value = lambda: None
        setattr(mock_local.return_value, 'stderr', 'Not an rpm package')
        setattr(mock_local.return_value, 'stdout', '')
        package.check_if_valid_rpm("/any/path/rpm")

        mock_local.assert_called_with("rpm -K --nosignature /any/path/rpm",
                                      capture=True)
        mock_abort.assert_called_with('Not an rpm package')

    @patch('prestoadmin.package.sudo')
    @patch('prestoadmin.package.put')
    def test_deploy_with_fallback_location(self, mock_put, mock_sudo):
        env.host = "any_host"
        package.deploy("/any/path/rpm")
        mock_put.return_value = lambda: None
        setattr(mock_put.return_value, 'succeeded', False)
        package.deploy("/any/path/rpm")
        mock_put.assert_called_with("/any/path/rpm",
                                    constants.REMOTE_PACKAGES_PATH,
                                    use_sudo=True,
                                    temp_dir='/tmp')