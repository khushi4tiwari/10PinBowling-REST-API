from rest_framework import serializers
from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import mixins
from bowling.models.game import Game
from bowling.models.match import Match
from bowling.serializers import GameSerializer, MatchSerializer, GameShotSerializer
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(('GET',))
def api_root(request, format=None):
    """
    Browse all APIs.
    """
    response = {
        'games': reverse('game-list', request=request, format=format),
        'matches': reverse('match-list', request=request, format=format)
    }

    return Response(response)


class GameList(generics.ListCreateAPIView):
    """
    Returns a list of all Games. Accepts a POST request with a data body to
    create a new Game. POST requests will return the newly-created Game object.
    """
    model = Game
    serializer_class = GameSerializer
    queryset = Game.objects.all()

class GameDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Perform operations on a single Game instance.
    """
    model = Game
    serializer_class = GameSerializer
    queryset = Game.objects.all()

class GameShot(generics.GenericAPIView):
    """
    Add a shot to the game.
    """
    model = Game
    serializer_class = GameShotSerializer
    queryset = Game.objects.all()

    def post(self, request, pk, *a, **k):
        game = self.get_object()
        pins = request.data.get('shot')
        try:
            pins = int(pins)
        except Exception:
            return Response({'detail': 'Pins must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)
        if pins < 0 or pins > 10:
            return Response({'detail': 'Pins must be between 0 and 10.'}, status=status.HTTP_400_BAD_REQUEST)
        if game.ended:
            return Response({'detail': 'The game has ended.'}, status=status.HTTP_400_BAD_REQUEST)

        ## Figure out the corresponding string of current shot.
        for index, r in enumerate(game.results):
            to_save = False
            if r is None:
                game.results[index] = self._to_str(pins)
                to_save = True
            elif game._frame_type(r, index) == 'incomplete':
                if (index != 9 or index == 9 and len(game.results[index]) == 1 and game.results[index][0].isdigit()) and (pins + game._transform_char(game.results[index][0]) == 10):
                    game.results[index] += '/'
                else:
                    game.results[index] += self._to_str(pins)
                to_save = True

            if to_save:
                try:
                    game.clean()
                    game.save()
                except ValidationError as e:
                    raise serializers.ValidationError({'shot': e.messages})
                serializer = GameSerializer(game, context={'request': request})
                return Response(serializer.data)

    def _to_str(self, pins):
        if pins == 0:
            return '-'
        elif pins == 10:
            return 'X'
        else:
            return str(pins)


class MatchList(generics.ListCreateAPIView):
    """
    Returns a list of all Matches. Accepts a POST request with a data body to
    create a new Match. POST requests will return the newly-created Match object.
    """
    model = Match
    serializer_class = MatchSerializer
    queryset = Match.objects.all()

class MatchDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Perform operations on a single Match instance.
    """
    model = Match
    serializer_class = MatchSerializer
    queryset = Match.objects.all()
