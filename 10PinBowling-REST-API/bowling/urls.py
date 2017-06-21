from django.conf import settings
from django.conf.urls import patterns, include, url

from rest_framework.urlpatterns import format_suffix_patterns

from bowling import views

urlpatterns = []

urlpatterns += patterns('',
)

urlpatterns += format_suffix_patterns(
    patterns('',
             url(r'^$', views.api_root),
             url(r'^games/$', views.GameList.as_view(), name='game-list'),
             url(r'^game/(?P<pk>[0-9]+)/$', views.GameDetail.as_view(), name='game-detail'),
             url(r'^game/(?P<pk>[0-9]+)/shots/$', views.GameShot.as_view(), name='game-shot'),

             url(r'^matches/$', views.MatchList.as_view(), name='match-list'),
             url(r'^match/(?P<pk>[0-9]+)/$', views.MatchDetail.as_view(), name='match-detail'),
    )
)

