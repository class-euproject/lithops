#
# Copyright Cloudlab URV 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import os
import time
import click
import logging
import shutil

import lithops
from lithops.tests import print_help, run_tests
from lithops.utils import setup_logger, verify_runtime_name
from lithops.config import get_mode, default_config, extract_storage_config,\
    extract_serverless_config, extract_standalone_config,\
    extract_localhost_config
from lithops.constants import CACHE_DIR, LITHOPS_TEMP_DIR, RUNTIMES_PREFIX,\
    JOBS_PREFIX, LOCALHOST, SERVERLESS, STANDALONE, FN_LOG_FILE, LOGS_DIR
from lithops.storage import InternalStorage
from lithops.serverless import ServerlessHandler
from lithops.storage.utils import clean_bucket
from lithops.standalone.standalone import StandaloneHandler
from lithops.localhost.localhost import LocalhostHandler

from lithops.utils import b64str_to_bytes
import hashlib

logger = logging.getLogger(__name__)


@click.group('lithops_cli')
@click.version_option()
def lithops_cli():
    pass


@lithops_cli.command('clean')
@click.option('--config', '-c', default=None, help='use json config file')
@click.option('--mode', '-m', default=None,
              type=click.Choice([SERVERLESS, LOCALHOST, STANDALONE], case_sensitive=True),
              help='execution mode')
@click.option('--backend', '-b', default=None, help='compute backend')
@click.option('--debug', '-d', is_flag=True, help='debug mode')
def clean(config, mode, backend, debug):
    log_level = 'INFO' if not debug else 'DEBUG'
    setup_logger(log_level)
    logger.info('Cleaning all Lithops information')

    mode = mode or get_mode(config)
    config_ow = {'lithops': {'mode': mode}}
    if backend:
        config_ow[mode] = {'backend': backend}
    config = default_config(config, config_ow)

    storage_config = extract_storage_config(config)
    internal_storage = InternalStorage(storage_config)

    mode = config['lithops']['mode'] if not mode else mode
    if mode == LOCALHOST:
        compute_config = extract_localhost_config(config)
        compute_handler = LocalhostHandler(compute_config)
    elif mode == SERVERLESS:
        compute_config = extract_serverless_config(config)
        compute_handler = ServerlessHandler(compute_config, storage_config)
    elif mode == STANDALONE:
        compute_config = extract_standalone_config(config)
        compute_handler = StandaloneHandler(compute_config)

    compute_handler.clean()

    # Clean object storage temp dirs
    storage = internal_storage.storage
    clean_bucket(storage, storage_config['bucket'], RUNTIMES_PREFIX, sleep=1)
    clean_bucket(storage, storage_config['bucket'], JOBS_PREFIX, sleep=1)

    # Clean localhost executor temp dirs
    shutil.rmtree(LITHOPS_TEMP_DIR, ignore_errors=True)
    # Clean local lithops cache
    shutil.rmtree(CACHE_DIR, ignore_errors=True)


@lithops_cli.command('test')
@click.option('--config', '-c', default=None, help='use json config file')
@click.option('--mode', '-m', default=None,
              type=click.Choice([SERVERLESS, LOCALHOST, STANDALONE], case_sensitive=True),
              help='execution mode')
@click.option('--backend', '-b', default=None, help='compute backend')
@click.option('--debug', '-d', is_flag=True, help='debug mode')
def test_function(config, mode, backend, debug):

    if debug:
        setup_logger(logging.DEBUG)

    def hello(name):
        return 'Hello {}!'.format(name)

    fexec = lithops.FunctionExecutor(config=config, mode=mode, backend=backend)
    fexec.call_async(hello, 'World')
    result = fexec.get_result()
    print()
    if result == 'Hello World!':
        print(result, 'Lithops is working as expected :)')
    else:
        print(result, 'Something went wrong :(')
    print()


