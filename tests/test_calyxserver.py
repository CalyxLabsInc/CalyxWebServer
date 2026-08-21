import tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import calyxserver as c
class T(unittest.TestCase):
 def test_config_and_welcome(self):
  with tempfile.TemporaryDirectory() as d:
   q=Path(d)/'config.calyx'
   q.write_text(c.CONFIG.replace('/var/calyxserver/www',str(Path(d)/'www')))
   s=c.load(q)
   self.assertEqual(s.port,8080)
   self.assertIn('About Calyx Server',c.ensure_root(s.root).joinpath('index.html').read_text())
 def test_limiter(self):
  x=c.Limiter(1,1,10)
  self.assertTrue(x.permit('a')[0])
  self.assertFalse(x.permit('a')[0])
 def test_network(self):
  self.assertEqual(str(c.nets('127.0.0.1/32')[0]),'127.0.0.1/32')
 def test_proxy_route(self):
  with tempfile.TemporaryDirectory() as d:
   q=Path(d)/'config.calyx'
   q.write_text(c.CONFIG.replace('enabled = false\n# Add routes','enabled = true\n/api = http://127.0.0.1:9000\n# Add routes',1))
   s=c.load(q)
   self.assertEqual(s.routes['/api'],'http://127.0.0.1:9000')
if __name__=='__main__':unittest.main()
