# A01 basic tests; run outside SuperMind with Python 3.
import math
import unittest

def allowed(s):
    return (s.startswith('600') and s.endswith('.SH')) or (s.startswith('00') and s.endswith('.SZ'))

def score(items):
    a = sorted(items, key=lambda z:(z[1]['r20'],z[0]))
    b = sorted(items, key=lambda z:(z[1]['vol'],z[0]))
    ar={s:i for i,(s,_) in enumerate(a)}
    br={s:i for i,(s,_) in enumerate(b)}
    n=max(1,len(items)-1)
    return sorted([(ar[s]/float(n)-br[s]/float(n),s) for s,_ in items],key=lambda z:(-z[0],z[1]))

class Tests(unittest.TestCase):
    def test_universe(self):
        self.assertTrue(allowed('600519.SH'))
        self.assertTrue(allowed('002782.SZ'))
        for s in ('601398.SH','603000.SH','688000.SH','300001.SZ','510300.SH'):
            self.assertFalse(allowed(s))
    def test_score(self):
        data=[('A',{'r20':.15,'vol':.02}),('B',{'r20':.05,'vol':.08}),('C',{'r20':.1,'vol':.04})]
        self.assertEqual(score(data)[0][1],'A')
    def test_position_lot(self):
        px=110
        shares=int(min(20000,49970)/(px*1.012)/100)*100
        self.assertEqual(shares,100)

if __name__=='__main__':
    unittest.main()