@lithops_cli.command('verify')
@click.option('--test', '-t', default='all', help='run a specific test, type "-t help" for tests list')
@click.option('--config', '-c', default=None, help='use json config file')
@click.option('--mode', '-m', default=None,
              type=click.Choice([SERVERLESS, LOCALHOST, STANDALONE], case_sensitive=True),
              help='execution mode')
@click.option('--backend', '-b', default=None, help='compute backend')
@click.option('--debug', '-d', is_flag=True, help='debug mode')
def verify(test, config, mode, backend, debug):
    if debug:
        setup_logger(logging.DEBUG)

    if test == 'help':
        print_help()
    else:
        run_tests(test, config, mode, backend)


# /---------------------------------------------------------------------------/
#
# lithops logs
#
# /---------------------------------------------------------------------------/

@click.group('logs')
@click.pass_context
def logs(ctx):
    pass


@logs.command('poll')
def poll():
    logging.basicConfig(level=logging.DEBUG)

    def follow(file):
        line = ''
        while True:
            if not os.path.isfile(FN_LOG_FILE):
                break
            tmp = file.readline()
            if tmp:
                line += tmp
                if line.endswith("\n"):
                    yield line
                    line = ''
            else:
                time.sleep(1)

    while True:
        if os.path.isfile(FN_LOG_FILE):
            for line in follow(open(FN_LOG_FILE, 'r')):
                print(line, end='')
        else:
            time.sleep(1)


@logs.command('get')
@click.argument('job_key')
def get(job_key):
    log_file = os.path.join(LOGS_DIR, job_key+'.log')

    if not os.path.isfile(log_file):
        print('The execution id: {} does not exists in logs'.format(job_key))
        return

    with open(log_file, 'r') as content_file:
        print(content_file.read())


# /---------------------------------------------------------------------------/
#
# lithops runtime
#
# /---------------------------------------------------------------------------/

@click.group('runtime')
@click.pass_context
def runtime(ctx):
    pass


@runtime.command('create')
@click.argument('name')
@click.option('--backend', '-b', default=None, help='compute backend')
@click.option('--memory', default=None, help='memory used by the runtime', type=int)
@click.option('--timeout', default=None, help='runtime timeout', type=int)
@click.option('--config', '-c', default=None, help='use json config file')
def create(name, backend, memory, timeout, config):
    """ Create a serverless runtime """
    setup_logger(logging.DEBUG)
    logger.info('Creating new lithops runtime: {}'.format(name))

    mode = SERVERLESS 
    config_ow = {'lithops': {'mode': mode}}
    if backend:
        config_ow[mode] = {'backend': backend}
    config = default_config(config, config_ow)

    storage_config = extract_storage_config(config)
    internal_storage = InternalStorage(storage_config)

    compute_config = extract_serverless_config(config)
    compute_handler = ServerlessHandler(compute_config, storage_config)
    mem = memory if memory else compute_config['runtime_memory']
    to = timeout if timeout else compute_config['runtime_timeout']
    runtime_key = compute_handler.get_runtime_key(name, mem)
    runtime_meta = compute_handler.create_runtime(name, mem, timeout=to)

    try:
        internal_storage.put_runtime_meta(runtime_key, runtime_meta)
    except Exception:
        raise("Unable to upload 'preinstalled-modules' file into {}".format(internal_storage.backend))

def _store_modules(func_key, function_file, module_data):
    # save function
    func_path = '/'.join([LITHOPS_TEMP_DIR, func_key, 'mapfunc.py'])
    os.makedirs(os.path.dirname(func_path), exist_ok=True)

    modules_path = '/'.join([os.path.dirname(func_path), 'modules'])
    os.makedirs(modules_path, exist_ok=True)

    from shutil import copy

    copy(function_file, modules_path)

    if module_data:
        logger.debug("Writing Function dependencies to local disk")

        for m_filename, m_data in module_data.items():
            m_path = os.path.dirname(m_filename)

            if len(m_path) > 0 and m_path[0] == "/":
                m_path = m_path[1:]
            to_make = os.path.join(modules_path, m_path)
            try:
                os.makedirs(to_make)
            except OSError as e:
                if e.errno == 17:
                    pass
                else:
                    raise e
            full_filename = os.path.join(to_make, os.path.basename(m_filename))

            with open(full_filename, 'wb') as fid:
                fid.write(b64str_to_bytes(m_data))

    logger.debug("Finished storing function and modules")
    return os.path.dirname(func_path), modules_path

