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

    def create(self, template, name, node):

        chore = copy.deepcopy(template)
        chore.update({
            "name": name,
            "node": node
        })

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

    def test_template_load(self):

        self.assertEqual(service.template_load(), [
            {
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
            },
            {
                "text": "clean your room",
                "language": "en-au",
                "tasks": [
                    {
                        "text": "put your blankets and pillows on the bed",
                        "interval": 60
                    },
                    {
                        "text": "put your dirty clothes in the hamper",
                        "interval": 60
                    },
                    {
                        "text": "put away your books",
                        "interval": 60
                    },
                    {
                        "text": "put away your toys",
                        "interval": 60
                    },
                    {
                        "text": "throw away the trash",
                        "interval": 60
                    },
                    {
                        "text": "sweep the floor",
                        "interval": 120
                    },
                    {
                        "text": "make the bed",
                        "interval": 60
                    }
                ]
            },
            {
                "text": "get ready for bed",
                "language": "en-au",
                "tasks": [
                    {
                        "text": "put on pajamas",
                        "interval": 60
                    },
                    {
                        "text": "brush your teeth",
                        "interval": 60
                    },
                    {
                        "text": "read a story",
                        "interval": 300
                    },
                    {
                        "text": "get in bed",
                        "interval": 15
                    }
                ]
            }
        ])

    def test_template_find(self):

        self.assertEqual(service.template_find("get ready for school"), {
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

    def test_chore_create(self):

        response = self.api.post("/chore", json={
            "template": "get ready for school",
            "name": "dude",
            "node": "bump"
        })

        self.assertEqual(response.json, {
            "chore": {
                "name": "dude",
                "node": "bump",
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
        })
        self.assertEqual(response.status_code, 201)

        self.assertEqual(self.apx.chore_redis.chores, {
            "bump":  {
                "name": "dude",
                "node": "bump",
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
        })

    def test_chore_list(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.get("/chore")

        self.assertEqual(response.json, {
            "chores": [{
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }]
        })
        self.assertEqual(response.status_code, 200)

    def test_chore_retrieve(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.get("/chore/bump")

        self.assertEqual(response.json, {
            "chore": {
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        })
        self.assertEqual(response.status_code, 200)

    def test_chore_next(self):

        self.apx.chore_redis.chores = {
            "bump":  {
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.post("/chore/bump/next")

        self.assertEqual(response.json, {
            "changed": True,
            "chore": {
                "name": "dude",
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
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.post("/chore/bump/task/1/complete")

        self.assertEqual(response.json, {
            "changed": True,
            "chore": {
                "name": "dude",
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
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        }

        response = self.api.post("/chore/bump/task/1/incomplete")

        self.assertEqual(response.json, {
            "changed": True,
            "chore": {
                "name": "dude",
                "node": "bump",
                "text": "get ready for school"
            }
        })
        self.assertEqual(response.status_code, 202)

        self.assertEqual(self.apx.chore_redis.changed, {
            "incomplete": ("bump", 1)
        })
