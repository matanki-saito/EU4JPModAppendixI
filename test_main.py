import re
from unittest import TestCase

from main import replace_parameter_map_definition


class Test(TestCase):
    def test_normalization(self):
        text = ("TEST あいう えお akasatana. {GetコサックName}aaa £nullpo£"
                "az  £nullpo£ aaaw x  £nullpo  a w£nullpo  ££nullpo£w as £nullp  a xx "
                "aw £nullp 　あGetDhimmiNameGetMarathasName£nullp")

        for pattern, repl in replace_parameter_map_definition.items():
            text = re.sub(pattern, repl, text)
            print("{:60} : {:10}".format(str(pattern), text))

        self.assertEquals(text, "TEST あいう えお akasatana. {GetコサックName}aaa £nullpo£"
                                "az  £nullpo£ aaaw x  £nullpo£ a w£nullpo££nullpo£w as £nullp£ a xx "
                                "aw £nullp£　あGetズィンミーNameGetマラーターName£nullp£")
