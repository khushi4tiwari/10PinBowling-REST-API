from rest_framework.test import APITestCase
from rest_framework import status
from django.core.exceptions import ValidationError
from bowling.models import Game

class GameTestCase(APITestCase):
    def test_validation_score(self):
        """
        Test case for the bowling validation and scoring functionality.

        Tests a few valid cases and invalid cases.
        """

        def test(results, expected_score):
            g = Game(results=results, player="aaa")
            if expected_score == -1:  # throw an error
                try:
                    g.full_clean()
                except ValidationError:
                    pass
                else:
                    self.fail("This test case should throw an error.")
            else:
                try:
                    g.save()
                except ValidationError as e:
                    self.fail("This test case should pass, but throws an error: {0}".format(e))
                else:
                    self.assertEqual(g.ended, True)
                    self.assertEqual(g.running_totals[9], expected_score)
        # successful examples
        test(['X']*9+['XXX'], 300)
        test(['9-']*10, 90)
        test(['5/']*9+['5/5'], 150)
        test(['X', '7/', '72', '9/', 'X', 'X', 'X', '23', '6/', '7/3'], 168)
        test(['--']*10, 0)
        test(['-1', '27', '3/', 'X', '5/', '7/', '34', '54', '--', 'X7-'], 113)
        test(['X', '7/', '9-', 'X', '-8', '8/', '-6', 'X', 'X', 'X81'], 167)

        # fail examples
        test(['1X']*10, -1)
        test(['X']*9+['AAA'], -1)
        test(['X']*9+['741'], -1)
        test(['/2']+['X']*9, -1)
        test(['410']+['X']*9, -1)
        test(['0X']+['X']*9, -1)
        test(['XX']+['X']*9, -1)
