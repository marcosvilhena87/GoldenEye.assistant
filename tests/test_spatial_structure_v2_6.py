import unittest
from tools.analyze_spatial_structure_v2_6 import audit, rate, phi, BASES
from tools.analyze_spatial_position_v2_4 import START, END

class StructureV26Tests(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(rate([1,1,2,2]),1/3)
        self.assertEqual(phi(2,0,0,2),1.0)
        self.assertEqual(phi(0,0,0,4),"")
    def test_byte_changes_and_alternation(self):
        markers=[100+i*30 for i in range(10)]
        frames={}
        for f in range(100,markers[-1]):
            row={address:0 for address in range(START,END+1)}
            row[BASES[0]]=f%2
            row[BASES[1]]=f%2
            row[BASES[2]]=1
            frames[f]=row
        b,s,sy,p,pattern=audit("test",frames,markers)
        self.assertEqual(len(b),9*12)
        self.assertEqual(len(s),9*3*2*2)
        self.assertEqual(len(sy),9*3*4)
        self.assertEqual(len(p),9*12*6)
        self.assertEqual(len(pattern),9*3)
        first=next(r for r in b if r["phase"]=="P0_HOLD" and r["byte_address"]=="0x3B30D0")
        self.assertEqual(first["change_rate"],1.0)
        alt=next(r for r in pattern if r["phase"]=="P0_HOLD" and r["base"]=="0x3B30D0")
        self.assertEqual(alt["alternating_aba_fraction"],1.0)
        matched=next(r for r in sy if r["phase"]=="P0_HOLD" and r["left"]=="0x3B30D0" and r["right"]=="0x3B30E0")
        self.assertEqual(matched["value_equal_fraction"],1.0)
        self.assertEqual(matched["synchrony_given_either"],1.0)
        lag2=next(r for r in p if r["phase"]=="P0_HOLD" and r["address"]=="0x3B30D0" and r["lag"]==2)
        self.assertEqual(lag2["raw_match_rate"],1.0)
    def test_short_phase_rejected(self):
        frames={f:{address:0 for address in range(START,END+1)} for f in range(18)}
        with self.assertRaises(ValueError):
            audit("test",frames,[i*2 for i in range(10)])

if __name__=="__main__":
    unittest.main()
