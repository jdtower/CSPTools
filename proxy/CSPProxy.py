#!/usr/bin/python

import signal
import sys
import threading
import os
import json
from libmproxy import proxy, flow
import re

#Todo
#	Local logging should be optional (opt-in/out?)
#defaultcsp = 'default-src \'none\'; script-src \'none\'; object-src \'none\'; img-src \'none\'; media-src \'none\'; style-src \'none\'; frame-src \'none\'; font-src \'none\'; xhr-src \'none\';'

#Create proxy
class CSPTestMaster(flow.FlowMaster):
    def __init__(self, server, state, policy, hostre, reporturi, block, callback=None):
        flow.FlowMaster.__init__(self, server, state)
        self.policy = policy
        self.hostre = hostre
        self.reporturi = reporturi
        self.callback = callback
        self.block = block

    def run(self):
        try:
            flow.FlowMaster.run(self)
        except KeyboardInterrupt:
            self.shutdown()

    def handle_request(self, r):
        f = flow.FlowMaster.handle_request(self, r)
        if f:
            if r.path == self.reporturi:
                report=json.loads(r.content)['csp-report']
                print report['violated-directive'] + " : " + report['blocked-uri']
                if(self.callback):
                    self.callback(r.content.strip())
        r.reply()
        return f

    def handle_response(self, r):
        f = flow.FlowMaster.handle_response(self, r)
        if f:
            if(self.hostre.search(r.request.host)):
                if self.block:
        	        f.response.headers.add("Content-Security-Policy-Report", self.policy + "report-uri " +self.reporturi); 
                else:
        	        f.response.headers.add("Content-Security-Policy-Report-Only", self.policy + "report-uri " +self.reporturi); 
        r.reply()
        return f

class CSPProxy:
    def __init__(self, policy, port, hostre, reporturi, block, callback):
        config = proxy.ProxyConfig(cacert = os.path.expanduser("~/.mitmproxy/mitmproxy-ca.pem"))
        state = flow.State()
        server = proxy.ProxyServer(config, port)
        self.proxy = CSPTestMaster(server, state, policy, hostre, reporturi, block, callback)

    def run(self):
        self.proxy.run()

    def shutdown(self):
        self.proxy.shutdown()
