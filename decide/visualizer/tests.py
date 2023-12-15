from django.test import TestCase
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from django.utils import timezone

from voting.models import Voting, Question, QuestionOption
from mixnet.models import Auth
from django.contrib.auth.models import User

from selenium import webdriver
from selenium.webdriver.common.by import By

import time

class VisualizerTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()

        self.q = Question(desc='test question')
        self.q.save()
        self.v = Voting(name='visualizer voting test', question=self.q, private=True)
        self.v.save()
        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        self.v.auths.add(a)
        self.v.create_pubkey()
        self.v.start_date = timezone.now()
        self.v.save()
        
        self.questionOption1 = QuestionOption(question = self.q, number = 1, option = 'Booth test option 1')
        self.questionOption1.save()

        self.questionOption2 = QuestionOption(question = self.q, number = 2, option = 'Booth test option 2')
        self.questionOption2.save()

        self.user = User(pk=2 ,username='anonymous')
        self.user.set_password('tbo12345')
        self.user.save()

        self.userPrivilege = User(pk=1 ,username='decide', is_staff=True, is_superuser=True)
        self.userPrivilege.set_password('decide')
        self.userPrivilege.save()

        self.client.post('/store/discord/{}/{}/{}/'.format(self.v.pk, self.user.pk, self.questionOption2.number))

        self.v.end_date = timezone.now()
        self.v.save()

        # In order to tally the votes, an admin must be logged and he must execute the task 'tally'
        self.base.login('decide', 'decide')
        self.v.tally_votes()

        options = webdriver.ChromeOptions()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()


    def test_simpleVisualizer(self):
            self.driver.get(f'{self.live_server_url}/visualizer/{self.v.pk}/')
            vState = self.driver.find_element(By.XPATH,"//*[@id='app-visualizer']/div/h1").text
            self.assertEqual(vState, "1 - " + self.v.name)

            voteNumber = self.driver.find_element(By.XPATH, "//*[@id='app-visualizer']/div/div/table/tbody/tr[1]/td[2]").text
            self.assertEqual(int(voteNumber), 1)

