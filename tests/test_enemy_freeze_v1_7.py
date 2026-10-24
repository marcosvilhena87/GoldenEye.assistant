import struct
import unittest
from tools.analyze_enemy_freeze_v1_7 import scan_graphics,analyze,decode_float
from tools.analyze_enemy_freeze_v1_6 import REGIONS

class GraphicsRefinementTests(unittest.TestCase):
    def test_multiple_opcodes_required(self):
        data=bytearray(128)
        data[0]=0xE7
        mask,windows=scan_graphics(bytes(data))
        self.assertFalse(mask)
        for off,op in ((0,0xE7),(8,0xB9),(16,0xFC)):
            data[off]=op
        mask,windows=scan_graphics(bytes(data))
        self.assertIn(0,mask)
        self.assertIn(20,mask)
    def test_float_decode(self):
        encoded=struct.pack(">f",12.5)
        self.assertEqual(decode_float(encoded,">"),12.5)
    def test_numeric_and_camera_controls(self):
        snapshots={};epochs=[1,2,3]
        for region,(start,size) in REGIONS.items():
            for epoch in epochs:
                blob=bytearray(size)
                blob[0:4]=struct.pack(">f",float(epoch)*10)
                snapshots[(epoch,"stable",region)]=bytes(blob)
                snapshots[(epoch,"hold",region)]=bytes(blob)
            cam=bytearray(snapshots[(3,"stable",region)])
            if region==3:cam[0:4]=struct.pack(">f",40.0)
            snapshots[(3,"camera",region)]=bytes(cam)
        windows,decoded,counts=analyze(snapshots,epochs)
        chosen=[row for row in decoded if row["format"]=="float32_be" and row["offset_hex"]=="0x0D5000"]
        self.assertEqual(len(chosen),1)
        self.assertEqual(chosen[0]["status"],"numeric_candidate_only")
        self.assertTrue(any(row["region"]==3 and row["camera_changed"] for row in decoded))
if __name__=="__main__":unittest.main()
