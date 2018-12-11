import os
import yaml
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

    with open("/etc/pi-k8s/settings.yaml", "r") as settings_file:
        return yaml.load(settings_file)

def template_load():

    with open("/etc/pi-k8s/templates.yaml", "r") as templates_file:
        templates = list(yaml.load_all(templates_file))

    for index, template in enumerate(templates):
        template["id"] = index

    return templates

def template_find(template_id):

    for template in template_load():
        if template_id == template["id"]:
            return template

    return None

def setting_list():

    return {"settings": setting_load()}

def template_list():

    return {"templates": template_load()}

def chore_create():

    chore = apx.chore_redis.create(
       template_find(connexion.request.json["template"]),
       connexion.request.json["person"],
       connexion.request.json["node"] 
    )

    return {"chore": chore}, 201

def chore_list():

    return {"chores": apx.chore_redis.list()}

def chore_retrieve(chore_id):

    return {"chore": apx.chore_redis.get(chore_id)}

def task_next(chore_id):

    chore = apx.chore_redis.get(chore_id)

    return {"changed": apx.chore_redis.next(chore), "chore": chore}, 202

def task_action(chore_id, task_id, action):

    chore = apx.chore_redis.get(chore_id)

    if action in ["pause", "unpause", "skip", "unskip", "complete", "incomplete"]:
        return {"changed": getattr(apx.chore_redis,action)(chore, task_id), "chore": chore}, 202
