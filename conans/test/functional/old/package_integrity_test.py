import os
import unittest

from conans.model.ref import ConanFileReference, PackageReference
from conans.test.utils.tools import TestClient, TestServer, \
    NO_SETTINGS_PACKAGE_ID, GenConanfile
from conans.util.files import set_dirty


class PackageIngrityTest(unittest.TestCase):

    def remove_locks_test(self):
        client = TestClient()
        client.save({"conanfile.py": GenConanfile().with_name("Hello").with_version("0.1")})
        client.run("create . lasote/testing")
        self.assertNotIn('does not contain a number!', client.out)
        ref = ConanFileReference.loads("Hello/0.1@lasote/testing")
        conan_folder = client.cache.package_layout(ref).base_folder()
        self.assertIn("locks", os.listdir(conan_folder))
        self.assertTrue(os.path.exists(conan_folder + ".count"))
        self.assertTrue(os.path.exists(conan_folder + ".count.lock"))
        client.run("remove * --locks", assert_error=True)
        self.assertIn("ERROR: Specifying a pattern is not supported", client.out)
        client.run("remove", assert_error=True)
        self.assertIn('ERROR: Please specify a pattern to be removed ("*" for all)', client.out)
        client.run("remove --locks")
        self.assertNotIn("locks", os.listdir(conan_folder))
        self.assertFalse(os.path.exists(conan_folder + ".count"))
        self.assertFalse(os.path.exists(conan_folder + ".count.lock"))

    def upload_dirty_test(self):
        test_server = TestServer([], users={"lasote": "mypass"})
        client = TestClient(servers={"default": test_server},
                            users={"default": [("lasote", "mypass")]})
        client.save({"conanfile.py": GenConanfile().with_name("Hello").with_version("0.1")})
        client.run("create . lasote/testing")
        ref = ConanFileReference.loads("Hello/0.1@lasote/testing")
        pref = PackageReference(ref, NO_SETTINGS_PACKAGE_ID)
        package_folder = client.cache.package_layout(pref.ref).package(pref)
        set_dirty(package_folder)

        client.run("upload * --all --confirm", assert_error=True)
        self.assertIn("ERROR: Hello/0.1@lasote/testing:5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9: "
                      "Upload package to 'default' failed: Package %s is corrupted, aborting upload"
                      % str(pref), client.out)
        self.assertIn("Remove it with 'conan remove Hello/0.1@lasote/testing -p=%s'"
                      % NO_SETTINGS_PACKAGE_ID, client.out)

        client.run("remove Hello/0.1@lasote/testing -p=%s -f" % NO_SETTINGS_PACKAGE_ID)
        client.run("upload * --all --confirm")
