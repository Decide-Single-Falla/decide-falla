from django.utils import timezone
from django.utils.dateparse import parse_datetime
import django_filters.rest_framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics

from .models import Vote
from .serializers import VoteSerializer
from base import mods
from base.perms import UserIsStaff

import random


class StoreView(generics.ListAPIView):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_fields = ('voting_id', 'voter_id')

    def get(self, request):
        self.permission_classes = (UserIsStaff,)
        self.check_permissions(request)
        return super().get(request)

    def post(self, request):
        """
         * voting: id
         * voter: id
         * vote: { "a": int, "b": int }
        """

        vid = request.data.get('voting')
        voting = mods.get('voting', params={'id': vid})
        if not voting or not isinstance(voting, list):
            # print("por aqui 35")
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        start_date = voting[0].get('start_date', None)
        # print ("Start date: "+  start_date)
        end_date = voting[0].get('end_date', None)
        #print ("End date: ", end_date)
        not_started = not start_date or timezone.now() < parse_datetime(start_date)
        #print (not_started)
        is_closed = end_date and parse_datetime(end_date) < timezone.now()
        if not_started or is_closed:
            #print("por aqui 42")
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        vote = request.data.get('vote')

        if not vid or not vote:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        if (voting[0].get('private')):

            token = request.auth.key

            voter = mods.post('authentication', entry_point='/getuser/', json={'token': token})

            uid = request.data.get('voter')

            a = vote.get("a")
            b = vote.get("b")

            v = Vote.objects.create(voting_id=vid, voter_id=uid)

        else:
            uid = request.data.get('voter')

            if not uid:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)

            # validating voter
            if request.auth:
                token = request.auth.key
            else:
                token = "NO-AUTH-VOTE"
            voter = mods.post('authentication', entry_point='/getuser/', json={'token': token})
            voter_id = voter.get('id', None)
            if not voter_id or voter_id != uid:
                # print("por aqui 59")
                return Response({}, status=status.HTTP_401_UNAUTHORIZED)

            # the user is in the census
            perms = mods.get('census/{}'.format(vid), params={'voter_id': uid}, response=True)
            if perms.status_code == 401:
                # print("por aqui 65")
                return Response({}, status=status.HTTP_401_UNAUTHORIZED)

            a = vote.get("a")
            b = vote.get("b")

            defs = { "a": a, "b": b }
            v, _ = Vote.objects.get_or_create(voting_id=vid, voter_id=uid,
                                          defaults=defs)

        v.a = a
        v.b = b

        v.save()

        return  Response({})

class DiscordStoreView(generics.CreateAPIView):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_fields = ('voting_id', 'voter_id')

    def post(self, request, voting_id, voter_id, selectedOption):

        """
         * voting: id
         * voter: id
         * vote: { "a": int, "b": int }
        """

        voting = mods.get('voting', params={'id': voting_id})
        if not voting or not isinstance(voting, list):
            # print("por aqui 35")
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        start_date = voting[0].get('start_date', None)

        # print ("Start date: "+  start_date)
        end_date = voting[0].get('end_date', None)
        #print ("End date: ", end_date)
        not_started = not start_date or timezone.now() < parse_datetime(start_date)
        #print (not_started)
        is_closed = end_date and parse_datetime(end_date) < timezone.now()
        numberOfOptions = len(voting[0].get('question').get('options'))

        if (numberOfOptions < selectedOption) or selectedOption == 0:
            return Response({"Invalid option"}, status=status.HTTP_401_UNAUTHORIZED)
        elif not_started or is_closed:
            #print("por aqui 42")
            return Response({"This voting is closed"}, status=status.HTTP_401_UNAUTHORIZED)

        bigpk = {
            'p': (voting[0].get('pub_key').get('p')),
            'g': (voting[0].get('pub_key').get('g')),
            'y': (voting[0].get('pub_key').get('y')),
        }
        cipher = DiscordStoreView.encrypt(bigpk, selectedOption)
        a = str(cipher[0])
        b = str(cipher[1])


        defs = { "a": a, "b": b }
        v, _ = Vote.objects.get_or_create(voting_id=voting_id, voter_id=voter_id,
                                        defaults=defs)
        v.a = a
        v.b = b

        v.save()

        return Response({})
    
    def get_random_integer(max_value):
        bit_length = max_value.bit_length()
        random_num = random.getrandbits(bit_length)
        return random_num % max_value
    
    def encrypt(pk, m, r=None):
        bits = 256
        if m == 0:
            raise ValueError("Can't encrypt 0 with El Gamal")

        if r is None:
            q = 2 ** bits
            q1 = q - 1
            r = DiscordStoreView.get_random_integer(q1)

        alpha = pow(pk.get('g'), r, pk.get('p'))
        beta = (pow(pk.get('y'), r, pk.get('p')) * m) % pk.get('p')

        return (alpha, beta)