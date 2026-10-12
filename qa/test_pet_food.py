import sys,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ecosystem as e
class FoodTests(unittest.TestCase):
 def setUp(self):
  self.s={};self.world=e.ensure(self.s);self.world['balance']=1000;self.world['equipped']={'outfit':'pajamas','hat':'cap','background':'room-ice'}
 def call(self,action,item,token=None):return e.pet_action(self.s,dict(action=action,item=item,requestId=token or uuid.uuid4().hex,price=0),1000)
 def test_every_food_uses_server_price_and_single_consumption(self):
  for f in [x for x in e.SHOP if x['category']=='food']:
   with self.subTest(f=f['id']):
    before=self.world['balance'];self.call('buy',f['id']);self.assertEqual(self.world['balance'],before-f['price']);n=self.world['inventory'][f['id']];token=uuid.uuid4().hex;first=self.call('use',f['id'],token);self.assertEqual(self.world['inventory'][f['id']],n-1);self.assertEqual(first,self.call('use',f['id'],token));self.assertEqual(self.world['inventory'][f['id']],n-1)
 def test_unowned_and_unknown_fail_without_cost(self):
  for id in ['pizza','invalid-food']:
   with self.assertRaises(ValueError):self.call('use',id)
  self.assertEqual(self.world['balance'],1000)
 def test_food_does_not_change_clothes_or_room(self):
  before=dict(self.world['equipped']);self.call('use','berry');self.assertEqual(before,self.world['equipped'])
 def test_inventory_never_goes_negative(self):
  for _ in range(3):self.call('use','berry')
  with self.assertRaises(ValueError):self.call('use','berry')
  self.assertEqual(self.world['inventory']['berry'],0)
if __name__=='__main__':unittest.main()