@runtime.command('extend')
@click.argument('base_runtime_name')
@click.option('--filepath', required=True, help='full path to the python file with map function')
@click.option('--function', required=True, help='name of the map function')
@click.option('--memory', default=None, help='memory used by the runtime', type=int)
@click.option('--timeout', default=None, help='runtime timeout', type=int)
@click.option('--config', '-c', default=None, help='use json config file')
@click.option('--exclude_modules', multiple=True, default=[], help='modules to exclude for docker build')
@click.option('--include_modules', multiple=True, default=[], help='modules to include for docker build')
@click.option('--image', '-i', default=None, help='docker image name, specified when runtime derrived from ow kind')
def extend(base_runtime_name, filepath, function, memory, timeout, config, exclude_modules, image, include_modules):
    """ Create a serverless runtime """
    setup_logger(logging.DEBUG)
    logger.info('Extending custom lithops runtime: {}'.format(base_runtime_name))

    path, function_file_name = os.path.split(filepath)

    function_mod_name = function_file_name
    if function_mod_name.endswith('.py'):
        function_mod_name = function_mod_name[:-3]

    config = default_config(config, {'lithops': {'mode': SERVERLESS}})

    storage_config = extract_storage_config(config)
    internal_storage = InternalStorage(storage_config)

    compute_config = extract_serverless_config(config)
    compute_handler = ServerlessHandler(compute_config, storage_config)
    mem = memory if memory else compute_config['runtime_memory']
    to = timeout if timeout else compute_config['runtime_timeout']

    runtime_key = compute_handler.get_runtime_key(base_runtime_name, mem)
    runtime_meta = internal_storage.get_runtime_meta(runtime_key)
    kind = compute_config[compute_config['backend']].get('kind')
    import importlib
    import sys
    import pickle
    import hashlib

    from lithops.job.serialize import SerializeIndependent, create_module_data

    if kind:
        ext_runtime_name = base_runtime_name
        ext_runtime_image_name = image
        ext_runtime_key = runtime_key
        base_image_name = image
    else:
        runtime_tag = hashlib.md5(open(filepath,'rb').read()).hexdigest()[:16]
        ext_runtime_name = "{}:{}".format(base_runtime_name.rsplit(":", 1)[0], runtime_tag)
        ext_runtime_image_name = ext_runtime_name
        base_image_name = base_runtime_name
        ext_runtime_key = compute_handler.get_runtime_key(ext_runtime_name, mem)

    sys.path.append(path)
    func_module = importlib.__import__(function_mod_name)
    func = getattr(func_module, function)

    serializer = SerializeIndependent(runtime_meta['preinstalls'])
    _, mod_paths = serializer([func], include_modules, exclude_modules)
    for inc_mod_name in include_modules:
        mod_paths.add(importlib.__import__(inc_mod_name).__path__[0])

    module_data = create_module_data(mod_paths)

    func_path, modules_path = _store_modules(ext_runtime_key, filepath, module_data)
    ext_docker_file = '/'.join([modules_path, "Dockerfile"])

    # Generate Dockerfile extended with function dependencies and function
    with open(ext_docker_file, 'w') as df:
        df.write('\n'.join([
                        'FROM {}'.format(base_image_name),
                        'ENV PYTHONPATH={}:${}'.format(func_path,'PYTHONPATH'), # set python path to point to dependencies folder
                        'COPY . {}'.format(func_path)]))

    # Build new extended runtime tagged by function hash
    cwd = os.getcwd()
    os.chdir(modules_path)

    compute_handler.build_runtime(ext_runtime_image_name, ext_docker_file)
    os.chdir(cwd)

    ext_runtime_meta = compute_handler.create_runtime(ext_runtime_name, mem, timeout=to)
    ext_meta = runtime_meta.get('ext_meta', {'map_func_mod': [], 'map_func': []})

    if function_mod_name not in ext_meta['map_func_mod']:
        ext_meta['map_func_mod'].append(function_mod_name)
    if function not in ext_meta['map_func']:
        ext_meta['map_func'].append(function)

    ext_runtime_meta['ext_meta'] = ext_meta

    ext_runtime_meta['map_func_mod'] = f'{function_mod_name}'
    ext_runtime_meta['map_func'] = f'{function}'
    logger.info("==============================================")
    logger.info(f"Extended runtime: {ext_runtime_name}")
    logger.info("==============================================")
    internal_storage.put_runtime_meta(ext_runtime_key, ext_runtime_meta)

