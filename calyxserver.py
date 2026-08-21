#!/usr/bin/env python3
'''Calyx Web Server: pure-Python static server and reverse proxy.'''
from __future__ import annotations
import argparse, configparser, html, http.client, ipaddress, logging, mimetypes, os, posixpath, signal, ssl, threading, time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit
VERSION='2.0.0'; DEFAULT_CONFIG=Path('/var/calyxserver/configuration/config.calyx'); LOG=logging.getLogger('calyx')
WELCOME='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Calyx Web Server</title><style>
:root{color-scheme:dark;--pink:#ff58c8;--purple:#a77aff;--muted:#cbbfca}*{box-sizing:border-box}body{margin:0;color:#fff;background:radial-gradient(circle at 10% 0,#551541,transparent 35%),radial-gradient(circle at 90% 10%,#302064,transparent 32%),#09070a;font:16px/1.65 system-ui,sans-serif}.wrap{width:min(1060px,calc(100% - 2rem));margin:auto}nav{display:flex;justify-content:space-between;padding:1.3rem 0;font-weight:800}.pink{color:var(--pink)}header{min-height:58vh;display:grid;align-content:center}.eyebrow{color:#ff9ddd;text-transform:uppercase;letter-spacing:.18em;font-size:.78rem;font-weight:800}h1{font-size:clamp(3rem,9vw,6.7rem);line-height:.92;margin:.5rem 0 1.4rem}.grad{background:linear-gradient(90deg,var(--pink),var(--purple));background-clip:text;color:transparent}.lead{max-width:720px;color:var(--muted);font-size:1.2rem}.status{display:inline-flex;align-items:center;gap:.6rem;margin-top:1rem;padding:.6rem 1rem;border:1px solid #65405c;border-radius:99px}.dot{width:.65rem;height:.65rem;border-radius:50%;background:#56eda5;box-shadow:0 0 17px #56eda5}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:5rem}.card,.about{border:1px solid #483248;background:#151017dc;border-radius:22px;padding:1.6rem}.card p,.about p{color:var(--muted)}.about{padding:clamp(1.6rem,5vw,3rem);margin-bottom:5rem;background:linear-gradient(135deg,#2b1226,#151027)}.about h2{font-size:clamp(2rem,4vw,3rem);margin:.4rem 0}code{color:#ff9ddd}footer{border-top:1px solid #332834;padding:2rem 0;color:#a99ba7}@media(max-width:760px){.grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap"><nav><span><span class="pink">CALYX</span> WEB SERVER</span><span>Pure Python. Open source.</span></nav><header><div class="eyebrow">The server is online</div><h1>Simple serving.<br><span class="grad">Serious control.</span></h1><p class="lead">Your public root is ready. Replace this page by editing <code>/var/calyxserver/www/index.html</code>.</p><div><span class="status"><span class="dot"></span>Calyx is accepting requests</span></div></header><section class="grid"><article class="card"><h2>Dependency-free</h2><p>Built entirely on the Python standard library for transparent deployment.</p></article><article class="card"><h2>Configurable</h2><p>Control TLS, proxy routes, paths, limits, access rules, and headers in <code>config.calyx</code>.</p></article><article class="card"><h2>Hardened defaults</h2><p>Request limits, safer headers, path confinement, and bounded concurrency are included.</p></article></section><section class="about"><div class="eyebrow">About the project</div><h2>About Calyx Server by Calyx Labs Inc.</h2><p>Calyx Web Server is an open-source web server application created to compete with Nginx and Apache as a lightweight, approachable, and simple alternative. It focuses on readable configuration, practical security controls, and a pure-Python codebase developers can understand, customize, and deploy.</p></section><footer>Calyx Web Server 2.0 • Make the web yours.</footer></div></body></html>'''
CONFIG='''# Calyx Web Server 2.0 configuration
[server]
host = 0.0.0.0
port = 8080
working_directory = /var/calyxserver/www
index_files = index.html,index.htm
list_directories = false
request_timeout_seconds = 15
max_request_body_bytes = 10485760
max_connections = 100
server_header = Calyx

[https]
enabled = false
certificate_file = /etc/calyxserver/tls/fullchain.pem
private_key_file = /etc/calyxserver/tls/privkey.pem
minimum_tls = 1.2

[security]
rate_limit_enabled = true
requests_per_minute = 120
rate_burst = 30
ban_seconds = 300
allowed_networks =
denied_networks =
allowed_methods = GET,HEAD,POST,PUT,PATCH,DELETE,OPTIONS
trust_proxy_headers = false
content_security_policy = default-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'

[proxy]
enabled = false
# Add routes such as: /api = http://127.0.0.1:9000
connect_timeout_seconds = 5
preserve_host = false
forwarded_headers = true

[logging]
level = INFO
'''
@dataclass
class Settings:
 host:str;port:int;root:Path;indexes:tuple;listing:bool;timeout:float;max_body:int;max_conn:int;header:str;https:bool;cert:Path|None;key:Path|None;tls:str;rate_on:bool;rpm:int;burst:int;ban:int;allow:tuple;deny:tuple;methods:frozenset;trust_proxy:bool;csp:str;proxy_on:bool;routes:dict;proxy_timeout:float;preserve_host:bool;forwarded:bool

def boolean(c,s,k,d=False):
 try:return c.getboolean(s,k,fallback=d)
 except ValueError as e:raise SystemExit(f'Invalid boolean [{s}] {k}: {e}')
def nets(v):
 try:return tuple(ipaddress.ip_network(x.strip(),strict=False) for x in v.split(',') if x.strip())
 except ValueError as e:raise SystemExit(f'Invalid network: {e}')
def pathval(v,base):
 x=Path(os.path.expandvars(os.path.expanduser(v)));return x if x.is_absolute() else base/x
def ensure_config(path):
 try:
  path.parent.mkdir(parents=True,exist_ok=True)
  if not path.exists():path.write_text(CONFIG,encoding='utf-8')
  return path.resolve()
 except PermissionError as e:raise SystemExit(f'Cannot create {path}; use sudo or --config') from e
def load(path,port=None):
 c=configparser.ConfigParser(interpolation=None);c.read(path,encoding='utf-8');g=lambda s,k,d='':c.get(s,k,fallback=d)
 try:
  routes={};reserved={'enabled','connect_timeout_seconds','preserve_host','forwarded_headers'}
  if c.has_section('proxy'):
   for k,v in c.items('proxy'):
    if k.startswith('/') and k not in reserved:
     u=urlsplit(v); 
     if u.scheme not in ('http','https') or not u.hostname:raise SystemExit(f'Invalid upstream: {v}')
     routes[k.rstrip('/') or '/']=v.rstrip('/')
  prt=port if port is not None else c.getint('server','port',fallback=8080)
  if not 1<=prt<=65535:raise SystemExit('Port must be 1-65535')
  return Settings(g('server','host','0.0.0.0'),prt,pathval(g('server','working_directory','/var/calyxserver/www'),path.parent).resolve(),tuple(x.strip() for x in g('server','index_files','index.html').split(',')),boolean(c,'server','list_directories'),c.getfloat('server','request_timeout_seconds',fallback=15),c.getint('server','max_request_body_bytes',fallback=10485760),c.getint('server','max_connections',fallback=100),g('server','server_header','Calyx'),boolean(c,'https','enabled'),pathval(g('https','certificate_file',''),path.parent) if g('https','certificate_file','') else None,pathval(g('https','private_key_file',''),path.parent) if g('https','private_key_file','') else None,g('https','minimum_tls','1.2'),boolean(c,'security','rate_limit_enabled',True),c.getint('security','requests_per_minute',fallback=120),c.getint('security','rate_burst',fallback=30),c.getint('security','ban_seconds',fallback=300),nets(g('security','allowed_networks','')),nets(g('security','denied_networks','')),frozenset(x.strip().upper() for x in g('security','allowed_methods','GET,HEAD').split(',')),boolean(c,'security','trust_proxy_headers'),g('security','content_security_policy',"default-src 'self'"),boolean(c,'proxy','enabled'),routes,c.getfloat('proxy','connect_timeout_seconds',fallback=5),boolean(c,'proxy','preserve_host'),boolean(c,'proxy','forwarded_headers',True))
 except (configparser.Error,ValueError) as e:raise SystemExit(f'Invalid config: {e}')
def ensure_root(root):
 root.mkdir(parents=True,exist_ok=True);root=root.resolve();idx=root/'index.html'
 if not idx.exists():idx.write_text(WELCOME,encoding='utf-8')
 return root
class Limiter:
 def __init__(self,rpm,burst,ban):self.rate=max(rpm,1)/60;self.cap=max(burst,1);self.ban=ban;self.d={};self.lock=threading.Lock()
 def permit(self,key):
  now=time.monotonic()
  with self.lock:
   tok,last,until=self.d.get(key,(self.cap,now,0));tok=min(self.cap,tok+(now-last)*self.rate)
   if until>now:return False,int(until-now)+1
   if tok<1:self.d[key]=(tok,now,now+self.ban);return False,self.ban
   self.d[key]=(tok-1,now,0);return True,0
HOP={'connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade'}
class Handler(BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1';server_version='Calyx';sys_version=''
 def setup(self):super().setup();self.connection.settimeout(self.server.s.timeout)
 def version_string(self):return self.server.s.header
 def ip(self):
  x=self.client_address[0]
  if self.server.s.trust_proxy:x=self.headers.get('X-Forwarded-For',x).split(',')[0].strip()
  try:return ipaddress.ip_address(x)
  except ValueError:return ipaddress.ip_address(self.client_address[0])
 def dispatch(self):
  ip=self.ip();s=self.server.s
  if any(ip in n for n in s.deny) or (s.allow and not any(ip in n for n in s.allow)):return self.send_error(403)
  if self.command not in s.methods:return self.send_error(405,'Method disabled')
  if s.rate_on:
   ok,retry=self.server.limiter.permit(str(ip))
   if not ok:self.send_response(429);self.send_header('Retry-After',str(retry));self.send_header('Content-Length','0');return self.end_headers()
  try:n=int(self.headers.get('Content-Length','0'))
  except ValueError:return self.send_error(400)
  if n>s.max_body:return self.send_error(413,'Request too large')
  route=self.route()
  if route:return self.proxy(route,n)
  if self.command not in ('GET','HEAD'):return self.send_error(501,'Static route only supports GET/HEAD')
  self.static()
 do_GET=dispatch;do_HEAD=dispatch;do_POST=dispatch;do_PUT=dispatch;do_PATCH=dispatch;do_DELETE=dispatch;do_OPTIONS=dispatch
 def route(self):
  if not self.server.s.proxy_on:return None
  x=urlsplit(self.path).path;m=[(k,v) for k,v in self.server.s.routes.items() if x==k or x.startswith(k.rstrip('/')+'/')]
  return max(m,key=lambda z:len(z[0])) if m else None
 def proxy(self,route,n):
  prefix,base=route;s=self.server.s;u=urlsplit(base);r=urlsplit(self.path);suffix=r.path[len(prefix):] or '/';target=urlunsplit(('', '',u.path.rstrip('/')+'/'+suffix.lstrip('/'),r.query,''));body=self.rfile.read(n) if n else None
  cls=http.client.HTTPSConnection if u.scheme=='https' else http.client.HTTPConnection;kw={'timeout':s.proxy_timeout}
  if u.scheme=='https':kw['context']=ssl.create_default_context()
  conn=cls(u.hostname,u.port,**kw);headers={k:v for k,v in self.headers.items() if k.lower() not in HOP};headers['Host']=self.headers.get('Host') if s.preserve_host else u.netloc
  if s.forwarded:headers.update({'X-Forwarded-For':self.client_address[0],'X-Forwarded-Proto':'https' if isinstance(self.connection,ssl.SSLSocket) else 'http','X-Forwarded-Host':self.headers.get('Host','')})
  try:
   conn.request(self.command,target,body,headers);resp=conn.getresponse();data=resp.read();self.send_response(resp.status,resp.reason)
   for k,v in resp.getheaders():
    if k.lower() not in HOP and k.lower() not in ('server','content-length'):self.send_header(k,v)
   self.send_header('Content-Length',str(len(data)));self.end_headers()
   if self.command!='HEAD':self.wfile.write(data)
  except Exception as e:LOG.warning('Proxy error: %s',e);self.send_error(502,'Upstream unavailable')
  finally:conn.close()
 def safe(self):
  root=self.server.s.root;raw=posixpath.normpath(unquote(urlsplit(self.path).path));x=root.joinpath(*(i for i in raw.split('/') if i not in ('','.','..')))
  try:x=x.resolve();x.relative_to(root);return x
  except (OSError,ValueError):return None
 def static(self):
  x=self.safe();s=self.server.s
  if x is None:return self.send_error(403)
  if x.is_dir():
   for name in s.indexes:
    if (x/name).is_file():x=x/name;break
   else:
    if not s.listing:return self.send_error(403,'Directory listing disabled')
    return self.listing(x)
  if not x.is_file():return self.send_error(404)
  data=x.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(x))[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.end_headers()
  if self.command!='HEAD':self.wfile.write(data)
 def listing(self,x):
  data=('<!doctype html><h1>Directory</h1><ul>'+''.join(f'<li><a href="{quote(i.name)}">{html.escape(i.name)}</a></li>' for i in sorted(x.iterdir()))+'</ul>').encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def end_headers(self):
  self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','SAMEORIGIN');self.send_header('Referrer-Policy','no-referrer');self.send_header('Permissions-Policy','geolocation=(), microphone=(), camera=()');self.send_header('Content-Security-Policy',self.server.s.csp)
  if isinstance(self.connection,ssl.SSLSocket):self.send_header('Strict-Transport-Security','max-age=31536000; includeSubDomains')
  super().end_headers()
 def log_message(self,f,*a):LOG.info('%s %s',self.client_address[0],f%a)
class Server(ThreadingHTTPServer):
 daemon_threads=True;allow_reuse_address=True
 def __init__(self,addr,s):self.s=s;self.limiter=Limiter(s.rpm,s.burst,s.ban);self.request_queue_size=s.max_conn;super().__init__(addr,Handler)
def main(argv=None):
 a=argparse.ArgumentParser();a.add_argument('--config',type=Path,default=DEFAULT_CONFIG);a.add_argument('--port',type=int);a.add_argument('--check-config',action='store_true');a.add_argument('--version',action='version',version=VERSION);o=a.parse_args(argv);cp=ensure_config(o.config);s=load(cp,o.port);logging.basicConfig(level=logging.INFO,format='%(asctime)s [%(levelname)s] %(message)s');s.root=ensure_root(s.root)
 if o.check_config:print(f'Configuration OK: {cp}');return 0
 try:srv=Server((s.host,s.port),s)
 except OSError as e:raise SystemExit(f'Cannot bind {s.host}:{s.port}: {e}')
 if s.https:
  if not s.cert or not s.key or not s.cert.is_file() or not s.key.is_file():raise SystemExit('HTTPS certificate/private key missing')
  ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_3 if s.tls=='1.3' else ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(s.cert,s.key);srv.socket=ctx.wrap_socket(srv.socket,server_side=True)
 def stop(*_):threading.Thread(target=srv.shutdown,daemon=True).start()
 signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop);LOG.info('Calyx %s serving %s on %s:%s',VERSION,s.root,s.host,s.port)
 try:srv.serve_forever(.5)
 finally:srv.server_close()
if __name__=='__main__':raise SystemExit(main())
