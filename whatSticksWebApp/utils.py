import os

#location of app_package directory
app_package_dir = os.path.abspath(os.path.dirname(__file__))
isExist = os.path.exists(os.path.join(app_package_dir,'_logs'))
if not isExist:
    os.makedirs(os.path.join(app_package_dir,'_logs'))
logs_dir = os.path.join(app_package_dir,'_logs')
