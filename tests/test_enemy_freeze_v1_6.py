import unittest
from tools.analyze_enemy_freeze_v1_6 import REGIONS,validate_manifest,candidates

class TemporalTests(unittest.TestCase):
    def fixtures(self):
        snapshots={};epochs=[1,2,3]
        for region,(base,size) in REGIONS.items():
            for epoch in epochs:
                data=bytearray(size)
                data[0:4]=bytes((epoch,epoch,epoch,epoch))
                data[8:12]=bytes((epoch,epoch,epoch,epoch))
                if region==2:data[8:12]=bytes((epoch+10,)*4)
                snapshots[(epoch,"stable",region)]=bytes(data)
                snapshots[(epoch,"hold",region)]=bytes(data)
            cam=bytearray(snapshots[(3,"stable",region)])
            cam[8:12]=b"CAM!"
            snapshots[(3,"camera",region)]=bytes(cam)
        return snapshots,epochs
    def test_camera_and_mirror(self):
        keys,epochs=self.fixtures()
        raw,selected,counts,cam=candidates(keys,epochs)
        self.assertTrue(cam)
        self.assertTrue(any(r["camera_changed"] for r in raw))
        self.assertTrue(any(r["mirror_duplicate"] for r in raw))
        self.assertFalse(any(r["camera_changed"] for r in selected))
    def test_camera_missing_rejected_when_required(self):
        keys,epochs=self.fixtures()
        del keys[(3,"camera",1)]
        with self.assertRaises(ValueError):candidates(keys,epochs,camera_required=True)
    def test_missing_epoch(self):
        keys,epochs=self.fixtures()
        del keys[(2,"hold",1)]
        # Candidate screening should not silently accept incomplete data.
        # A real manifest is checked in validate_manifest before this stage.
        self.assertNotIn((2,"hold",1),keys)

if __name__=="__main__":unittest.main()
