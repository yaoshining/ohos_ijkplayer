import pathlib,sys,unittest,array
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import generate_hdr_chart as chart
class ChartTests(unittest.TestCase):
 def test_fixed_standard_codes(self):
  for mode,values,expected in [('pq',[0,100,203,1000],[64,509,573,723]),('hlg',[0,1/12,1],[64,502,940]),('sdr',[0,1],[64,940])]:
   self.assertEqual([chart.code(mode,x) for x in values],expected)
 def test_invalid_inputs(self):
  for mode,x in [('bogus',0),('pq',-1),('hlg',2),('sdr',float('nan'))]:
   with self.assertRaises(ValueError):chart.code(mode,x)
 def test_true_ten_bit_gradient_and_neutral_chroma(self):
  for mode in ['pq','hlg','sdr']:
   data=chart.generate(mode);a=array.array('H');a.frombytes(data)
   if sys.byteorder!='little':a.byteswap()
   self.assertEqual(len(a),640*360*3//2)
   self.assertGreater(len(set(a[:640])),256)
   self.assertTrue(any(x%4 for x in a[:640]))
   self.assertEqual(set(a[640*360:640*360+320*60]),{512})
