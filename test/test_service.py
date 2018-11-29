import unittest
import unittest.mock

import os
import copy
import json

import service

class MockChoreRedis(object):

    def __init__(self, host, port, channel):

        self.host = host
        self.port = port
        self.channel = channel

        self.chores = {}
        self.changed = {}

    def get(self, node):

        if node in self.chores:
            return self.chores[node]

        return None

    def create(self, template, person, node):

        chore = copy.deepcopy(template)
        chore.update({
            "id": node,
            "person": person,
            "node": node
        })

        for index, task in enumerate(chore["tasks"]):
            task["id"] = index

        self.chores[node] = chore

        return chore

    def list(self):

        return list(self.chores.values())

    def next(self, chore):

        self.changed["next"] = chore["node"]
        return True

    def complete(self, chore, index):

        self.changed["complete"] = (chore["node"], index)
        return True

    def incomplete(self, chore, index):

        self.changed["incomplete"] = (chore["node"], index)
        return True

class TestService(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch.dict(os.environ, {
        "REDIS_HOST": "data.com",
        "REDIS_PORT": "667",
        "REDIS_CHANNEL": "stuff"
    })
    @unittest.mock.patch("pi_k8s_fitches.chore_redis.ChoreRedis", MockChoreRedis)
    def setUp(self):

        self.apx = service.api()
        self.api = self.apx.app.test_client()

    def test_health(self):

        self.assertEqual(self.api.get("/health").json, {"message": "OK"})

    def test_setting_load(self):

        self.assertEqual(service.setting_load(), {
            "node": [
                "pi-k8s-timmy",
                "pi-k8s-sally"
            ],
            "person": [
                "Timmy",
                "Sally"
            ],
            "language": [
                "en"
            ]
        })

    def test_template_load(self):

        self.assertEqual(service.template_load(), [
            {
                "id": 0,
                "text": "get ready for school",
                "language": "en-au",
                "tasks": [
                    {
                        "text": "get out of bed",
                        "interval": 15
                    },
                    {
                        "text": "get dressed",
                        "interval": 60
                    },
                    {
                        "text": "brush your teeth",
                        "interval": 60
                    },
                    {
                        "text": "put on your boots, coat, and hat",
                        "interval": 60
                    }
                ]
            }
        ])

    def test_template_find(self):

        self.assertEqual(service.template_find(0), {
            "id": 0,
            "text": "get ready for school",
            "language": "en-au",
            "tasks": [
                {
                    "text": "get out of bed",
                    "interval": 15
                },
                {
                    "text": "get dressed",
                    "interval": 60
                },
                {
                    "text": "brush your teeth",
                    "interval": 60
                },
                {
                    "text": "put on your boots, coat, and hat",
                    "interval": 60
                }
            ]
        })

        self.assertIsNone(service.template_find("watch tv"))

    def test_setting_list(self):

        response = self.api.get("/setting")

        self.assertEqual(response.json, {
            "settings": {
                "node": [
                    "pi-k8s-timmy",
                    "pi-k8s-sally"
                ],
                "person": [
                    "Timmy",
                    "Sally"
                ],
                "language": [
                    "en"
                ]
            }
        })
        self.assertEqual(response.status_code, 200)

    def test_template_list(self):

        response = self.api.get("/template")

        self.assertEqual(response.json, {
            "templates": [{
                "id": 0,
                "text": "get ready for school",
                "language": "en-au",
                "tasks": [
                    {
                        "text": "get out of bed",
                        "interval": 15
                    },
                    {
                        "text": "get dressed",
                        "interval": 60
                    },
                    {
                        "text": "brush your teeth",
                        "interval": 60
                    },
                    {
                        "text": "put on your boots, coat, and hat",
                        "interval": 60
                    }
                ]
            }]
        })
        self.assertEqual(response.status_code, 200)

    def test_chore_create(self):

        response = self.api.post("/chore", json={
            "template": 0,
            "person": "dude",
            "node": "bump"
        })

        self.assertEqual(response.json, {
            "chore": {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school",
                "language": "en-au",
                "tasks": [
                    {
                        "id": 0,
                        "text": "get out of bed",
                        "interval": 15
                    },
                    {
                        "id": 1,
                        "text": "get dressed",
                        "interval": 60
                    },
                    {
                        "id": 2,
                        "text": "brush your teeth",
                        "interval": 60
                    },
                    {
                        "id": 3,
                        "text": "put on your boots, coat, and hat",
                        "interval": 60
                    }
                ]
            }
        })
        self.assertEqual(response.status_code, 201)

        self.assertEqual(self.apx.chore_redis.chores, {
            "bump":  {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school",
                "language": "en-au",
                "tasks": [
                    {
                        "id": 0,
                        "text": "get out of bed",
                        "interval": 15
                    },
                    {
                        "id": 1,
                        "text": "get dressed",
                        "interval": 60
                    },
                    {
                        "id": 2,
                        "text": "brush your teeth",
                        "interval": 60
                    },
                    {
                        "id": 3,
                        "text": "put on your boots, coat, and hat",
                        "interval": 60
                    }
                ]
            }
        })

    def test_chore_list(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.get("/chore")

        self.assertEqual(response.json, {
            "chores": [{
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }]
        })
        self.assertEqual(response.status_code, 200)

    def test_chore_retrieve(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.get("/chore/bump")

        self.assertEqual(response.json, {
            "chore": {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        })
        self.assertEqual(response.status_code, 200)

    def test_chore_next(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.post("/chore/bump/next")

        self.assertEqual(response.json, {
            "changed": True,
            "chore": {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        })
        self.assertEqual(response.status_code, 202)

        self.assertEqual(self.apx.chore_redis.changed, {
            "next": "bump"
        })

    def test_chore_complete(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.post("/chore/bump/task/1/complete")

        self.assertEqual(response.json, {
            "changed": True,
            "chore": {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        })
        self.assertEqual(response.status_code, 202)

        self.assertEqual(self.apx.chore_redis.changed, {
            "complete": ("bump", 1)
        })

    def test_chore_incomplete(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.post("/chore/bump/task/1/incomplete")

        self.assertEqual(response.json, {
            "changed": True,
            "chore": {
                "id": "bump",
                "person": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        })
        self.assertEqual(response.status_code, 202)

        self.assertEqual(self.apx.chore_redis.changed, {
            "incomplete": ("bump", 1)
        })
