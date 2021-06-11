"""
This (integration) test is supposed to test CRUD enpoints in the carbon-api.
"""
import os
import sys
from datetime import datetime
import unittest
from fastapi.testclient import TestClient
from jose import jwt
from uuid import uuid4

# fix import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


# Setup runtime environment
# TODO: should use the dotenv library in the future
os.environ['AUTH_ENDPOINT'] = "http://example.com"
os.environ['SECRET'] = "hire_me"
os.environ['MONGO_PORT'] = '27017'
os.environ['MONGO_HOST'] = "localhost"
SECRET = os.getenv('SECRET')


# Load & prepare SUT
from api.api import app
from api.models import UsageResponseModel
client = TestClient(app)


def _get_auth_token() -> dict:
    """ Generate an auth token for a user
    This token shold be accepted by the api.
    It technically mocks the auth system.
    """
    payload = {
        "user_id": f"testuser_{str(uuid4())}",
        "aud": "fastapi-users:auth",
        "exp": int(datetime.now().timestamp())+3600
    }
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    print("valid token for testing is:", token)
    return token


class TestCrudCase(unittest.TestCase):
    """Test CRUD operations - against the test database"""
    # TODO: Mock the database - I decided that this is
    # out of scope for this challenge. In a production env, mongomock
    # is a good candidate to also eliminate this dependency.

    def setUp(self) -> None:
        """each test gets a new auth token for a NEW user.
        this means that if you want to test a sequence,
        you have to do in in one test case."""
        _token = _get_auth_token()
        self.auth_header = {"Authorization": f"Bearer {_token}"}
        return super().setUp()

    def test_create_usage_unauthorized(self):
        """assert failing due to lack of authorization"""
        response = client.post(
            "/usages",
            json={
                "amount": 1312,
                "usage_type_id": 100
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_create_usage_authorized(self):

        response = client.post(
            "/usages",
            headers=self.auth_header,
            json={
                "amount": 1312,
                "usage_type_id": 100
            },
        )

        # something got created? :)
        self.assertEqual(response.status_code, 201)

        # test if we meet the expectations from pydantic.
        response_model = UsageResponseModel.parse_obj(response.json())
        self.assertIsInstance(response_model, UsageResponseModel)

    def test_modify_usage(self):
        # 1. create some usage first.
        response = client.post(
            "/usages",
            headers=self.auth_header,
            json={
                "amount": 1312,
                "usage_type_id": 100
            }
        )
        self.assertEqual(response.status_code, 201)
        resource_id = response.json().get('_id')

        # 2. patch new resource: change usage type
        patch_res = client.put(
            f'/usages/{resource_id}',
            headers=self.auth_header,
            json={
                "usage_type_id": 101
            }
        )
        self.assertEqual(patch_res.status_code, 200)
        # should be ResponseModel
        response_model = UsageResponseModel.parse_obj(patch_res.json())
        self.assertIsInstance(response_model, UsageResponseModel)

        # should contain new usage_type:
        self.assertEqual(response_model.usage_type.id, 101)

    def test_delete_usage(self):
        # 1. create some usage first.
        response = client.post(
            "/usages",
            headers=self.auth_header,
            json={
                "amount": 1312,
                "usage_type_id": 100
            }
        )
        self.assertEqual(response.status_code, 201)
        resource_id = response.json().get('_id')

        # 2. delete this resource now
        del_res = client.delete(
            f'/usages/{resource_id}',
            headers=self.auth_header,
            json={}
        )
        self.assertEqual(del_res.status_code, 200)

        # 3. check if resource is really gone
        get_res = client.get(
            f'/usages/{resource_id}',
            headers=self.auth_header
        )
        self.assertEqual(get_res.status_code, 404)

    def test_list_all_for_user(self):
        # 1. Create a few resources
        for i in range(5):
            client.post(
                "/usages",
                headers=self.auth_header,
                json={
                    "amount": 41+i,
                    "usage_type_id": 100+i
                }
            )

        # 2. Get them all
        get_res = client.get(
            '/usages',
            headers=self.auth_header
        )
        # amount of resources should match created
        self.assertEqual(len(get_res.json()), 5)


    def test_get_foreign_access(self):
        """One of the most damaging vulns on REST API these days is 
        Broken Object Level Authorization - or short BOLA
        https://owasp.org/www-project-api-security/
        This tests is checking for BOLA.
        """
        # 0. create mallory-user
        mallory_token = _get_auth_token()

        # 1. Alice creates usage
        response = client.post(
            "/usages",
            headers=self.auth_header,
            json={
                "amount": 1312,
                "usage_type_id": 100
            }
        )
        self.assertEqual(response.status_code, 201)
        alice_resource_id = response.json().get('_id')

        # 2. Mallory tries to access Alices usage
        get_res = client.get(
            f'/usages/{alice_resource_id}',
            headers={"Authorization": f"Bearer {mallory_token}"}
        )
        # If we did it right, Mallory should not be able to access
        # Alice resouce
        self.assertEqual(get_res.status_code, 404)


if __name__ == "__main__":
    TestCrudCase.run()
