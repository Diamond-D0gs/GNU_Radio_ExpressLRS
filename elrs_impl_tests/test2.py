from hashlib import md5

uid = md5(str(f'-DMY_BINDING_PHRASE="{'eggseggs'}"').encode('utf-8')).digest()[:6]
print(list(uid))
print('')