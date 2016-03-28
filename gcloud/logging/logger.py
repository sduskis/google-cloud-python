# Copyright 2016 Google Inc. All rights reserved.
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

"""Define API Loggers."""

import json

from google.protobuf.json_format import MessageToJson


class Logger(object):
    """Loggers represent named targets for log entries.

    See:
    https://cloud.google.com/logging/docs/api/ref_v2beta1/rest/v2beta1/projects.logs

    :type name: string
    :param name: the name of the logger

    :type client: :class:`gcloud.logging.client.Client`
    :param client: A client which holds credentials and project configuration
                   for the logger (which requires a project).

    :type labels: dict or :class:`NoneType`
    :param labels: (optional) mapping of default labels for entries written
                   via this logger.
    """
    def __init__(self, name, client, labels=None):
        self.name = name
        self._client = client
        self.labels = labels

    @property
    def client(self):
        """Clent bound to the logger."""
        return self._client

    @property
    def project(self):
        """Project bound to the logger."""
        return self._client.project

    @property
    def full_name(self):
        """Fully-qualified name used in logging APIs"""
        return 'projects/%s/logs/%s' % (self.project, self.name)

    def _require_client(self, client):
        """Check client or verify over-ride.

        :type client: :class:`gcloud.logging.client.Client` or ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current logger.

        :rtype: :class:`gcloud.logging.client.Client`
        :returns: The client passed in or the currently bound client.
        """
        if client is None:
            client = self._client
        return client

    def batch(self, client=None):
        """Return a batch to use as a context manager.

        :type client: :class:`gcloud.logging.client.Client` or ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current topic.

        :rtype: :class:`Batch`
        :returns: A batch to use as a context manager.
        """
        client = self._require_client(client)
        return Batch(self, client)

    def _get_labels(self, labels):
        """Return effective labels.

        Helper for :meth:`log_text`, :meth:`log_struct`, and :meth:`log_proto`.

        :type labels: dict or :class:`NoneType`
        :param labels: labels passed in to calling method.

        :rtype: dict or :class:`NoneType`.
        :returns: the passed-in labels, if not none, else any default labels
                  configured on the logger instance.
        """
        if labels is not None:
            return labels
        return self.labels

    def log_text(self, text, client=None, labels=None):
        """API call:  log a text message via a POST request

        See:
        https://cloud.google.com/logging/docs/api/ref_v2beta1/rest/v2beta1/entries/write

        :type text: text
        :param text: the log message.

        :type client: :class:`gcloud.logging.client.Client` or ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current logger.

        :type labels: dict or :class:`NoneType`
        :param labels: (optional) mapping of labels for the entry.
        """
        client = self._require_client(client)

        data = {
            'entries': [{
                'logName': self.full_name,
                'textPayload': text,
                'resource': {
                    'type': 'global',
                },
            }],
        }

        labels = self._get_labels(labels)
        if labels is not None:
            data['entries'][0]['labels'] = labels

        client.connection.api_request(
            method='POST', path='/entries:write', data=data)

    def log_struct(self, info, client=None, labels=None):
        """API call:  log a structured message via a POST request

        See:
        https://cloud.google.com/logging/docs/api/ref_v2beta1/rest/v2beta1/entries/write

        :type info: dict
        :param info: the log entry information

        :type client: :class:`gcloud.logging.client.Client` or ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current logger.

        :type labels: dict or :class:`NoneType`
        :param labels: (optional) mapping of labels for the entry.
        """
        client = self._require_client(client)

        data = {
            'entries': [{
                'logName': self.full_name,
                'jsonPayload': info,
                'resource': {
                    'type': 'global',
                },
            }],
        }

        labels = self._get_labels(labels)
        if labels is not None:
            data['entries'][0]['labels'] = labels

        client.connection.api_request(
            method='POST', path='/entries:write', data=data)

    def log_proto(self, message, client=None, labels=None):
        """API call:  log a protobuf message via a POST request

        See:
        https://cloud.google.com/logging/docs/api/ref_v2beta1/rest/v2beta1/entries/write

        :type message: Protobuf message
        :param message: the message to be logged

        :type client: :class:`gcloud.logging.client.Client` or ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current logger.

        :type labels: dict or :class:`NoneType`
        :param labels: (optional) mapping of labels for the entry.
        """
        client = self._require_client(client)
        as_json_str = MessageToJson(message)
        as_json = json.loads(as_json_str)

        data = {
            'entries': [{
                'logName': self.full_name,
                'protoPayload': as_json,
                'resource': {
                    'type': 'global',
                },
            }],
        }

        labels = self._get_labels(labels)
        if labels is not None:
            data['entries'][0]['labels'] = labels

        client.connection.api_request(
            method='POST', path='/entries:write', data=data)

    def delete(self, client=None):
        """API call:  delete all entries in a logger via a DELETE request

        See:
        https://cloud.google.com/logging/docs/api/ref_v2beta1/rest/v2beta1/projects.logs/delete

        :type client: :class:`gcloud.logging.client.Client` or ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current logger.
        """
        client = self._require_client(client)
        client.connection.api_request(
            method='DELETE', path='/%s' % self.full_name)

    def list_entries(self, projects=None, filter_=None, order_by=None,
                     page_size=None, page_token=None):
        """Return a page of log entries.

        See:
        https://cloud.google.com/logging/docs/api/ref_v2beta1/rest/v2beta1/entries/list

        :type projects: list of strings
        :param projects: project IDs to include. If not passed,
                            defaults to the project bound to the client.

        :type filter_: string
        :param filter_: a filter expression. See:
                        https://cloud.google.com/logging/docs/view/advanced_filters

        :type order_by: string
        :param order_by: One of :data:`gcloud.logging.ASCENDING` or
                         :data:`gcloud.logging.DESCENDING`.

        :type page_size: int
        :param page_size: maximum number of entries to return, If not passed,
                          defaults to a value set by the API.

        :type page_token: string
        :param page_token: opaque marker for the next "page" of entries. If not
                           passed, the API will return the first page of
                           entries.

        :rtype: tuple, (list, str)
        :returns: list of :class:`gcloud.logging.entry.TextEntry`, plus a
                  "next page token" string:  if not None, indicates that
                  more entries can be retrieved with another call (pass that
                  value as ``page_token``).
        """
        log_filter = 'logName:%s' % (self.name,)
        if filter_ is not None:
            filter_ = '%s AND %s' % (filter_, log_filter)
        else:
            filter_ = log_filter
        return self.client.list_entries(
            projects=projects, filter_=filter_, order_by=order_by,
            page_size=page_size, page_token=page_token)


