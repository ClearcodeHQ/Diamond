# coding=utf-8
"""
Gather HTTP Response code and Duration of HTTP request

#### Dependencies
  * urllib2

"""

import urllib2
import time
import re

from urlparse import urlparse
from datetime import datetime

import diamond.collector


class WebsiteMonitorCollector(diamond.collector.Collector):
    """
    Gather HTTP response code and Duration of HTTP request
    """

    def get_default_config_help(self):
        config_help = super(WebsiteMonitorCollector,
                            self).get_default_config_help()
        config_help.update({
            'endpoints': "A list of FQDN of HTTP endpoints to test",
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        default_config = super(WebsiteMonitorCollector,
                               self).get_default_config()
        default_config['endpoints'] = []
        default_config['path'] = 'websitemonitor'
        return default_config

    def get_endpoint_name(self, endpoint):
        netloc = urlparse(endpoint).netloc
        return re.sub(r'[^0-9A-Za-z]', '_', netloc)

    def check_endpoint(self, endpoint):
        """
        Collects information about passed endpoint.
        """
        req = urllib2.Request('%s' % (endpoint))
        endpoint_name = self.get_endpoint_name(endpoint)
        try:
            # time in seconds since epoch as a floating number
            start_time = time.time()
            # human-readable time e.g November 25, 2013 18:15:56
            st = datetime.fromtimestamp(start_time
                                        ).strftime('%B %d, %Y %H:%M:%S')
            self.log.debug('Start time: %s' % (st))

            resp = urllib2.urlopen(req)
            # time in seconds since epoch as a floating number
            end_time = time.time()
            # human-readable end time e.eg. November 25, 2013 18:15:56
            et = datetime.fromtimestamp(end_time).strftime('%B %d, %Y %H:%M%S')
            self.log.debug('End time: %s' % (et))
            # Response time in milliseconds
            rt = int(format((end_time - start_time) * 1000, '.0f'))
            # Publish metrics
            self.publish('%s.response_time.%s' % (endpoint_name, resp.code), rt,
                         metric_type='COUNTER')
        # urllib2 will puke on non HTTP 200/OK URLs
        except urllib2.HTTPError, e:
            if e.code != 200:
                # time in seconds since epoch as a floating number
                end_time = time.time()
                # Response time in milliseconds
                rt = int(format((end_time - start_time) * 1000, '.0f'))
                # Publish metrics -- this is recording a failure, rt will
                # likely be 0 but does capture HTTP Status Code
                self.publish('%s.response_time.%s' % (endpoint_name, e.code), rt,
                             metric_type='COUNTER')

        except IOError, e:
            self.log.error('Unable to open %s' % (endpoint))

        except Exception, e:
            self.log.error("Unknown error opening url: %s", e)

    def collect(self):
        for endpoint in self.config['endpoints']:
            self.check_endpoint(endpoint)
