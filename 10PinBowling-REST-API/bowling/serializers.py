from bowling.models.game import Game
from bowling.models.match import Match
from rest_framework import serializers
import json
from django.core.exceptions import ValidationError

class TransparentField(serializers.Field):
    """
    Transparently pass the data through the serializer.
    Useful for JSONField, which takes care of serialization/deserialization under the hood.
    """
    def to_representation(self, data):
        return data
    def to_internal_value(self, data):
        return data

class AbsoluteURLField(serializers.Field):
    """
    Prepend the site URL to the relative URL.
    """
    def to_representation(self, relative_url):
        """
        http://www.django-rest-framework.org/api-guide/fields/
        """
        if relative_url is not None:
            request = self.context['request']
            return request.build_absolute_uri(relative_url)
        else:
            return None

class GameSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializes Game object to JSON data, and creates Game objects from JSON data.
    """
    results = TransparentField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    shots = AbsoluteURLField(read_only=True, source="shots_relurl")
    frame_scores = TransparentField(read_only=True)
    running_totals = TransparentField(read_only=True)
    ended = serializers.BooleanField(read_only=True)

    class Meta:
        model = Game

    def validate(self, attrs):
        "Call model clean() method, to check the validity of results field."
        instance = Game(**attrs)
        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError({'results': e.messages})
        return attrs

class MatchSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializes Match object to JSON data, and creates Match objects from JSON data.
    """
    games = GameSerializer(many=True, read_only=True)

    class Meta:
        model = Match

class GameShotSerializer(serializers.Serializer):
    """
    Provide the shot field on the Browsable API.
    """
    shot = serializers.IntegerField()
