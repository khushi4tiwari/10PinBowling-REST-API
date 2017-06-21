from django.db import models
from django.core.exceptions import ValidationError
from jsonfield import JSONField

class Game(models.Model):
    """
    The Game object definition.
    """
    def __init__(self, *a, **k):
        """
        Save an original copy of results for convenience.
        """
        super(Game, self).__init__(*a, **k)
        self.___results = self.results  # save an original copy
    class Meta:
        app_label = 'bowling'

    results = JSONField(default=[None] * 10)
    match = models.ForeignKey('bowling.Match', related_name='games', blank=True, null=True)
    player = models.CharField(max_length=255)

    def clean(self):
        """
        Validate results field.

        The results should be a valid list of frame records.
        If the field is updated, it must not rewrite the original data in the field.
        """
        results = self.results
        if not isinstance(results, list):
            raise ValidationError({'results': 'This field must be an array.'})
        if len(results) != 10:
            raise ValidationError({'results': 'Length must be 10.'})
        for old_r, r in zip(self.___results, results):
            if old_r is None:
                break
            if old_r != r:
                raise ValidationError({'results': 'Cannot rewrite previous records.'})

        for index, r in enumerate(results):
            if r is None:
                break

            if not isinstance(r, basestring):
                raise ValidationError({'results': 'All items must be string.'})

            t = self._frame_type(r, index)
            if t == 'invalid':
                raise ValidationError({'results': 'Invalid frame #{0}.'.format(index+1)})
            elif t == 'incomplete':
                # verify that the frames after are all None
                for r_after in results[index+1:]:
                    if r_after is not None:
                        raise ValidationError({'results': 'Invalid frame data.'})

    def _frame_type(self, frame, frame_index):
        """
        Return a string that represents the type of the frame.
        """
        if frame is None:
            frame = ''
        frame = frame.replace('0', '@').replace('-', '0')
        if frame_index != 9:  # not the last frame
            t = self._frame_type_regular(frame)
        else:  # last frame
            t = self._frame_type_last(frame)
        return t

    def _frame_type_regular(self, frame):
        """
        Returns the frame type as treating a regular frame (not the last one).

        All possibilities:
        strike: 'X'
        spare: like '7/'
        open: like '72'
        incomplete: like '7'
        invalid: other characters, other string lengths, '74' and like
        """
        if len(frame) == 1:
            if frame == 'X':
                return 'strike'
            elif frame.isdigit():
                return 'incomplete'
            else:
                return 'invalid'
        elif len(frame) == 2:
            if frame[1] == '/' and frame[0].isdigit():
                return 'spare'
            elif frame.isdigit() and self._transform_char(frame[0]) + self._transform_char(frame[1]) < 10:
                return 'open'
            else:
                return 'invalid'
        else:
            return 'invalid'

    def _frame_type_last(self, frame):
        """
        Returns the frame type as treating the last frame.

        All possibilities:
        strike: 'XXX' or like 'XX9' or like 'X9X' or like 'X99'
        spare: like '7/X' or like '7/2'
        open: like '72'
        incomplete: like '7', 'X', 'XX', 'X9', '7/'
        invalid: other characters, other string lengths, '74' and like
        """
        if len(frame) == 3:
            if self._frame_type_regular(frame[0]) == 'strike' and (frame[1].isdigit() or frame[1] == 'X') and (frame[2].isdigit() or frame[2] == 'X'):
                return 'strike'
            elif self._frame_type_regular(frame[0:2]) == 'spare' and (frame[2].isdigit() or frame[2] == 'X'):
                return 'spare'
            else:
                return 'invalid'
        elif len(frame) == 2:
            if self._frame_type_regular(frame[0:2]) == 'open':
                return 'open'
            elif self._frame_type_regular(frame[0:2]) == 'spare':
                return 'incomplete'
            elif frame[0] == 'X' and (frame[1].isdigit() or frame[1] == 'X'):
                return 'incomplete'
            else:
                return 'invalid'
        elif len(frame) == 1:
            if frame[0].isdigit() or frame[0] == 'X':
                return 'incomplete'
            else:
                return 'invalid'
        else:
            return 'invalid'

    def _transform_char(self, ch):
        "convert character to pins"
        if ch == '-':
            return 0
        elif ch == 'X':
            return 10
        else:
            return int(ch)

    @property
    def frame_scores(self):
        """
        Calculate the frame scores according to frame records.
        """
        fscores = [None] * 10   # initialize
        for index, r in enumerate(self.results):
            t = self._frame_type(r, index)
            if t == 'open':
                fscores[index] = self._transform_char(r[0]) + self._transform_char(r[1])
            elif t == 'spare':
                ## Definition: count next one shot
                if index != 9:
                    r_next = self.results[index + 1]
                    if r_next is not None:
                        fscores[index] = 10 + self._transform_char(r_next[0])
                    else:
                        fscores[index] = None
                else:  # last frame
                    fscores[index] = 10 + self._transform_char(r[2])
            elif t == 'strike':
                ## Definition: count next two shots
                if index == 9:  # last frame
                    fscores[index] = 10 + self._transform_char(r[1]) + self._transform_char(r[2])
                else:
                    # aggregate future shots
                    future_shots = ''
                    for r_future in self.results[index+1:]:
                        if r_future is not None:
                            future_shots += r_future
                    if len(future_shots) >= 2:
                        if future_shots[1] == '/':  # a spare
                            fscores[index] = 10 + 10
                        else:
                            fscores[index] = 10 + self._transform_char(future_shots[0]) + self._transform_char(future_shots[1])
                    else:
                        fscores[index] = None
            else:
                fscores[index] = None
        return fscores

    @property
    def running_totals(self):
        """
        Calculate running total scores.
        """
        sum = 0
        running_totals = [None] * 10    # initialization
        for index, fscore in enumerate(self.frame_scores):
            if fscore is not None:
                sum += fscore
                running_totals[index] = sum
            else:
                break
        return running_totals

    @property
    def ended(self):
        """
        Returns a boolean value. True when every frame is complete.
        """
        for index, r in enumerate(self.results):
            if self._frame_type(r, index) not in ['strike', 'spare', 'open']:
                return False  # incomplete game
        return True  # every frame is complete

    @property
    def shots_relurl(self):
        """
        Link to the shots API.
        """
        return '/game/{0}/shots/'.format(self.id)
