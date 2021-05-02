#
# (C) Copyright Cloudlab URV 2020
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


import logging

logger = logging.getLogger(__name__)


class StoragelessBackend:
    def __init__(self, config):
        logger.debug("Creating Storageless dummy client")
        config.pop('user_agent', None)

    def get_client(self):
        logger.error("in StoragelessBackend.get_client")
        raise Exception("Storage access request when Storageless defined")

    def put_object(self, bucket_name, key, data):
        """
        :param bucket_name: bucket name
        :param key: key of the object.
        :param data: data of the object
        :type data: str/bytes
        :return: None
        """
        logger.error("in StoragelessBackend.put_object")
        raise Exception("Storage access request when Storageless defined")

    def get_object(self, bucket_name, key, stream=False, extra_get_args={}):
        """
        :param bucket_name: bucket name
        :param key: key of the object
        :return: Data of the object
        :rtype: str/bytes
        """
        logger.error("in StoragelessBackend.get_object")
        raise Exception("Storage access request when Storageless defined")

    def head_object(self, bucket_name, key):
        """
        Head object from Redis with a key. 
        Throws StorageNoSuchKeyError if the given key does not exist.
        :param bucket_name: bucket name
        :param key: key of the object
        :return: Data of the object
        :rtype: dict
        """
        logger.error("in StoragelessBackend.head_object")
        raise Exception("Storage access request when Storageless defined")

    def delete_object(self, bucket_name, key):
        """
        :param bucket_name: bucket name
        :param key: data key
        """
        logger.error("in StoragelessBackend.delete_object")
        raise Exception("Storage access request when Storageless defined")

    def delete_objects(self, bucket_name, key_list):
        """
        :param bucket_name: bucket name
        :param key_list: list of keys
        """
        logger.error("in StoragelessBackend.delete_objects")
        raise Exception("Storage access request when Storageless defined")

    def head_bucket(self, bucket_name):
        """
        Head bucket from Redis with a name.
        Throws StorageNoSuchKeyError if the given bucket does not exist.
        :param bucket_name: name of the bucket
        :return: metadata of the bucket
        :rtype: dict
        """
        logger.error("in StoragelessBackend.head_bucket")
        raise Exception("Storage access request when Storageless defined")

    def list_objects(self, bucket_name, prefix=None):
        """
        Return a list of objects for the given bucket and prefix.
        :param bucket_name: name of the bucket.
        :param prefix: Prefix to filter object names.
        :return: List of objects in bucket that match the given prefix.
        :rtype: list of dict
        """
        logger.error("in StoragelessBackend.list_objects")
        raise Exception("Storage access request when Storageless defined")

    def list_keys(self, bucket_name, prefix=None):
        """
        Return a list of keys for the given prefix.
        :param bucket_name: name of the bucket.
        :param prefix: Prefix to filter object names.
        :return: List of keys in bucket that match the given prefix.
        :rtype: list of str
        """
        logger.error("in StoragelessBackend.list_keys")
        raise Exception("Storage access request when Storageless defined")