class Batch(object):
    """Context manager:  collect entries to log via a single API call.

    Helper returned by :meth:`Logger.batch`

    :type logger: :class:`gcloud.logging.logger.Logger`
    :param logger: the logger to which entries will be logged.

    :type client: :class:`gcloud.logging.client.Client`
    :param client: The client to use.
    """
    def __init__(self, logger, client):
        self.logger = logger
        self.entries = []
        self.client = client

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()

    def log_text(self, text):
        """Add a text entry to be logged during :meth:`commit`.

        :type text: string
        :param text: the text entry
        """
        self.entries.append(('text', text))

    def log_struct(self, info):
        """Add a struct entry to be logged during :meth:`commit`.

        :type info: dict
        :param info: the struct entry
        """
        self.entries.append(('struct', info))

    def log_proto(self, message):
        """Add a protobuf entry to be logged during :meth:`commit`.

        :type message: protobuf message
        :param message: the protobuf entry
        """
        self.entries.append(('proto', message))

    def commit(self, client=None):
        """Send saved log entries as a single API call.

        :type client: :class:`gcloud.logging.client.Client` or ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current batch.
        """
        if client is None:
            client = self.client
        data = {
            'logName': self.logger.path,
            'resource': {'type': 'global'},
        }
        entries = data['entries'] = []
        for entry_type, entry in self.entries:
            if entry_type == 'text':
                info = {'textPayload': entry}
            elif entry_type == 'struct':
                info = {'structPayload': entry}
            elif entry_type == 'proto':
                as_json_str = MessageToJson(entry)
                as_json = json.loads(as_json_str)
                info = {'protoPayload': as_json}
            else:
                raise ValueError('Unknown entry type: %s' % (entry_type,))
            entries.append(info)

        client.connection.api_request(
            method='POST', path='/entries:write', data=data)
        del self.entries[:]
