import datetime
import random
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from .models import Vote
from .serializers import VoteSerializer
from base import mods
from base.models import Auth
from base.tests import BaseTestCase
from census.models import Census
from mixnet.models import Key
from voting.models import Question
from voting.models import QuestionOption
from voting.models import Voting


class StoreTextCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.question = Question(desc='qwerty')
        self.question.save()
        self.voting = Voting(pk=5001,
                             name='voting example',
                             question=self.question,
                             start_date=timezone.now(),
        )
        self.voting.save()

    def tearDown(self):
        super().tearDown()

    def gen_voting(self, pk):
        voting = Voting(pk=pk, name='v1', question=self.question, start_date=timezone.now(),
                end_date=timezone.now() + datetime.timedelta(days=1))
        voting.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def gen_votes(self):
        votings = [random.randint(1, 5000) for i in range(10)]
        users = [random.randint(3, 5002) for i in range(50)]
        for v in votings:
            a = random.randint(2, 500)
            b = random.randint(2, 500)
            self.gen_voting(v)
            random_user = random.choice(users)
            user = self.get_or_create_user(random_user)
            self.login(user=user.username)
            census = Census(voting_id=v, voter_id=random_user)
            census.save()
            data = {
                "voting": v,
                "voter": random_user,
                "vote": { "a": a, "b": b }
            }
            response = self.client.post('/store/', data, format='json')
            self.assertEqual(response.status_code, 200)

        self.logout()
        return votings, users

    def test_gen_vote_invalid(self):
        data = {
            "voting": 1,
            "voter": 1,
            "vote": { "a": 1, "b": 1 }
        }
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_store_vote(self):
        VOTING_PK = 345
        CTE_A = 96
        CTE_B = 184
        census = Census(voting_id=VOTING_PK, voter_id=1)
        census.save()
        self.gen_voting(VOTING_PK)
        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "vote": { "a": CTE_A, "b": CTE_B }
        }
        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().voting_id, VOTING_PK)
        self.assertEqual(Vote.objects.first().voter_id, 1)
        self.assertEqual(Vote.objects.first().a, CTE_A)
        self.assertEqual(Vote.objects.first().b, CTE_B)

    def test_vote(self):
        self.gen_votes()
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.count())
        self.assertEqual(votes[0], VoteSerializer(Vote.objects.all().first()).data)

    def test_filter(self):
        votings, voters = self.gen_votes()
        v = votings[0]

        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voting_id=v).count())

        v = voters[0]
        response = self.client.get('/store/?voter_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voter_id=v).count())

    def test_hasvote(self):
        votings, voters = self.gen_votes()
        vo = Vote.objects.first()
        v = vo.voting_id
        u = vo.voter_id

        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]["voting_id"], v)
        self.assertEqual(votes[0]["voter_id"], u)

    def test_voting_status(self):
        data = {
            "voting": 5001,
            "voter": 1,
            "vote": { "a": 30, "b": 55 }
        }
        census = Census(voting_id=5001, voter_id=1)
        census.save()
        # not opened
        self.voting.start_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # not closed
        self.voting.start_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        self.voting.end_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        # closed
        self.voting.end_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

class StorePrivateTextCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.question = Question(desc='qwerty')
        self.question.save()
        self.voting = Voting(pk=5001,
                             name='voting example',
                             question=self.question,
                             start_date=timezone.now(),
                             private = True,
        )
        self.voting.save()

        user_anonymous = User(pk = 2, username='anonymous')
        user_anonymous.set_password('tbo12345')
        user_anonymous.save()

        data = {'username': 'anonymous', 'password': 'tbo12345'}
        response = mods.post('authentication/login', json=data, response=True)
        self.assertEqual(response.status_code, 200)
        self.token = response.json().get('token')
        self.assertTrue(self.token)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

    def tearDown(self):
        super().tearDown()

    def test_store_multiple_private_vote(self):
        dataStore1 = {
            "voting": 5001,
            "voter": 2,
            "vote": { "a": 96, "b": 184 }
        }

        dataStore2 = {
            "voting": 5001,
            "voter": 2,
            "vote": { "a": 192, "b": 368 }
        }

        response = self.client.post('/store/', dataStore1, format='json')
        self.assertEqual(response.status_code, 200)


        response = self.client.post('/store/', dataStore2, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)

    def test_store_private_other_user(self):
        
        dataNotAnonymous = {
            "voting": 5001,
            "voter": 1,
            "vote": { "a": 500, "b": 1000 }
        }

        response = self.client.post('/store/', dataNotAnonymous, format='json')

        self.assertEqual(response.status_code, 401)

class StoreDiscordTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.question = Question(desc='Discord test question')
        self.question.save()
        self.questionOption = QuestionOption(question = self.question, number = 1, option = 'Discord test option')
        self.questionOption.save()
        self.pub_key = Key(
                         p = 70231406362306344090225989749017969969678324391204499979828159692550421617459,
                         g = 25943344578732287435064720875717831230723987786285223171781188446421474939830,
                         y = 42255321982391907760391246745603444196092319848940113576180033593436149670776
                         )
        self.pub_key.save()

        self.voting = Voting(pk = 50014,
                             name = 'Discord test voting',
                             question = self.question,
                             start_date = timezone.now(),
                             pub_key = self.pub_key,
                            )
        self.voting.save()

    def tearDown(self):
        super().tearDown()

    def gen_voting(self, pk):
        pub_key = Key(
                         p = 70231406322306344090225989749017969969678324391204499979828159692550421617459,
                         g = 25943344578732287435064720875717831230723987786285221171781188446421474939830,
                         y = 42255321982391907760391246745603444196092419848940113576180033593436149670776
                         )
        pub_key.save()
        voting = Voting(pk=pk, name='v1', question=self.question, start_date=timezone.now(),
                 pub_key = pub_key, end_date=timezone.now() + datetime.timedelta(days=1))
        voting.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def test_discord_invalid_voting(self):

        votingId = 1
        voterId = 1
        selectedOption = 1

        response = self.client.post('/store/discord/{}/{}/{}/'.format(votingId,voterId,selectedOption))
        self.assertEqual(response.status_code, 401)

    def test_discord_invalid_option(self):

        votingId = 50014
        voterId = 1
        selectedOption = 0

        response = self.client.post('/store/discord/{}/{}/{}/'.format(votingId,voterId,selectedOption))
        self.assertEqual(response.status_code, 401)

        selectedOption = 10

        response = self.client.post('/store/discord/{}/{}/{}/'.format(votingId,voterId,selectedOption))
        self.assertEqual(response.status_code, 401)

    def test_discord_store_vote(self):

        votingId = 50015
        voterId = 1
        selectedOption = 1

        self.gen_voting(votingId)
        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/discord/{}/{}/{}/'.format(votingId,voterId,selectedOption))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().voting_id, 50015)
        self.assertEqual(Vote.objects.first().voter_id, 1)

    def test_discord_voting_status(self):

        votingId = 50014
        voterId = 1
        selectedOption = 1

        # not opened
        self.voting.start_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/discord/{}/{}/{}/'.format(votingId,voterId,selectedOption))
        self.assertEqual(response.status_code, 401)

        # not closed
        self.voting.start_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        self.voting.end_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/discord/{}/{}/{}/'.format(votingId,voterId,selectedOption))
        self.assertEqual(response.status_code, 200)

        # closed
        self.voting.end_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/discord/{}/{}/{}/'.format(votingId,voterId,selectedOption))
        self.assertEqual(response.status_code, 401)