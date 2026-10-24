import unittest
from tools.analyze_spatial_dependency_v2_9 import audit,model
from tools.analyze_spatial_position_v2_4 import START,END

class DependencyV29Tests(unittest.TestCase):
 def test_predictable_relation_improves_out_of_sample(self):
  tx=[0,1]*30;ty=[3,4]*30
  m=model(tx,ty,[0,1]*10,[3,4]*10)
  self.assertEqual(m['conditional_accuracy'],1)
  self.assertEqual(m['baseline_accuracy'],.5)
  self.assertGreater(m['logloss_gain'],0)
 def test_unseen_feature_falls_back_to_baseline(self):
  m=model([0]*30,[3]*30,[5]*5,[3]*5)
  self.assertEqual(m['seen_fraction'],0)
  self.assertEqual(m['accuracy_gain'],0)
  self.assertEqual(m['logloss_gain'],0)
 def test_all_phases_and_transitions(self):
  bounds=[100+i*36 for i in range(10)]
  frames={}
  for f in range(bounds[0],bounds[-1]):
   row={o:0 for o in range(START,END+1)}
   row[0x3B30D0]=(f//3)%2
   row[0x3B30E0]=(f//3)%2
   row[0x3B30EC]=(f//5)%2
   frames[f]=row
  evaluations,transitions=audit('test',frames,bounds)
  self.assertEqual(len(evaluations),2*3*2*(9+8))
  self.assertGreater(len(transitions),0)
  self.assertTrue(all(r['test_n']>0 for r in evaluations))
 def test_split_validation(self):
  with self.assertRaises(ValueError):audit('test',{},[],.9)
if __name__=='__main__':unittest.main()
