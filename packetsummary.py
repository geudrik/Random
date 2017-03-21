#! /usr/bin/env python2.7
#
#   packetsummary.pl -> packetsummary.py
#
#   Written by Pat Litke.
#   Reason: GLP is too restrictive (yes, I'm pointing at you, Cuckoo)
#   This is essentially a re-write of my Scapy based summary script (because scapy..)
#
#   Thank you Jon Oberheide for your dpkt crash-course
#   Thank you to the DPKT developers for making their lib easily accessible

# Requirements
import dpkt
import magic

# Standard Lib
import socket
import string
import os
import urlparse
import re

class packetsummary(object):
    """
    Accepts a filepath as a single argument, returns a dict
    Raises an exceptions on errors
    """

    def __init__(self, path = None):
        """
        Initialize
        """

        if path == None:
            raise Exception("No filepath to our pcap specified")

        if not os.path.exists(path):
            raise Exception("Filepath {0} doesn't exist".format(path))

        if os.path.getsize(path) == 0:
            raise Exception("The file supplied is zero bytes in size...")

        mime    =   magic.from_file(path, mime=True)
        if mime != "application/vnd.tcpdump.pcap":
            raise Exception("Bad mime type for this file ({0}). Must be application/vnd.tcpdump.pcap".format(mime))

        # Set our instance vars
        self.path               =   path
        self.smtpFlows          =   {}

        self.stratumRE          =   re.compile('^\{"method": "mining.authorize".*\["(.*)", "(.*)"\]')
        self.SSHRE1             =   re.compile('^SSH.*-OpenSSH_\d.*\s.*\-.*\x0D\x0A$')
        self.SSHRE2             =   re.compile('^SSH.*-OpenSSH_\d.*\x0D\x0A$')


        # Define our result skeleton
        self.results            =   {

            # Hosts
            'hosts'             :   [],

            # Domain
            'domains'           :   [],
            'dns'               :   [],

            # HTTP
            'http'              :   [],

            # Flows
            'tcp_connections'   :   [],
            'udp_connections'   :   [],
            'icmp_requests'     :   [],

            # Application traffic
            'smtp'              :   [],
            'irc'               :   [],
            'stratum'           :   [],
            'ssl'               :   [],
            'ssh'               :   [],
        }

    def _convert_string_to_printable(self, s = None):
        """
        Ensure that the passed string contains only printable characters.
        If it doesn't, convert those that aren't to hex
        """
        r = ""
        for c in s:
            if c not in string.printable:
                r += "\\x%02x" % ord(c)
            else:
                r += c
        return r

    def _tcp_parse_http(self, c = None, data = None):
        """
        Extract HTTP Flow information and add it to our results
        We've opted to re-parse the data portion of our packet as our check sets valid defaults to False
        """

        try:
            http            =   dpkt.http.Request()
            http.unpack(data)
        except:
            pass

        try:

            flow            =   {
                'host'          :   None,
                'port'          :   c['spt'],
                'payload'       :   self._convert_string_to_printable(data),

                # https://docs.python.org/2/library/urlparse.html#urlparse.urlunparse
                'uri'           :   None,
                'body'          :   self._convert_string_to_printable(http.body),
                'path'          :   self._convert_string_to_printable(http.uri),
                'user-agent'    :   self._convert_string_to_printable(http.headers['user-agent']) if 'user-agent' in http.headers else None,
                'version'       :   self._convert_string_to_printable(http.version),
                'method'        :   self._convert_string_to_printable(http.method)
            }

            # Check for a host
            if 'host' in http.headers:
                flow['host'] = self._convert_string_to_printable(http.headers['host'])

            # Build our URI
            flow['uri']         =   self._convert_string_to_printable(urlparse.urlunparse(
                    (
                        'http',
                        flow['host'],
                        http.uri,
                        None,
                        None,
                        None
                    )
                ))

            # Add our flow to our results
            self.results['http'].append(flow)

        except Exception:
            pass

    def _tcp_build_smtp(self, c = None, data = None, reassemble = False):
        """
        Build / Reassemble SMTP flows
        """

        if reassemble == False:

            if c['dst'] in self.smtpFlows:
                self.smtpFlows[c['dst']] =+ data
            else:
                self.smtpFlows[c['dst']] = data

        else:

            for flow, data in self.smtpFlows.iteritems():
                # New flow
                if data.startswith("HELO") or data.startswith("HELO"):
                    self.smtp_requests.appent({"dest":flow, "payload":data})

    def _add_unique_domains(self, domain = None):
        """
        Attempt to add domain to our list of unique domains
        """
        if domain not in self.results['domains']:
            self.results['domains'].append(domain)

    def _udp_parse_dns(self, data):
        """
        Parse all DNS stuffery and build our DNS result list
        """

        dns                         =   dpkt.dns.DNS(data)
        q                           =   {}
        qType                       =   None
        qName                       =   None

        rD                          =   {
            dpkt.dns.DNS_A          :   'A',
            dpkt.dns.DNS_AAAA       :   'AAAA',
            dpkt.dns.DNS_MX         :   'MX',
            dpkt.dns.DNS_NS         :   'NS',
            dpkt.dns.DNS_TXT        :   'TXT',
            dpkt.dns.DNS_CNAME      :   'CNAME',
            dpkt.dns.DNS_PTR        :   'PTR',
            dpkt.dns.DNS_SOA        :   'SOA',
            dpkt.dns.DNS_SRV        :   'SRV',
            dpkt.dns.DNS_HINFO      :   'HINFO',
        }

        # Ensure we have a clean message
        if (
            dns.opcode == dpkt.dns.DNS_QUERY or
            dns.rcode == dpkt.dns.DNS_RCODE_NOERR or
            dns.qr == dpkt.dns.DNS_R
            ):

            ##
            ### Question
            try:
                qType               =   dns.qd[0].type
                qName               =   dns.qd[0].name
            except IndexError:
                return False

            q['request']            =   qName

            # Match on Query
            try:
                q['type']           =   rD[qType]
            except:
                pass

            ##
            ### Answers
            q['answers']            =   []
            for ans in dns.an:
                a                   =   {}

                # A Response
                if ans.type == dpkt.dns.DNS_A:
                    a['type']       =   'A'
                    try:
                        a['data']   =   socket.inet_ntoa(ans.rdata)
                    except:
                        continue

                # QuadA Response
                elif ans.type == dpkt.dns.DNS_AAAA:
                    a['type']       =   'AAAA'
                    try:
                        a['data']   =   socket.inet_ntop(socket.AF_INET6, ans.rdata)
                    except:
                        continue

                # SOA Response
                elif ans.type == dpkt.dns.DNS_SOA:
                    a['type']       =   'SOA'
                    a['data']       =   ','.join([ ans.mname, ans.rname, str(ans.serial), str(ans.minimum), str(ans.refresh), str(ans.retry), str(ans.expire) ])

                elif ans.type == dpkt.dns.DNS_MX:
                    a['type']       =   'MX'
                    a['data']       =   ans.mxname

                elif ans.type == dpkt.dns.DNS_NS:
                    a['type']       =   'NS'
                    a['data']       =   ans.nsname

                elif ans.type == dpkt.dns.DNS_TXT:
                    a['type']       =   'TXT'
                    a['data']       =   ' '.join(ans.text)

                elif ans.type == dpkt.dns.DNS_CNAME:
                    a['type']       =   'CNAME'
                    a['data']       =   ans.cname

                elif ans.type == dpkt.dns.DNS_PTR:
                    a['type']       =   'PTR'
                    a['data']       =   ans.ptrname

                elif ans.type == dpkt.dns.DNS_HINFO:
                    a['type']       =   'HINFO'
                    a['data']       =   ' '.join(ans.text)

                elif ans.type == dpkt.dns.DNS_SRV:
                    # Do something with SRV
                    pass


                q['answers'].append(a)


            # Cleanup and uniquifying
            self._add_unique_domains(q['request'])
            self.results['dns'].append(q)

    def _add_host(self, h = None):
        """
        Add a host to our list of unique hosts
        """
        if h == None:
            raise Exception("No host passed to _add_host")

        s   =   self._convert_string_to_printable(h['src'])
        d   =   self._convert_string_to_printable(h['dst'])

        if s not in self.results['hosts']:
            self.results['hosts'].append(s)

        if d not in self.results['hosts']:
            self.results['hosts'].append(d)



    def _parse_tcp(self, tstamp = None, c = None, data = None):
        """
        This is more or less a meta routing. We're indicate which methods
        we want to run against this packet (though they're defined elsewhere)
        """

        ##
        ### HTTP
        try:
            http            =   dpkt.http.Request()
            http.method     =   False
            http.uri        =   False
            http.version    =   False
            http            =   http.unpack(data)
            self._tcp_parse_http(c, data)

        except:

            # If any of our three fields are set, good enough
            if http.method or http.uri or http.version:
                self._tcp_parse_http(c, data)


        ##
        ### IRC TODO:


        ##
        ### SSH - This is a total hack
        if self.SSHRE1.match(data):
            self.results['ssh'].append([tstamp, "Potential SSH v2 Client Connection"])
        elif self.SSHRE2.match(data):
            self.results['ssh'].append([tstamp, "Potential SSH v2 Server Response"])



        ##
        ### SSL
        # Normal SSL
        try:

            sslStream = isinstance(dpkt.ssl.TLSRecord(data), dpkt.ssl.TLSRecord)
            if sslStream:
                if c['spt'] == 443 or c['dpt'] == 443:
                    self.results['ssl'].append([tstamp, "SSL/TLS Stream Initialization"])
                elif c['spt'] != 443 or c['dpt'] != 443:
                    self.results['ssl'].append([tstamp, "SSL/TLS over non-standard port spt: {0} dpt {1}".format(c['spt'], c['dpt'])])

            elif not sslStream:
                if c['spt'] == 443 or c['dpt']:
                    self.results['ssl'].append([tstamp, "Non-SSL Stream Detected over port 443", self._convert_string_to_printable(data) ])

        except:
            pass


        ##
        ### Stratrum
        strat = self.stratumRE.match(data)
        if strat:
            info    =   {
                'user'      :   strat.group(1),
                'pass'      :   strat.group(2),
                'payload'   :   self._convert_string_to_printable(data)
            }
            self.results['stratum'].append([tstamp, info])



        ##
        ### SMTP
        if c['dpt'] == 25:
            self._tcp_build_smtp(c, data)


    def _parse_udp(self, tstamp = None, c = None, data = None):
        """
        Just like the TCP parse instance above, this is more or less a meta method
        """

        ##
        ### DNS
        try:
            dpkt.dns.DNS(data)
            self._udp_parse_dns(data)
        except:
            pass


    def _parse_icmp(self, c = None, data = None):
        """

        """



    def run(self):
        """
        Attempt analysis on the file we've got set
        """

        # Open a DPKT reader
        try:
            handle = open(self.path, 'rb')
            pcap = dpkt.pcap.Reader(handle)
        except(IOError, OSError):
            raise Exception("Unable to open our file, and/or read from it")

        # Loop through our capture, one packet at a time
        for timestamp, buff in pcap:
            # try:

            # Get packet data
            eth                 =   dpkt.ethernet.Ethernet(buff)
            ip                  =   eth.data

            # Define var for this packet
            c                   =   {}

            # Packet is IPv4
            if isinstance(ip, dpkt.ip.IP):
                c['src']        =   socket.inet_ntoa(ip.src)
                c['dst']        =   socket.inet_ntoa(ip.dst)

            # Packet is IPv6
            elif isinstance(ip, dpkt.ip6.IP6):
                c['src']        =   socket.inet_ntop(socket.AF_INET6, ip.src)
                c['dst']        =   socket.inet_ntop(socket.AF_INET6, ip.dst)

            # Unknown type, go to next packet
            else:
                continue

            # Attempt to add a new host
            self._add_host(c)

            # Handle TCP Processing
            if ip.p == dpkt.ip.IP_PROTO_TCP:

                # Get data
                tcp             =   ip.data
                if not isinstance(tcp, dpkt.tcp.TCP):
                    tcp         =   dpkt.tcp.TCP(tcp)

                # Ensure we actually have data to work with (eg: not an empty packet)
                if len(tcp.data) > 0:
                    c['spt']    =   tcp.sport
                    c['dpt']    =   tcp.dport

                    # TCP connection: add it to our timeline
                    self.results['tcp_connections'].append(c)

                    # Process our TCP packet
                    self._parse_tcp(timestamp, c, tcp.data)

                else:
                    continue


            # Handle UDP Processing
            elif ip.p == dpkt.ip.IP_PROTO_UDP:

                # Get data
                udp             =   ip.data
                if not isinstance(udp, dpkt.udp.UDP):
                    udp         =   dpkt.udp.UDP(udp)

                # Ensure we actually have data to work with (eg: not an empty packet)
                if len(udp.data) > 0:
                    c['spt']    =   udp.sport
                    c['dpt']    =   udp.dport

                    # udp connection: add it to our timeline
                    self.results['udp_connections'].append(c)

                    # Process our udp packet
                    self._parse_udp(timestamp, c, udp.data)

                else:
                    continue


            # Handle ICMP Processing
            elif ip.p == dpkt.ip.IP_PROTO_ICMP:

                # Get data
                icmp                =   ip.data
                if not isinstance(icmp, dpkt.icmp.ICMP):
                    icmp            =   dpkt.icmp.ICMP(icmp)

                # Process ICMP
                #self._parse_icmp(c, icmp)



            # # Handle exceptions
            # except AttributeError, dpkt.dpkt.NeedData:
            #     continue
            # except Exception as e:
            #     print "exception: {0}".format(e)


        # Close our handle
        handle.close()

        # Cleanup
        self._tcp_build_smtp(reassemble = True)

        # Return
        return self.results



if __name__ == "__main__":
    import sys
    import json
    summary = packetsummary(sys.argv[1])

    t = summary.run()

    print(json.dumps(t))



