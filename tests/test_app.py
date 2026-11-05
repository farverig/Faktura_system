import os, tempfile, unittest
from pathlib import Path
from decimal import Decimal
tmp=tempfile.TemporaryDirectory()
os.environ["FAKTURA_DATA"]=tmp.name
os.environ["APP_PASSWORD"]="test"
os.environ["APP_SECRET"]="test-secret"
import app
class InvoiceTests(unittest.TestCase):
 def test_vat(self):
  d={"lines":[{"qty":"3","price":"500","vat":"25"}]}
  self.assertEqual(app.totals(d),(Decimal("1500.00"),Decimal("375.00"),Decimal("1875.00")))
 def test_pdf(self):
  d={"customer":"Kunde","customer_address":"Testvej 1","customer_cvr":"","issue_date":"2026-11-05","due_date":"2026-11-13","lines":[{"name":"Ydelse","qty":"1","price":"100","vat":"25"}]}
  self.assertTrue(app.make_pdf(132,d,app.get_settings()).startswith(b"%PDF"))
 def test_sequence_initialized(self):
  with app.db() as c:
   self.assertGreaterEqual(c.execute("SELECT next_number FROM sequence WHERE id=1").fetchone()[0],1)
if __name__=="__main__":unittest.main()
