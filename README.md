# python-libobs - Python binding for Open Build Service REST API.

Python binding for the [Open Build Service (OBS)][1] [REST API][2].

Currently, only supporting(all I need right now):
  * Trigger run of defined services in `_service` file
  * Query project building status.
  * Upload(create or override) source file.

Please check `test.py` for sample:
```
env OBS_USER='cathay4t' \
    OBS_PASS='noidea' \
    OBS_PROJECT='home:cathay4t:libstoragemgmt-rhel7-test' \
    OBS_PKG="libstoragemgmt" \
    OBS_GIT_REPO="https://github.com/cathay4t/libstoragemgmt.git" \
    OBS_GIT_BRANCH="fix_ontap_vri" \
    ./test.py
```

Licensed under GPLv3+.

[1]: http://www.open-build-service.org
[2]: https://github.com/openSUSE/open-build-service/blob/master/docs/api/api/api.txt
