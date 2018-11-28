import os
import json
import connexion

import pi_k8s_fitches.chore_redis

apx = None

def api():

    import service

    service.apx = connexion.App("service", specification_dir='/opt/pi-k8s/openapi')
    service.apx.add_api('service.yaml')

    service.apx.chore_redis = pi_k8s_fitches.chore_redis.ChoreRedis(
        host=os.environ['REDIS_HOST'],
        port=int(os.environ['REDIS_PORT']),
        channel=os.environ['REDIS_CHANNEL']
    )

    return service.apx

def health():

    return {"message": "OK"}

def setting_load():

    with open("/etc/pi-k8s/settings.json", "r") as settings_file:
        return json.load(settings_file)

def template_load():

    with open("/etc/pi-k8s/templates.json", "r") as templates_file:
        return json.load(templates_file)

def template_find(text):

    for template in template_load():
        if text == template["text"]:
            return template

    return None

def setting_list():

    return {"settings": setting_load()}

def template_list():

    return {"templates": template_load()}

def chore_create():

    chore = apx.chore_redis.create(
       template_find(connexion.request.json["template"]),
       connexion.request.json["name"],
       connexion.request.json["node"] 
    )

    return {"chore": chore}, 201

def chore_list():

    return {"chores": apx.chore_redis.list()}

def chore_retrieve(node):

    return {"chore": apx.chore_redis.get(node)}

def task_next(node):

    chore = apx.chore_redis.get(node)

    return {"changed": apx.chore_redis.next(chore), "chore": chore}, 202

def task_complete(node, index):

    chore = apx.chore_redis.get(node)

    return {"changed": apx.chore_redis.complete(chore, index), "chore": chore}, 202

def task_incomplete(node, index):

    chore = apx.chore_redis.get(node)

    return {"changed": apx.chore_redis.incomplete(chore, index), "chore": chore}, 202