@runtime.command('build')
@click.argument('name')
@click.option('--file', '-f', default=None, help='file needed to build the runtime')
@click.option('--config', '-c', default=None, help='use json config file')
@click.option('--backend', '-b', default=None, help='compute backend')
def build(name, file, config, backend):
    """ build a serverless runtime. """
    verify_runtime_name(name)
    setup_logger(logging.DEBUG)

    mode = SERVERLESS
    config_ow = {'lithops': {'mode': mode}}
    if backend:
        config_ow[mode] = {'backend': backend}
    config = default_config(config, config_ow)

    storage_config = extract_storage_config(config)
    compute_config = extract_serverless_config(config)
    compute_handler = ServerlessHandler(compute_config, storage_config)
    compute_handler.build_runtime(name, file)


@runtime.command('update')
@click.argument('name')
@click.option('--config', '-c', default=None, help='use json config file')
@click.option('--backend', '-b', default=None, help='compute backend')
def update(name, config, backend):
    """ Update a serverless runtime """
    verify_runtime_name(name)
    setup_logger(logging.DEBUG)

    mode = SERVERLESS
    config_ow = {'lithops': {'mode': mode}}
    if backend:
        config_ow[mode] = {'backend': backend}
    config = default_config(config, config_ow)

    storage_config = extract_storage_config(config)
    internal_storage = InternalStorage(storage_config)
    compute_config = extract_serverless_config(config)
    compute_handler = ServerlessHandler(compute_config, storage_config)

    timeout = compute_config['runtime_memory']
    logger.info('Updating runtime: {}'.format(name))

    runtimes = compute_handler.list_runtimes(name)

    for runtime in runtimes:
        runtime_key = compute_handler.get_runtime_key(runtime[0], runtime[1])
        runtime_meta = compute_handler.create_runtime(runtime[0], runtime[1], timeout)

        try:
            internal_storage.put_runtime_meta(runtime_key, runtime_meta)
        except Exception:
            raise("Unable to upload 'preinstalled-modules' file into {}".format(internal_storage.backend))


@runtime.command('delete')
@click.argument('name')
@click.option('--config', '-c', default=None, help='use json config file')
@click.option('--backend', '-b', default=None, help='compute backend')
def delete(name, config, backend):
    """ delete a serverless runtime """
    verify_runtime_name(name)
    setup_logger(logging.DEBUG)

    mode = SERVERLESS
    config_ow = {'lithops': {'mode': mode}}
    if backend:
        config_ow[mode] = {'backend': backend}
    config = default_config(config, config_ow)

    storage_config = extract_storage_config(config)
    internal_storage = InternalStorage(storage_config)
    compute_config = extract_serverless_config(config)
    compute_handler = ServerlessHandler(compute_config, storage_config)

    runtimes = compute_handler.list_runtimes(name)
    for runtime in runtimes:
        compute_handler.delete_runtime(runtime[0], runtime[1])
        runtime_key = compute_handler.get_runtime_key(runtime[0], runtime[1])
        internal_storage.delete_runtime_meta(runtime_key)


lithops_cli.add_command(runtime)
lithops_cli.add_command(logs)


if __name__ == '__main__':
    lithops_cli()
